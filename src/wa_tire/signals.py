"""Opportunity signals: residual (actual vs expected) and growth gap (tire vs dealer), ranked."""

import numpy as np
import pandas as pd


def residuals(pred, years):
    """Mean log(actual / expected) per county over `years`; residual_pct is exp(mean) - 1."""
    p = pred[pred["year"].isin(years)]
    log_res = np.log(p["actual"] / p["model"])
    out = log_res.groupby(p["county"]).mean().rename("residual_log").reset_index()
    out["residual_pct"] = np.exp(out["residual_log"]) - 1
    return out


def growth_gap(cy, base_year, end_year):
    """Real tire-dealer log growth minus real new-car-dealer log growth, base_year -> end_year."""
    b = cy[cy["year"] == base_year].set_index("county")
    e = cy[cy["year"] == end_year].set_index("county")
    out = pd.DataFrame({
        "tire_growth_log": np.log(e["tire_real"] / b["tire_real"]),
        "newcar_growth_log": np.log(e["newcar_real"] / b["newcar_real"]),
    })
    out["growth_gap_log"] = out["tire_growth_log"] - out["newcar_growth_log"]
    return out.reset_index()


def rank_and_flag(res, gap, top_share):
    """Rank counties on both signals (1 = strongest); top candidate = top `top_share` on both and both > 0."""
    df = res.merge(gap, on="county")
    df["residual_rank"] = df["residual_log"].rank(ascending=False, method="min").astype(int)
    df["growth_gap_rank"] = df["growth_gap_log"].rank(ascending=False, method="min").astype(int)
    cut = int(np.ceil(top_share * len(df)))
    df["top_residual"] = (df["residual_rank"] <= cut) & (df["residual_log"] > 0)
    df["top_growth_gap"] = (df["growth_gap_rank"] <= cut) & (df["growth_gap_log"] > 0)
    df["top_candidate"] = df["top_residual"] & df["top_growth_gap"]
    df["combined_rank"] = (df["residual_rank"] + df["growth_gap_rank"]).rank(method="min").astype(int)
    return df.sort_values(["combined_rank", "residual_rank"]).reset_index(drop=True)


def top_counties(ranked, n=3):
    """Flagged top candidates first, then by combined rank; first n county names."""
    order = ranked.sort_values(["top_candidate", "combined_rank"], ascending=[False, True])
    return list(order["county"].head(n))
