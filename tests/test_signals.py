import numpy as np
import pandas as pd
import pytest

from wa_tire import signals


def test_residual_is_mean_log_ratio_over_selected_years():
    pred = pd.DataFrame({
        "county": ["A", "A", "A", "B", "B", "B"],
        "year": [2023, 2024, 2025, 2023, 2024, 2025],
        "actual": [110.0, 121.0, 999.0, 90.0, 90.0, 90.0],
        "model": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
    })
    res = signals.residuals(pred, [2023, 2024]).set_index("county")
    assert res.loc["A", "residual_log"] == pytest.approx((np.log(1.1) + np.log(1.21)) / 2)
    assert res.loc["B", "residual_pct"] == pytest.approx(-0.1)


def test_growth_gap_math_and_flags():
    cy = pd.DataFrame({
        "county": ["A", "A", "B", "B", "C", "C", "D", "D"],
        "year": [2019, 2025] * 4,
        "tire_real": [100.0, 150.0, 100.0, 100.0, 100.0, 90.0, 100.0, 130.0],
        "newcar_real": [100.0, 120.0, 100.0, 100.0, 100.0, 100.0, 100.0, 140.0],
    })
    gap = signals.growth_gap(cy, 2019, 2025).set_index("county")
    assert gap.loc["A", "growth_gap_log"] == pytest.approx(np.log(1.5) - np.log(1.2))
    assert gap.loc["D", "growth_gap_log"] < 0
    res = pd.DataFrame({"county": ["A", "B", "C", "D"], "residual_log": [0.2, 0.3, -0.1, 0.1]})
    ranked = signals.rank_and_flag(res, gap.reset_index(), top_share=0.5).set_index("county")
    assert ranked["top_candidate"].to_dict() == {"A": True, "B": False, "C": False, "D": False}
