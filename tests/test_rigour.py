import numpy as np
import pandas as pd
import pytest
from scipy import stats

from wa_tire import rigour


def test_resample_keeps_whole_counties_under_unique_labels():
    df = pd.DataFrame({"county": ["A", "A", "B", "B", "C", "C"], "year": [2017, 2018] * 3, "x": range(6)})
    bdf, bcy = rigour.resample(df, df, np.random.default_rng(0))
    assert bdf["county"].nunique() == 3  # one label per draw, even when a county is drawn twice
    for label, g in bdf.groupby("county"):
        src = df[df["county"] == rigour.original(label)]
        assert g["year"].tolist() == src["year"].tolist() and g["x"].tolist() == src["x"].tolist()
    assert bcy.equals(bdf)


def test_coef_ci_uses_clustered_se_and_t_with_g_minus_1_df():
    fit = type("Fit", (), {"params": pd.Series({"log_vehicles": 0.6, "log_dealer": 0.1}),
                           "bse": pd.Series({"log_vehicles": 0.1, "log_dealer": 0.1})})()
    ci = rigour.coef_ci(fit, groups=20).set_index("term")
    t = stats.t.ppf(0.975, 19)
    assert ci.loc["log_vehicles", "ci_low"] == pytest.approx(0.6 - t * 0.1)
    assert ci["excludes_zero"].to_dict() == {"log_vehicles": True, "log_dealer": False}


def test_summarise_bootstrap_counts_only_draws_that_include_the_county():
    long = pd.DataFrame({
        "county": ["A"] * 4 + ["B"] * 2, "draw": [0, 1, 2, 3, 0, 2],
        "residual_rank": [1, 2, 1, 5, 3, 4], "residual_z": 0.0, "residual_log": [0.1, 0.2, 0.3, 0.4, -0.1, 0.0],
        "residual_flag": [True, True, True, False, False, False],
        "top_quartile_residual": [True, True, True, False, False, True],
        "growth_flag": True, "top_candidate": [True, True, False, False, False, False],
    })
    s = rigour.summarise_bootstrap(long).set_index("county")
    assert s.loc["A", "draws"] == 4 and s.loc["B", "draws"] == 2
    assert s.loc["A", "rank_median"] == 1.5
    assert s.loc["A", "pct_residual_flag"] == 0.75 and s.loc["A", "pct_top_candidate"] == 0.5
    assert s.loc["B", "pct_top_quartile"] == 0.5


def test_loo_and_tier_changes_name_the_dropped_county():
    base = pd.DataFrame({"county": ["K"], "residual_flag": [True], "growth_flag": [True], "top_candidate": [True]})
    loo = pd.DataFrame({"county": ["K", "K"], "dropped": ["X", "Y"], "residual_flag": [True, False],
                        "growth_flag": [True, True], "top_candidate": [True, False]})
    ch = rigour.loo_changes(loo, base, ["K", "missing"]).set_index("county")
    assert ch.loc["K", "top_candidate_changed_by"] == "Y" and ch.loc["K", "growth_flag_changed_by"] == "none"
    assert "missing" not in ch.index
    v1 = pd.DataFrame({"county": ["K"], "tier": ["Watch"]})
    loo_tier = pd.DataFrame({"county": ["K", "K", "N"], "tier": ["Watch", "Watch", "Watch"], "dropped": ["X", "Y", "Y"]})
    assert rigour.tier_changes(loo_tier, v1).to_dict("records") == [
        {"dropped": "Y", "county": "N", "tier_v1": "none", "tier_now": "Watch"}]
