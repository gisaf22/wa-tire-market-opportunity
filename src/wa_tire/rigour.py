"""v1.1 rigour checks: clustered coefficient CIs, county bootstrap, leave-one-county-out.

All checks reuse the v1 model and signal rules unchanged (model.py, signals.py, config.py).
Pre-registered hypotheses and definitions: reports/findings_log.md.
"""

import numpy as np
import pandas as pd
from scipy import stats

from wa_tire import model, signals

SEP = "#"  # bootstrap copies of a county are labelled "<county>#<k>"


def coef_ci(fit, groups, level=0.95):
    """Coefficient CIs from county-clustered SEs, t critical value with G - 1 degrees of freedom."""
    rows = ["log_vehicles", "log_dealer"]
    t = stats.t.ppf(0.5 + level / 2, groups - 1)
    b, se = fit.params[rows], fit.bse[rows]
    return pd.DataFrame({
        "coef": b, "se_cluster": se, "ci_low": b - t * se, "ci_high": b + t * se,
        "excludes_zero": (b - t * se > 0) | (b + t * se < 0), "clusters": groups,
    }).rename_axis("term").reset_index()


def score(df, cy, recent_n, z_min, top_share, base_year, end_year):
    """v1 signals for one model frame: fit on train, residuals on test, growth gap, ranks and flags.

    Returns (fit, ranked) with a `top_quartile_residual` column added.
    """
    fit, test_pred = model.run_split(df)
    res = signals.residual_stats(test_pred, recent_n, z_min)
    gap = signals.growth_gap(cy[cy["county"].isin(df["county"].unique())], base_year, end_year)
    ranked = signals.rank_and_flag(res, gap[~gap["growth_data_missing"]], top_share)
    ranked["top_quartile_residual"] = ranked["residual_rank"] <= int(np.ceil(top_share * len(ranked)))
    return fit, ranked


def resample(df, cy, rng):
    """Draw counties with replacement; each draw keeps all of a county's years under a unique label."""
    counties = df["county"].unique()
    drawn = rng.choice(counties, size=len(counties), replace=True)
    labels, model_parts, cy_parts = [], [], []
    for k, c in enumerate(drawn):
        label = f"{c}{SEP}{k}"
        labels.append(label)
        model_parts.append(df[df["county"] == c].assign(county=label))
        cy_parts.append(cy[cy["county"] == c].assign(county=label))
    return pd.concat(model_parts, ignore_index=True), pd.concat(cy_parts, ignore_index=True)


def original(label):
    return label.split(SEP)[0]


BOOT_COLS = ["residual_rank", "residual_z", "residual_log", "residual_flag", "top_quartile_residual",
             "growth_flag", "top_candidate"]


def bootstrap(df, cy, draws, seed, **rules):
    """Long table, one row per (draw, original county); a county drawn twice is scored on its first copy."""
    rng = np.random.default_rng(seed)
    out = []
    for b in range(draws):
        bdf, bcy = resample(df, cy, rng)
        _, ranked = score(bdf, bcy, **rules)
        ranked = ranked.assign(source=ranked["county"].map(original),
                               copy=ranked["county"].str.split(SEP).str[1].astype(int))
        first = ranked.sort_values("copy").drop_duplicates("source")
        out.append(first[["source"] + BOOT_COLS].rename(columns={"source": "county"}).assign(draw=b))
    return pd.concat(out, ignore_index=True)


def summarise_bootstrap(long, level=0.90):
    """Per county: draws included, median and interval of residual rank and log residual, % of draws flagged."""
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    g = long.groupby("county")
    return pd.DataFrame({
        "draws": g.size(),
        "rank_median": g["residual_rank"].median(),
        "rank_low": g["residual_rank"].quantile(lo),
        "rank_high": g["residual_rank"].quantile(hi),
        "residual_log_median": g["residual_log"].median(),
        "residual_log_low": g["residual_log"].quantile(lo),
        "residual_log_high": g["residual_log"].quantile(hi),
        "pct_top_quartile": g["top_quartile_residual"].mean(),
        "pct_residual_flag": g["residual_flag"].mean(),
        "pct_top_candidate": g["top_candidate"].mean(),
    }).reset_index().sort_values("rank_median", kind="stable").reset_index(drop=True)


def leave_one_out(df, cy, **rules):
    """Refit once per county with that county dropped. Long table: dropped county x remaining county flags."""
    out = []
    for drop in df["county"].unique():
        _, ranked = score(df[df["county"] != drop], cy, **rules)
        out.append(ranked[["county"] + BOOT_COLS].assign(dropped=drop))
    return pd.concat(out, ignore_index=True)


def loo_changes(loo, baseline, counties):
    """For each county of interest: drops that flip its residual flag, growth flag or top-candidate flag."""
    base = baseline.set_index("county")
    rows = []
    for c in counties:
        if c not in base.index:
            continue
        sub = loo[loo["county"] == c]
        row = {"county": c, "refits": len(sub)}
        for flag in ["residual_flag", "growth_flag", "top_candidate"]:
            flips = sub.loc[sub[flag] != bool(base.loc[c, flag]), "dropped"]
            row[f"{flag}_v1"] = bool(base.loc[c, flag])
            row[f"{flag}_changed_by"] = ", ".join(sorted(flips)) or "none"
        rows.append(row)
    return pd.DataFrame(rows)


def loo_tiers(frames, cy, views, concentration, max_share, **rules):
    """v1 tiers with each county dropped from every view in turn.

    `frames` is {view: model frame}, `views` is {view: short label}, primary first.
    Returns one row per (dropped county, tiered county).
    """
    primary = next(iter(views))
    out = []
    for drop in sorted(set().union(*(f["county"] for f in frames.values()))):
        ranked = {v: score(f[f["county"] != drop], cy, **rules)[1] for v, f in frames.items()}
        tiers = signals.tier_table(signals.compare_views(ranked), ranked[primary], views, concentration, max_share)
        out.append(tiers.assign(dropped=drop))
    return pd.concat(out, ignore_index=True)


def tier_changes(loo_tier, v1_tiers):
    """Dropped counties under which the tier table differs from v1: a v1 county changes tier or vanishes,
    or a new county is tiered."""
    v1 = dict(zip(v1_tiers["county"], v1_tiers["tier"]))
    rows = []
    for drop, t in loo_tier.groupby("dropped"):
        now = dict(zip(t["county"], t["tier"]))
        for c in sorted(set(v1) | set(now)):
            if c != drop and v1.get(c) != now.get(c):
                rows.append({"dropped": drop, "county": c, "tier_v1": v1.get(c, "none"), "tier_now": now.get(c, "none")})
    return pd.DataFrame(rows, columns=["dropped", "county", "tier_v1", "tier_now"])
