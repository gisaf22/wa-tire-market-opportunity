"""Clean, combine NAICS codes, deflate, build county x quarter and county x year tables."""

import numpy as np
import pandas as pd

from wa_tire import config


def combine_codes(raw):
    """Map NAICS to series: 441320 + 441340 -> 'tire', 441110 -> 'newcar'; drop everything else."""
    df = raw[raw["naics"].astype(str).isin(config.SERIES)].copy()
    df["series"] = df["naics"].astype(str).map(config.SERIES)
    return df


def check_no_double_counting(raw, locs):
    """Every row must come from a kept location that belongs to exactly one county, once per cell."""
    rule = locs.set_index("location_code")["rule"]
    bad = raw[~raw["location_code"].map(rule).isin(["city", "unincorporated"])]
    if len(bad):
        raise ValueError(f"rows from dropped location codes: {sorted(bad['location_code'].unique())}")
    if raw.groupby("location_code")["county"].nunique().max() > 1:
        raise ValueError("a location code maps to more than one county")
    dupes = raw.duplicated(["location_code", "quarter", "naics"])
    if dupes.any():
        raise ValueError(f"{dupes.sum()} duplicated location x quarter x NAICS rows")


def county_quarter(raw, locs, quarters):
    """County x quarter x series: disclosed nominal sales, units, total and hidden ('D') cells.

    Every county x quarter x series is present; no rows means no taxpayers (sales 0).
    hidden_share_ub is the upper-bound share of taxpayers sitting in hidden cells.
    """
    check_no_double_counting(raw, locs)
    df = combine_codes(raw)
    g = df.groupby(["county", "quarter", "series"]).agg(
        sales=("taxable_sales", "sum"), units=("units", "sum"),
        cells=("hidden", "size"), hidden_cells=("hidden", "sum"),
    )
    counties = sorted(locs["county"].dropna().unique())
    full = pd.MultiIndex.from_product([counties, quarters, ["tire", "newcar"]], names=g.index.names)
    g = g.reindex(full, fill_value=0).reset_index()
    hidden_ub = config.MAX_HIDDEN_PER_CELL * g["hidden_cells"]
    g["hidden_share_ub"] = np.where(hidden_ub > 0, hidden_ub / (g["units"] + hidden_ub), 0.0)
    g["year"] = g["quarter"].str[:4].astype(int)
    return g


def deflate(cq, deflators):
    """Add real_sales in constant CPI_BASE_YEAR dollars (tire CPI for tires, new-vehicle CPI for dealers)."""
    out = cq.merge(deflators[["series", "quarter", "factor"]], on=["series", "quarter"], how="left")
    if out["factor"].isna().any():
        raise ValueError(f"missing CPI for quarters {sorted(out.loc[out['factor'].isna(), 'quarter'].unique())}")
    out["real_sales"] = out["sales"] * out["factor"]
    return out.drop(columns="factor")


def exclusions(cq, county_year_df):
    """Counties excluded from modelling, with reasons."""
    tire = cq[cq["series"] == "tire"]
    hidden_q = (tire["hidden_share_ub"] > config.HIDDEN_QUARTER_SHARE).groupby(tire["county"]).mean()
    model = county_year_df[county_year_df["year"] >= config.MODEL_FIRST_YEAR]
    zero_tire = model.groupby("county")["tire_real"].min() <= 0
    zero_newcar = model.groupby("county")["newcar_real"].min() <= 0
    out = pd.DataFrame({"hidden_quarter_share": hidden_q, "zero_tire_year": zero_tire, "zero_newcar_year": zero_newcar})
    reasons = []
    for county, r in out.iterrows():
        why = []
        if r["hidden_quarter_share"] > config.MAX_HIDDEN_QUARTERS:
            why.append(f"tire data hidden in {r['hidden_quarter_share']:.0%} of quarters")
        if r["zero_tire_year"]:
            why.append("a model year with no disclosed tire-dealer sales")
        if r["zero_newcar_year"]:
            why.append("a model year with no disclosed new-car-dealer sales")
        reasons.append("; ".join(why))
    out["reason"] = reasons
    out["excluded"] = out["reason"] != ""
    return out.reset_index().rename(columns={"index": "county"})


def county_year(cq, vehicles):
    """County x year (full years only): nominal and real sales by series, hidden cells, vehicles."""
    full_years = cq.groupby("year")["quarter"].nunique()
    cq = cq[cq["year"].isin(full_years[full_years == 4].index)]
    wide = cq.pivot_table(index=["county", "year"], columns="series",
                          values=["sales", "real_sales", "hidden_cells"], aggfunc="sum")
    wide.columns = [f"{s}_{v}".replace("_real_sales", "_real").replace("_sales", "_nominal")
                    for v, s in wide.columns]
    wide = wide.reset_index()
    return wide.merge(vehicles, on=["county", "year"], how="left")


def naics_transition_check(cq):
    """Statewide tire-dealer Q2/Q1 nominal ratio by year; 2022 is the 441320 -> 441340 switch."""
    s = cq[cq["series"] == "tire"].groupby("quarter")["sales"].sum()
    rows = []
    for y in sorted({q[:4] for q in s.index}):
        if f"{y}Q1" in s and f"{y}Q2" in s:
            rows.append({"year": int(y), "q2_over_q1": s[f"{y}Q2"] / s[f"{y}Q1"]})
    out = pd.DataFrame(rows)
    out["is_switch_year"] = out["year"] == 2022
    return out


def qoq_outliers(cq, included):
    """County quarters whose real tire QoQ log change departs from the statewide change by > threshold."""
    t = cq[(cq["series"] == "tire") & cq["county"].isin(included)].sort_values(["county", "quarter"]).copy()
    t["log_real"] = np.log(t["real_sales"].where(t["real_sales"] > 0))
    t["qoq"] = t.groupby("county")["log_real"].diff()
    state = np.log(t.groupby("quarter")["real_sales"].sum()).diff()
    t["state_qoq"] = t["quarter"].map(state)
    t["excess"] = t["qoq"] - t["state_qoq"]
    out = t[t["excess"].abs() > config.QOQ_OUTLIER_LOG]
    return out[["county", "quarter", "real_sales", "qoq", "state_qoq", "excess", "hidden_cells"]]


def coverage_table(cq, cy, excl):
    """One row per county: coverage, mean recent real sales, hidden share, inclusion."""
    tire = cq[cq["series"] == "tire"]
    cov = tire.groupby("county").agg(
        first_quarter=("quarter", "min"), last_quarter=("quarter", "max"),
        tire_hidden_cells=("hidden_cells", "sum"), tire_cells=("cells", "sum"),
    )
    last = cy["year"].max()
    recent = cy[cy["year"] == last].set_index("county")[["tire_real", "newcar_real", "vehicles"]]
    recent.columns = [f"{c}_{last}" for c in recent.columns]
    return cov.join(recent).join(excl.set_index("county")[["hidden_quarter_share", "excluded", "reason"]]).reset_index()


def load_processed(name):
    """Read a pipeline output from data/processed/ (used by the notebook)."""
    return pd.read_csv(config.PROCESSED / f"{name}.csv")
