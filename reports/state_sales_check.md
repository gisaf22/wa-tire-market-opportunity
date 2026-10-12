# State tire-dealer sales check

Checked 2026-10-12. Availability and quality only; no modelling.

## Verdict

**Recommended state: Washington.** It passes questions 1–3.

- **Tire dealers are a separate category:** six-digit NAICS 441320, which becomes 441340 under 2022 NAICS.
- **Geography:** reported by local jurisdiction (each city plus each county's unincorporated area). These can be summed to all 39 counties.
- **Frequency and history:** quarterly, 2005Q1–2026Q1 (85 quarters).

| State | Tire-dealer category? | Geography | Frequency | History | Measures | Suppression (tire dealers) | Access | Verdict |
|---|---|---|---|---|---|---|---|---|
| **Washington** (DOR Taxable Retail Sales, local) | **Yes**, six-digit: 441320 (2005Q1–2022Q1), 441340 (2022Q2–) | 325 cities and unincorporated areas → 39 counties (summed) | Quarterly (and annual) | 2005Q1 – 2026Q1 | Taxable retail sales; units (number of reporting taxpayers). No gross sales at local level. | Per jurisdiction: "D" when there are fewer than 3 firms. In the sample, 30% of jurisdiction-quarter rows are hidden. At county level: in large counties, at most 2–6% of accounts are hidden (2020s median). Tiny counties are mostly hidden. | Public web report builder. Results come from a plain GET URL that scripts can call (no login, CAPTCHA, or robots.txt). No stated terms of use. | **GO** |
| Washington (DOR Quarterly Business Review, Table 3) | **No**: only 4413 "Automotive Parts & Tire" | 39 counties (has county totals) | Quarterly | 2004 – 2026Q1 | Taxable retail sales, units | n/a | Same builder style | NO-GO (parts and tires combined) |
| Texas (Comptroller Quarterly Sales Tax Historical Data) | **No**: 23 two-digit sectors only (e.g. "Retail Trade" 44-45) | 254 counties, cities, MSAs | Quarterly | 2002 – 2026 (web); 2016 – 2026 (open-data API) | Gross sales, amount subject to tax, outlets | n/a | Web form and Socrata API `7z4d-yf2c` | NO-GO |
| Virginia | Not checked | – | – | – | – | – | – | Not checked: the task says to stop once one state passes |

## Washington detail

**Source:** WA Dept. of Revenue, Taxable Retail Sales (local) report builder
https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal/Report.aspx
Results endpoint, example call:
`https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal/Results.aspx?Year=2025Q4,2025Q3&Code1=441320&Code2=441340&Sumby=n6&SicNaics=2&Location=1700,1726&Format=HTML&TaxType=45`
Definitions: https://dor.wa.gov/about/frequently-asked-questions

1. **Category.** Six-digit NAICS is selectable ("Sum By: Six Digit NAICS").
   - 441320 Tire Dealers covers 2005Q1–2022Q1.
   - 441340 Tire Dealers covers 2022Q2 onward. DOR moved accounts to 2022 NAICS from 2022Q2.
   - King and Spokane show no level break between 2022Q1 and 2022Q2. The code change is a relabel, but the join must map both codes.
2. **Geography.**
   - Each location code is CCNN. CC is the county number (01–39). NN=00 is the unincorporated county area; other NN values are cities.
   - Cities that span counties are already split by county (e.g. "Auburn/King Only").
   - The local builder has no county-total code, so county figures are sums of jurisdictions.
   - I excluded the transit-area codes (PTBA, e.g. 2727) and a few `xx99` codes (e.g. 3499 "Thurston County"). I did not confirm what the `xx99` codes represent; they may be special taxing districts. They should be checked before a full pull so nothing is double-counted or missed.
3. **Frequency and history.** Quarterly from 2005Q1 to 2026Q1, 85 quarters. Annual totals are also offered. SIC-based data (1994–2004) exists but is not comparable.
4. **Measures.**
   - **Taxable retail sales:** the local sales-tax base, with tax type "Sales". Use tax is a separate option.
   - **Units:** the number of taxpayers reporting in that jurisdiction. Branches at one location count as one unit.
   - **Gross sales are not available at local level.** DOR's Gross Business Income builder has no location selector (statewide only), and the FAQ says state B&O income is not tied to a location.
   - *Inference, not verified:* units are taxpayer accounts, not stores. King's units step up at 2008Q3 (90 → 121) and keep rising from 2018 (≈270 → 435 by 2020s). Those dates line up with WA's July 2008 destination-sourcing change and its 2018 remote-seller and marketplace rules. Taxable sales show no matching jumps. Units should not be used as a store count.
5. **Suppression.**
   - The FAQ says: "If a particular SIC or NAICS grouping contains fewer than three firms then the data cannot be disclosed."
   - Sales and units are suppressed together. The smallest disclosed unit count in the sample is 3, which matches the rule. Each suppressed jurisdiction therefore hides at most 2 taxpayers.
   - In the sample, almost every large-county quarter has at least one suppressed small city. The upper-bound share of hidden *accounts* is low and falls over time. Hidden dollar share is unknown but probably similar (inference).

   | County (sample) | Quarters with no suppression | Median max-hidden-units share, 2005–12 → 2020–26 | Notes |
   |---|---|---|---|
   | King | 0 / 85 | 17% → 2% | Disclosed ≈ $61M/quarter (2020s median) |
   | Spokane | 0 / 85 | 15% → 6% | |
   | Yakima | 1 / 85 | 36% → 5% | |
   | Whatcom | 27 / 85 | 26% → 2% | |
   | Garfield (pop. ~2k) | 2 / 85 | 100% | 59 quarters fully hidden, 17 with no tire dealers at all |

   Implication: large and mid-size counties are usable as a lower-bound series with a known, small hidden-account margin. Very small counties are not usable.
6. **Access.**
   - ASP.NET form. The results page is a plain GET with comma-separated `Year` and `Location` lists, so no form-state handling is needed.
   - `Year=All` is **not** accepted via GET; quarters must be listed explicitly.
   - The page says to limit each query to 100 locations.
   - No robots.txt (404) and no data-reuse terms. The only notice is the footer copyright, "Washington State Department of Revenue and its licensors. All rights reserved." Underlying figures are public statistics, but reuse terms are unstated.
   - Non-browser User-Agents receive older HTML markup. The script handles both versions.

### Sample pulled

- Script: `scripts/wa_tire_sample.py` (Python, pandas, requests). Run it as `python3 scripts/wa_tire_sample.py` from the repo root; it takes about 1 minute and makes 20 requests with 1 s pauses.
- `data/raw/wa_dor_trs_tire_sample_jurisdiction.csv` has 5,157 rows covering 79 jurisdictions in King, Spokane, Yakima, Whatcom and Garfield, 2005Q1–2026Q1. Raw strings are kept alongside the parsed numbers.
- `data/raw/wa_dor_trs_tire_sample_county.csv` has county × quarter rows: disclosed sales, units, jurisdictions reporting, jurisdictions suppressed, and a no-rows flag. All 85 quarters are present for each county.
- Seasonality is visible: Q4 is 20–54% above the Q1–Q3 average (median by county, 2010–2025; King lowest, Spokane highest), consistent with winter-tire demand.
- A full 39-county pull would take about 160 requests.

## Texas detail (no-go)

- Web form: https://mycpa.cpa.state.tx.us/allocation/HistSales. The industry selector lists 23 two-digit sectors only.
- A Harris County "Retail Trade" query returned gross sales, amount subject to tax, and outlets by quarter from 2002. There was no finer breakdown.
- The open-data copy, https://data.texas.gov/resource/7z4d-yf2c.json (1.1M rows, 2016–2026), has the same 23 industries.
- I did not search for other Texas sources (e.g. public-records requests for NAICS-level data).

## Uncertainty and not verified

- What the `xx99` location codes in the WA local builder are (see Geography above).
- Whether WA ever suppresses an extra cell to stop a hidden one being worked out by subtraction. No sign of it in the sample: only cells with fewer than 3 units are hidden.
- How much of WA's 441320/441340 taxable sales comes from remote or online sellers rather than local shops. This matters for interpreting the series.
- Reliance on the scraped HTML layout. If DOR changes the page, the parser in the script breaks.
- Virginia was not assessed.

---
Washington DOR publishes six-digit tire-dealer (441320 → 441340) taxable retail sales and taxpayer counts quarterly from 2005Q1 to 2026Q1, by city and unincorporated area, which sum to counties.
Suppression is limited to cells with fewer than 3 firms. Large counties hide only a few percent of accounts; tiny counties are mostly hidden. Texas offers only broad sectors (no-go), and Virginia was not checked.
A 5-county sample and a re-runnable script are in `data/raw/` and `scripts/`.

Decision needed: whether taxable retail sales plus a taxpayer count, with no gross sales, is an acceptable measure for the feasibility work. If yes, the next step is a full 39-county pull after resolving the `xx99` location codes.
