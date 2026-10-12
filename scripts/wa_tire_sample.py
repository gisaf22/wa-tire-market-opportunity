"""Pull a small sample of Washington DOR taxable retail sales for tire dealers.

Source: WA Dept. of Revenue, Taxable Retail Sales (local) report builder
https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal/Report.aspx

Tire dealers are NAICS 441320 (2017 NAICS, 2005Q1-2022Q1) and 441340
(2022 NAICS, 2022Q2 onward). The builder reports by local jurisdiction
(each city plus the unincorporated county area), so county figures are the
sum of a county's jurisdictions.

Usage (from the repo root):
    python3 scripts/wa_tire_sample.py

Writes:
    data/raw/wa_dor_trs_tire_sample_jurisdiction.csv  (one row per jurisdiction x quarter x NAICS)
    data/raw/wa_dor_trs_tire_sample_county.csv        (county x quarter, with suppression counts)
"""

import html
import re
import time
from pathlib import Path

import pandas as pd
import requests

BASE = "https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal"
TIRE_CODES = {"441320", "441340"}
# Two-digit DOR county prefixes: King, Spokane, Yakima, Whatcom, Garfield.
SAMPLE_COUNTIES = {"17": "King", "32": "Spokane", "39": "Yakima", "37": "Whatcom", "12": "Garfield"}
QUARTERS_PER_REQUEST = 24
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

session = requests.Session()
session.headers["User-Agent"] = "tire-market-feasibility research script (python-requests)"


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def get_options():
    """Return (quarters, locations) from the report builder form."""
    page = session.get(f"{BASE}/Report.aspx", timeout=60).text
    selects = {}
    for sel_id in ("MainContent_lstbYear", "MainContent_lstbLoc"):
        body = re.search(rf'<select[^>]*id="{sel_id}"[^>]*>(.*?)</select>', page, re.S).group(1)
        selects[sel_id] = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', body)
    quarters = sorted(v for v, _ in selects["MainContent_lstbYear"] if re.fullmatch(r"\d{4}Q[1-4]", v))
    # Keep cities and unincorporated areas; drop transit (PTBA) and xx99 special codes.
    locations = [
        (code, strip_tags(label)[len(code):].strip())
        for code, label in selects["MainContent_lstbLoc"]
        if not code.endswith("99") and "PTBA" not in label
    ]
    return quarters, locations


def fetch(quarters, loc_codes):
    params = {
        "Year": ",".join(quarters),
        "Code1": "441320",
        "Code2": "441340",
        "Sumby": "n6",
        "SicNaics": "2",
        "Location": ",".join(loc_codes),
        "Format": "HTML",
        "TaxType": "45",  # retail sales tax (not use tax)
    }
    r = session.get(f"{BASE}/Results.aspx", params=params, timeout=300)
    r.raise_for_status()
    rows = []
    # The label may contain <b><font> wrappers depending on the User-Agent.
    for label, table in re.findall(r'id="MainContent_lbl\d+"[^>]*>(.*?)</span>\s*<table(.*?)</table>', r.text, re.S):
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)[1:]:
            cells = [strip_tags(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) == 5:
                rows.append([strip_tags(label)] + cells)
    return rows


def name_key(name):
    """Normalise jurisdiction names: results say 'Spokane City', the form says 'Spokane (City)'."""
    key = re.sub(r"\b(city|only)\b", "", name.lower())
    return re.sub(r"[^a-z]", "", key)


def to_number(s):
    s = s.replace("$", "").replace(",", "")
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    quarters, locations = get_options()
    print(f"{len(quarters)} quarters available: {quarters[0]} to {quarters[-1]}")

    records = []
    for prefix, county in SAMPLE_COUNTIES.items():
        locs = [(c, n) for c, n in locations if c[:2] == prefix]
        name_to_code = {name_key(n): c for c, n in locs}
        for i in range(0, len(quarters), QUARTERS_PER_REQUEST):
            chunk = quarters[i : i + QUARTERS_PER_REQUEST]
            for label, year, tax_type, naics, taxable, units in fetch(chunk, [c for c, _ in locs]):
                q = re.fullmatch(r"(\d{4}) Quarter (\d)", year)
                records.append({
                    "county": county,
                    "county_prefix": prefix,
                    "location_code": name_to_code[name_key(label)],
                    "location": label,
                    "period": f"{q.group(1)}Q{q.group(2)}" if q else year,
                    "naics": naics,
                    "taxable_sales": to_number(taxable),
                    "units": to_number(units),
                    "taxable_raw": taxable,
                    "units_raw": units,
                })
            time.sleep(1)
        print(f"{county}: {len(locs)} jurisdictions fetched")

    df = pd.DataFrame(records)
    df = df[df["naics"].isin(TIRE_CODES)]
    df["suppressed"] = df["taxable_sales"].isna()
    df.to_csv(OUT_DIR / "wa_dor_trs_tire_sample_jurisdiction.csv", index=False)

    full = pd.MultiIndex.from_product([SAMPLE_COUNTIES.values(), quarters], names=["county", "period"])
    county = (
        df.groupby(["county", "period"])
        .agg(
            taxable_sales_disclosed=("taxable_sales", "sum"),
            units_disclosed=("units", "sum"),
            jurisdictions_reporting=("location", "nunique"),
            jurisdictions_suppressed=("suppressed", "sum"),
        )
        .reindex(full)
        .reset_index()
    )
    county["no_rows"] = county["jurisdictions_reporting"].isna()
    county = county.fillna({"jurisdictions_reporting": 0, "jurisdictions_suppressed": 0})
    county.to_csv(OUT_DIR / "wa_dor_trs_tire_sample_county.csv", index=False)

    print(f"\n{len(df)} jurisdiction rows; {df['suppressed'].mean():.1%} suppressed")
    summary = county.groupby("county").agg(
        quarters=("period", "size"),
        quarters_no_rows=("no_rows", "sum"),
        quarters_any_suppressed=("jurisdictions_suppressed", lambda s: int((s > 0).sum())),
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()
