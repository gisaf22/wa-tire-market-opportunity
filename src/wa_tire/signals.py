"""Opportunity signals: out-of-sample residual scaled by model error, and relative growth gap.

Residual flag: actual above expected in every recent test year AND mean recent log residual
greater than RESIDUAL_Z_MIN x the model's typical error (median absolute test log error).
Growth flag: top quartile on relative growth gap, with relative gap > 0 and real tire growth > 0.
Top candidate: both flags.
"""

import numpy as np
import pandas as pd


def residual_stats(test_pred, recent_n, z_min):
    """Per county: test years above expected, mean recent log residual, residual / typical error, flag."""
    p = test_pred.assign(log_res=np.log(test_pred["actual"] / test_pred["model"]))
    typical = p["log_res"].abs().median()
    recent = sorted(p["year"].unique())[-recent_n:]
    r = p[p["year"].isin(recent)]
    out = pd.DataFrame({
        "test_years_above": (p["log_res"] > 0).groupby(p["county"]).sum(),
        "test_years": p.groupby("county").size(),
        "above_all_recent": (r["log_res"] > 0).groupby(r["county"]).all(),
        "residual_log": r.groupby("county")["log_res"].mean(),
    }).reset_index()
    out["residual_pct"] = np.exp(out["residual_log"]) - 1
    out["typical_error"] = typical
    out["residual_z"] = out["residual_log"] / typical
    out["recent_years"] = f"{recent[0]}-{recent[-1]}"
    out["residual_flag"] = out["above_all_recent"] & (out["residual_z"] > z_min)
    return out


def growth_gap(cy, base_year, end_year, dealer_col):
    """Real log growth base->end for tires and dealer activity, each net of the trend of the counties in `cy`.

    relative_gap = (county tire - state tire growth) - (county dealer - state dealer growth).
    The state terms are the same for every county, so ranking on relative_gap equals ranking on
    the raw gap; they only move the zero line.
    """
    b = cy[cy["year"] == base_year].set_index("county")
    e = cy[cy["year"] == end_year].set_index("county")
    out = pd.DataFrame({
        "tire_growth_log": np.log(e["tire_real"] / b["tire_real"]),
        "dealer_growth_log": np.log(e[dealer_col] / b[dealer_col]),
    })
    state_tire = np.log(e["tire_real"].sum() / b["tire_real"].sum())
    state_dealer = np.log(e[dealer_col].sum() / b[dealer_col].sum())
    out["tire_rel_log"] = out["tire_growth_log"] - state_tire
    out["dealer_rel_log"] = out["dealer_growth_log"] - state_dealer
    out["growth_gap_log"] = out["tire_growth_log"] - out["dealer_growth_log"]
    out["relative_gap_log"] = out["tire_rel_log"] - out["dealer_rel_log"]
    out["growth_period"] = f"{base_year}-{end_year}"
    return out.reset_index()


def rank_and_flag(res, gap, top_share):
    """Rank on residual_z and relative gap (1 = strongest) and set the flags described above."""
    df = res.merge(gap, on="county")
    df["residual_rank"] = df["residual_z"].rank(ascending=False, method="min").astype(int)
    df["growth_gap_rank"] = df["relative_gap_log"].rank(ascending=False, method="min").astype(int)
    cut = int(np.ceil(top_share * len(df)))
    df["growth_flag"] = (df["growth_gap_rank"] <= cut) & (df["relative_gap_log"] > 0) & (df["tire_growth_log"] > 0)
    df["top_candidate"] = df["residual_flag"] & df["growth_flag"]
    df["combined_rank"] = (df["residual_rank"] + df["growth_gap_rank"]).rank(method="min").astype(int)
    return df.sort_values(["top_candidate", "combined_rank"], ascending=[False, True]).reset_index(drop=True)


def top_counties(ranked, n=3):
    """Flagged top candidates first, then by combined rank; first n county names."""
    order = ranked.sort_values(["top_candidate", "combined_rank"], ascending=[False, True])
    return list(order["county"].head(n))


def compare_views(ranked_by_view):
    """County x view table of flags, to see whether candidates change with the dealer measure."""
    frames = []
    for view, r in ranked_by_view.items():
        frames.append(r.set_index("county")[["residual_flag", "growth_flag", "top_candidate"]].add_suffix(f"_{view}"))
    return pd.concat(frames, axis=1).reset_index()


def flagged_counties(comparison, views):
    """Counties that are a top candidate in any view, ordered by the first view in `views` first."""
    out = []
    for v in views:
        out += [c for c in comparison.loc[comparison[f"top_candidate_{v}"].eq(True), "county"] if c not in out]
    return out


def _flag(x):
    """True only for a set True flag (NaN = county not in that view)."""
    return bool(x) if pd.notna(x) else False


def tier_table(comparison, ranked_primary, views, primary_last_year):
    """Tier every county that is a top candidate in any view, with a one-line reason.

    `views` is {view: short label}, primary first. Robust: top candidate in both views.
    Watch: top candidate in one view only, including counties the primary view cannot assess.
    """
    (primary, p_name), (secondary, s_name) = list(views.items())
    prim = ranked_primary.set_index("county")
    rows = []
    for _, c in comparison.iterrows():
        p, s = _flag(c[f"top_candidate_{primary}"]), _flag(c[f"top_candidate_{secondary}"])
        if not (p or s):
            continue
        county = c["county"]
        if p and s:
            tier, reason = "Robust", "Flagged under both dealer measures."
        elif p:
            tier, reason = "Watch", f"Flagged under {p_name} only."
        elif county not in prim.index:
            tier, reason = "Watch", f"Flagged under {s_name} only; not assessable under {p_name} (no published data)."
        else:
            r = prim.loc[county]
            if not r["growth_flag"] and r["tire_growth_log"] <= 0:
                why = (f"in the {p_name} window tire sales did not grow 2019-{primary_last_year}, so its signal comes "
                       f"from later years; recheck when {p_name} {primary_last_year + 1} is released.")
            elif not r["residual_flag"]:
                why = f"residual within model error under {p_name}."
            else:
                why = f"growth gap not in the top quartile under {p_name}."
            tier, reason = "Watch", f"Flagged under {s_name} only; {why}"
        rows.append({"county": county, "tier": tier, "reason": reason})
    out = pd.DataFrame(rows, columns=["county", "tier", "reason"])
    return out.sort_values("tier", key=lambda t: t.map({"Robust": 0, "Watch": 1}), kind="stable").reset_index(drop=True)
