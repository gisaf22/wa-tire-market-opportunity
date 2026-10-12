"""WA DOR taxable retail sales pulls and the location-code rule.

Location codes are CCNN: CC = county number (01-39), NN = 00 for the
unincorporated county area, otherwise a city. Rule (see reports/location_codes.md):
  keep   NN == 00 (unincorporated) and city codes
  drop   transit-area codes (label contains "PTBA"): overlays, would double count
  drop   CC99 codes ("Thurston County" etc.): return no records for any NAICS
"""

import difflib
import html
import re
import time

import pandas as pd
import requests

from wa_tire import config

session = requests.Session()
session.headers["User-Agent"] = "tire-market-feasibility research (python-requests)"


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def name_key(name):
    """Normalise jurisdiction names: results say 'Spokane City', the form says 'Spokane (City)'."""
    key = re.sub(r"\b(city|only)\b", "", name.lower())
    return re.sub(r"[^a-z]", "", key)


def match_code(label, key_to_code):
    """Location code for a results label; closest name within the county if not exact (form has typos, e.g. 'Nothport')."""
    key = name_key(label)
    if key in key_to_code:
        return key_to_code[key]
    close = difflib.get_close_matches(key, list(key_to_code), n=1, cutoff=0.8)
    if not close:
        raise KeyError(f"no location code for results label {label!r}")
    return key_to_code[close[0]]


def to_number(s):
    s = s.replace("$", "").replace(",", "")
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def classify_location(code, label):
    if "PTBA" in label.upper():
        return "drop_ptba"
    if code.endswith("99"):
        return "drop_99"
    if code.endswith("00"):
        return "unincorporated"
    return "city"


def get_form_options():
    """Return (quarters, locations DataFrame) from the report builder form."""
    page = session.get(f"{config.DOR_BASE}/Report.aspx", timeout=60).text
    out = {}
    for sel_id in ("MainContent_lstbYear", "MainContent_lstbLoc"):
        body = re.search(rf'<select[^>]*id="{sel_id}"[^>]*>(.*?)</select>', page, re.S).group(1)
        out[sel_id] = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', body)
    quarters = sorted(v for v, _ in out["MainContent_lstbYear"] if re.fullmatch(r"\d{4}Q[1-4]", v))
    locs = pd.DataFrame(
        [(c, strip_tags(lab)[len(c):].strip(" -")) for c, lab in out["MainContent_lstbLoc"]],
        columns=["location_code", "location"],
    )
    locs["county_no"] = locs["location_code"].str[:2]
    locs["rule"] = [classify_location(c, n) for c, n in zip(locs["location_code"], locs["location"])]
    names = (
        locs[locs["rule"] == "unincorporated"]
        .assign(county=lambda d: d["location"].str.replace("Unincorporated ", "").str.replace(" County", ""))
        .set_index("county_no")["county"]
    )
    locs["county"] = locs["county_no"].map(names)
    return quarters, locs


def fetch(quarters, loc_codes):
    """One Results.aspx request; returns raw rows [label, year, tax_type, naics, taxable, units]."""
    lo, hi = config.QUERY_CODE_RANGE
    params = {
        "Year": ",".join(quarters), "Code1": lo, "Code2": hi, "Sumby": "n6", "SicNaics": "2",
        "Location": ",".join(loc_codes), "Format": "HTML", "TaxType": config.DOR_TAX_TYPE,
    }
    r = session.get(f"{config.DOR_BASE}/Results.aspx", params=params, timeout=300)
    r.raise_for_status()
    rows = []
    # The label may contain <b><font> wrappers depending on the User-Agent.
    for label, table in re.findall(r'id="MainContent_lbl\d+"[^>]*>(.*?)</span>\s*<table(.*?)</table>', r.text, re.S):
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)[1:]:
            cells = [strip_tags(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) == 5:
                rows.append([strip_tags(label)] + cells)
    return rows


def pull_sales(refresh=False):
    """Jurisdiction x quarter x NAICS rows for kept locations. Cached in data/raw/."""
    out = config.RAW / "wa_dor_trs_jurisdiction.csv"
    loc_out = config.RAW / "wa_dor_locations.csv"
    if out.exists() and loc_out.exists() and not refresh:
        return (pd.read_csv(out, dtype={"location_code": str, "naics": str, "county_no": str}),
                pd.read_csv(loc_out, dtype={"location_code": str, "county_no": str}))
    quarters, locs = get_form_options()
    quarters = [q for q in quarters if q >= config.FIRST_QUARTER]
    kept = locs[locs["rule"].isin(["city", "unincorporated"])]
    cache = config.RAW / "wa_dor_cache"
    cache.mkdir(parents=True, exist_ok=True)
    records = []
    for county_no, grp in kept.groupby("county_no"):
        key_to_code = {name_key(n): c for c, n in zip(grp["location_code"], grp["location"])}
        part = cache / f"{county_no}_{quarters[0]}_{quarters[-1]}.csv"
        if part.exists() and not refresh:
            rows = pd.read_csv(part, dtype=str, keep_default_na=False).values.tolist()
        else:
            rows = fetch(quarters, list(grp["location_code"]))
            pd.DataFrame(rows, columns=["label", "year", "tax", "naics", "taxable", "units"]).to_csv(part, index=False)
            time.sleep(config.REQUEST_PAUSE_S)
        for label, year, _tax, naics, taxable, units in rows:
            q = re.fullmatch(r"(\d{4}) Quarter (\d)", year)
            records.append({
                "county_no": county_no, "county": grp["county"].iloc[0],
                "location_code": match_code(label, key_to_code), "location": label,
                "quarter": f"{q.group(1)}Q{q.group(2)}", "naics": naics,
                "taxable_sales": to_number(taxable), "units": to_number(units),
                "hidden": taxable.strip() == "D",
            })
        print(f"  {grp['county'].iloc[0]}: {len(grp)} jurisdictions")
    df = pd.DataFrame(records)
    df = df[df["naics"].isin(config.SERIES)]
    config.RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    locs.to_csv(loc_out, index=False)
    return df, locs
