"""BLS CPI-U (U.S. city average, NSA) for tires and new vehicles, via the keyless v1 API.

v1 allows at most 10 years per request, so the range is requested in chunks.
"""

import pandas as pd
import requests

from wa_tire import config

BLS_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"


def pull_cpi(first_year, last_year, refresh=False):
    """Monthly CPI, columns: series, year, month, value."""
    out = config.RAW / "bls_cpi.csv"
    if out.exists() and not refresh:
        return pd.read_csv(out)
    rows = []
    for start in range(first_year, last_year + 1, 10):
        body = {"seriesid": [config.CPI_TIRES, config.CPI_NEW_VEHICLES],
                "startyear": str(start), "endyear": str(min(start + 9, last_year))}
        r = requests.post(BLS_URL, json=body, timeout=60)
        r.raise_for_status()
        payload = r.json()
        if payload["status"] != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS API: {payload.get('message')}")
        for s in payload["Results"]["series"]:
            for d in s["data"]:
                # "-" = not collected (e.g. Oct 2025, lapse in appropriations); skipped.
                if d["period"].startswith("M") and d["period"] != "M13" and d["value"] != "-":
                    rows.append((s["seriesID"], int(d["year"]), int(d["period"][1:]), float(d["value"])))
    df = pd.DataFrame(rows, columns=["series", "year", "month", "value"]).sort_values(["series", "year", "month"])
    config.RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


def quarterly_deflators(cpi):
    """Quarterly price factor to constant CPI_BASE_YEAR dollars: real = nominal * factor."""
    cpi = cpi.assign(quarter=cpi["year"].astype(str) + "Q" + ((cpi["month"] - 1) // 3 + 1).astype(str))
    base = cpi[cpi["year"] == config.CPI_BASE_YEAR].groupby("series")["value"].mean()
    q = cpi.groupby(["series", "quarter"])["value"].agg(["mean", "size"]).reset_index()
    q = q[q["size"] >= 2]  # at least 2 of 3 months observed
    q["factor"] = q["series"].map(base) / q["mean"]
    names = {config.CPI_TIRES: "tire", config.CPI_NEW_VEHICLES: "newcar"}
    return q.assign(series=q["series"].map(names)).rename(columns={"mean": "cpi"})[["series", "quarter", "cpi", "factor"]]
