import numpy as np
import pandas as pd
import pytest

from wa_tire import build, config, pull_wa


def _locs():
    rows = [("1700", "Unincorporated King County"), ("1726", "Seattle"),
            ("1799", "King County"), ("1717", "King County PTBA")]
    locs = pd.DataFrame(rows, columns=["location_code", "location"])
    locs["county_no"] = "17"
    locs["county"] = "King"
    locs["rule"] = [pull_wa.classify_location(c, n) for c, n in rows]
    return locs


def _raw(rows):
    df = pd.DataFrame(rows, columns=["location_code", "quarter", "naics", "taxable_sales", "units", "hidden"])
    df["county"] = "King"
    return df


def test_combine_codes_joins_tire_codes_and_drops_others():
    raw = _raw([("1700", "2022Q1", "441320", 10.0, 3, False), ("1700", "2022Q2", "441340", 11.0, 3, False),
                ("1700", "2022Q2", "441110", 50.0, 4, False), ("1700", "2022Q2", "441330", 99.0, 5, False)])
    out = build.combine_codes(raw)
    assert list(out["series"]) == ["tire", "tire", "newcar"]
    cq = build.county_quarter(raw, _locs(), ["2022Q1", "2022Q2"])
    tire = cq[cq["series"] == "tire"].set_index("quarter")["sales"]
    assert tire["2022Q1"] == 10.0 and tire["2022Q2"] == 11.0  # one continuous series across the switch


def test_99_and_ptba_codes_are_dropped_and_not_double_counted():
    locs = _locs()
    assert dict(zip(locs["location_code"], locs["rule"])) == {
        "1700": "unincorporated", "1726": "city", "1799": "drop_99", "1717": "drop_ptba"}
    assert pull_wa.classify_location("3499", "Thurston County") == "drop_99"
    good = _raw([("1700", "2020Q1", "441320", 5.0, 3, False), ("1726", "2020Q1", "441320", 7.0, 4, False)])
    cq = build.county_quarter(good, locs, ["2020Q1"])
    assert cq.loc[cq["series"] == "tire", "sales"].item() == 12.0
    with pytest.raises(ValueError):
        build.county_quarter(pd.concat([good, _raw([("1799", "2020Q1", "441320", 12.0, 7, False)])]), locs, ["2020Q1"])
    with pytest.raises(ValueError):
        build.county_quarter(pd.concat([good, good.iloc[[0]]]), locs, ["2020Q1"])


def test_no_negative_sales_and_hidden_cells_counted():
    raw = _raw([("1700", "2020Q1", "441320", 5.0, 3, False), ("1726", "2020Q1", "441320", np.nan, np.nan, True)])
    cq = build.county_quarter(raw, _locs(), ["2020Q1"])
    tire = cq[cq["series"] == "tire"].iloc[0]
    assert tire["sales"] == 5.0 and tire["hidden_cells"] == 1
    assert tire["hidden_share_ub"] == pytest.approx(2 / (3 + 2))
    assert (cq["sales"] >= 0).all()
    processed = config.PROCESSED / "county_quarter.csv"
    if processed.exists():
        real = pd.read_csv(processed)
        assert (real["sales"] >= 0).all() and (real["real_sales"] >= 0).all()
