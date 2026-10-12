"""Dealer activity alternative: Census County Business Patterns employment, NAICS 441110, WA counties.

CBP counts mid-March employment at establishment location. Since 2017 CBP applies noise
infusion and does not publish county cells with very few establishments, so small counties
are often missing. CENSUS_API_KEY is read from the environment and never logged.
"""

import os

import pandas as pd
import requests

from wa_tire import config

CBP_URL = "https://api.census.gov/data/{year}/cbp"


def pull_cbp(first_year, last_year, refresh=False):
    """County x year 441110 employment and establishments; stops at the first year not yet released."""
    out = config.RAW / "census_cbp_441110.csv"
    if out.exists() and not refresh:
        return pd.read_csv(out)
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise RuntimeError("CENSUS_API_KEY is not set")
    frames = []
    for year in range(first_year, last_year + 1):
        params = {"get": "NAME,EMP,ESTAB", "for": "county:*", "in": "state:53",
                  config.CBP_NAICS_VAR: config.NEWCAR_CODE, "key": key}
        r = requests.get(CBP_URL.format(year=year), params=params, timeout=60)
        if r.status_code == 404:
            break  # year not released
        if r.status_code != 200:
            raise RuntimeError(f"CBP {year}: HTTP {r.status_code}")  # no response text: URL carries the key
        rows = r.json()
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df["year"] = year
        frames.append(df)
    df = pd.concat(frames)
    df["county"] = df["NAME"].str.replace(" County, Washington", "", regex=False)
    df = df.rename(columns={"EMP": "newcar_emp", "ESTAB": "newcar_estab"})
    df = df.astype({"newcar_emp": float, "newcar_estab": float})[["county", "year", "newcar_emp", "newcar_estab"]]
    config.RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df
