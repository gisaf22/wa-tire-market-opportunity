"""State survey: finest automotive/tire industry category published at local level.

Reproduces the test-1 checks behind reports/state_survey.md for states with
machine-readable sources. Prints the automotive/tire categories found per state.
Run: python scripts/survey/check_categories.py
"""
import io
import time

import pandas as pd
import requests

UA = {"User-Agent": "tire-market-feasibility state survey (research; polite pacing)"}
PAUSE = 1.5
AUTO = r"441|[Tt]ire|Auto|Motor Vehicle"


def get(url, **kw):
    r = requests.get(url, headers=UA, timeout=60, **kw)
    r.raise_for_status()
    time.sleep(PAUSE)
    return r


def california():
    base = "https://cdtfa.ca.gov/dataportal/api/odata"
    out = {}
    for s in ["Taxable_Sales_Large_Counties", "Taxable_Sales_Large_Cities"]:
        v = get(f"{base}/{s}", params={"$select": "BusinessType,CalendarYear", "$top": 100000}).json()["value"]
        df = pd.DataFrame(v)
        out[s] = sorted(df.loc[df.BusinessType.str.contains(AUTO), "BusinessType"].unique())
        out[s + " years"] = (df.CalendarYear.min(), df.CalendarYear.max())
    return out


def new_york():
    r = get("https://data.ny.gov/resource/ny73-2j3u.json", params={
        "$select": "naics_industry_group,description",
        "$group": "naics_industry_group,description",
        "$where": "starts_with(naics_industry_group,'441')"})
    return pd.DataFrame(r.json()).to_dict("records")


def excel_rows(url, sheet=None):
    x = pd.read_excel(io.BytesIO(get(url).content), sheet_name=sheet, header=None)
    frames = x.values() if isinstance(x, dict) else [x]
    hits = set()
    for d in frames:
        rows = d.astype(str).apply(lambda r: " | ".join(c for c in r if c != "nan"), axis=1)
        rows = rows[rows.str.contains(r"(?i)(^|\| )441|tire|motor vehicle")]
        # keep the category label, drop the numbers, so each category prints once
        hits |= set(rows.str.split(" | ", regex=False).str[:2].str.join(" | "))
    return sorted(hits)


def minnesota():
    # Statewide 4-digit table is the finest MN publishes; local tables cannot be finer.
    return excel_rows("https://www.revenue.state.mn.us/sites/default/files/2025-06/"
                      "mn-state-4-digit-industry-code-2023.xlsx")


def virginia():
    return excel_rows("https://www.coopercenter.org/sites/default/files/2026-04/"
                      "QuarterlyTaxableSalesReport_2025_Q4.xlsx", sheet="County")


def utah():
    return excel_rows("https://files.tax.utah.gov/tax/esu/sales-month/2025-04-monthly-sales.xlsx", sheet="Table 6")


if __name__ == "__main__":
    for name, fn in [("California", california), ("New York", new_york), ("Minnesota", minnesota),
                     ("Virginia", virginia), ("Utah", utah)]:
        try:
            print(f"== {name}\n{fn()}\n")
        except Exception as e:  # record and move on
            print(f"== {name}\nERROR: {e}\n")
