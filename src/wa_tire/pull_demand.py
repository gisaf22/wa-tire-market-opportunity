"""Vehicle demand: WA DOL registration transactions by residential county and calendar year.

Source: data.wa.gov "Vehicle Registrations by Class and County" (hmzg-s6q4), monthly from 2017-01.
WA registrations renew annually, so a calendar year's transaction count approximates the
registered fleet. Only full calendar years are kept.
"""

import pandas as pd
import requests

from wa_tire import config


def pull_registrations(refresh=False):
    out = config.RAW / "wa_dol_registrations.csv"
    if out.exists() and not refresh:
        return pd.read_csv(out)
    classes = ",".join(f"'{c}'" for c in config.DOL_USE_CLASSES)
    params = {
        "$select": "registered_owner_county as county, date_extract_y(month) as year, "
                   "count(distinct date_extract_m(month)) as months, sum(number_of_registrations) as vehicles",
        "$where": f"use_class in ({classes})",
        "$group": "county, year",
        "$limit": "50000",
    }
    r = requests.get(config.DOL_DATASET, params=params, timeout=120)
    r.raise_for_status()
    df = pd.DataFrame(r.json()).astype({"year": int, "months": int, "vehicles": float})
    df = df[(df["months"] == 12) & (df["county"] != "Out Of State")].drop(columns="months")
    config.RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df
