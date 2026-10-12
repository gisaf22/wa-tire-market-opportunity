import numpy as np
import pandas as pd
import pytest

from wa_tire import signals


def _test_pred(ratios):
    rows = [(c, y, r * 100.0, 100.0) for c, rs in ratios.items() for y, r in zip([2023, 2024, 2025], rs)]
    return pd.DataFrame(rows, columns=["county", "year", "actual", "model"])


def test_residual_scaled_by_typical_error_and_flag():
    pred = _test_pred({"A": [1.2, 1.2, 1.2], "B": [0.9, 1.1, 1.0], "C": [1.05, 1.05, 1.05]})
    res = signals.residual_stats(pred, recent_n=3, z_min=1.0).set_index("county")
    typical = np.median(np.abs(np.log([1.2] * 3 + [0.9, 1.1, 1.0] + [1.05] * 3)))
    assert res.loc["A", "typical_error"] == pytest.approx(typical)
    assert res.loc["A", "residual_z"] == pytest.approx(np.log(1.2) / typical)
    assert res.loc["B", "test_years_above"] == 1 and res.loc["C", "test_years_above"] == 3
    # A: above in all years and beyond 1x typical error; C: always above but within error; B: not always above
    assert res["residual_flag"].to_dict() == {"A": True, "B": False, "C": False}


def test_relative_growth_gap_vs_vehicles_and_tire_growth_requirement():
    cy = pd.DataFrame({
        "county": ["A", "A", "B", "B", "C", "C"],
        "year": [2019, 2023] * 3,
        "tire_real": [100.0, 150.0, 100.0, 90.0, 100.0, 100.0],
        "vehicles": [100.0, 100.0, 100.0, 50.0, 100.0, 100.0],
    })
    gap = signals.growth_gap(cy, 2019, 2023).set_index("county")
    state_tire, state_vehicles = np.log(340 / 300), np.log(250 / 300)
    assert gap.loc["A", "growth_gap_log"] == pytest.approx(np.log(1.5) - np.log(1.0))  # tire minus vehicle growth
    assert gap.loc["A", "relative_gap_log"] == pytest.approx(np.log(1.5) - state_tire + state_vehicles)
    shift = gap["growth_gap_log"] - gap["relative_gap_log"]
    assert np.allclose(shift, state_tire - state_vehicles)  # constant shift: same ranking as the raw gap
    res = pd.DataFrame({"county": ["A", "B", "C"], "residual_z": [2.0, 3.0, 0.5], "residual_flag": [True, True, False]})
    ranked = signals.rank_and_flag(res, gap.reset_index(), top_share=2 / 3).set_index("county")
    # B has the largest gap but tire sales fell, so it is not a growth candidate
    assert ranked["growth_flag"].to_dict() == {"A": True, "B": False, "C": False}
    assert ranked["top_candidate"].to_dict() == {"A": True, "B": False, "C": False}


def test_concentration_cap_moves_robust_to_watch_unless_city_hidden():
    comparison = pd.DataFrame({"county": ["A", "B", "C"], "top_candidate_p": [True, True, True],
                               "top_candidate_s": [True, True, True]})
    ranked_primary = pd.DataFrame({"county": ["A", "B", "C"], "residual_flag": [True] * 3, "growth_flag": [True] * 3})
    conc = pd.DataFrame({"county": ["A", "B", "C"], "top_jurisdiction": ["Town A", "Town B", "Town C"],
                         "top_jurisdiction_share_of_growth": [0.7, 0.7, 0.4],
                         "top_jurisdiction_hidden": [False, True, False]})
    tiers = signals.tier_table(comparison, ranked_primary, {"p": "P", "s": "S"}, conc, max_share=0.5).set_index("county")
    assert tiers["tier"].to_dict() == {"A": "Watch", "B": "Robust", "C": "Robust"}
    assert "Town A accounts for 70%" in tiers.loc["A", "reason"]
    assert "not applied" in tiers.loc["B", "reason"] and "Town B" in tiers.loc["B", "reason"]
