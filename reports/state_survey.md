# State survey: local tire-dealer sales data (2026-10-15)

**Result: no surveyed state passes.** No state checked publishes tire dealers (NAICS 441320/441340/44132, or a "tire dealers" label) as a separate category at county or city level. Every state checked either stops at NAICS 4413 or coarser locally, or publishes no local industry detail at all. One lead is unresolved: **Oklahoma** (see below).

Go/no-go test: (1) a separate tire-dealer category, (2) county or city geography, (3) at least 5 years of history. States are recorded at the first test they fail. Survey time box: about 1 hour, which ran out before the last ten states got a full check.

**Evidence levels**
- **Verified:** I downloaded the official data and inspected the categories. `scripts/survey/check_categories.py` reproduces this.
- **Documented:** the official source's report or documentation shows the category scheme, but I did not download the data.
- **Uncertain:** not confirmed from a primary source in the time box.

## Table

Columns after "Tire category?" are filled only for passing states. None passed, so they are blank (—).

| State | Tire category? (finest local detail) | Geography | Frequency | History | Measures | Suppression | Labour taxed? | Access | Verdict | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| California | No: 4413 "Automotive Parts, Accessories and Tire Stores" (counties); 441 only (cities) | County, city | Quarterly | County/city industry tables 2009–2014 in the API | Taxable sales, permits | — | — | OData API | **FAIL (1)** | Verified |
| Colorado | No: NAICS 441 "Motor Vehicle and Parts Dealers" | County, city | Monthly | 2016– | Gross, retail, net taxable sales | "NR" if fewer than 3 taxpayers or one is over 80% | — | Google Sheets/PDF | **FAIL (1)** | Verified (2024 county report) |
| Utah | No: economic supersectors only locally | City, county | Monthly | — | Taxable sales | — | — | XLSX | **FAIL (1)** | Verified (Apr 2025 file) |
| Minnesota | No: 4413 is the finest code even statewide, so local tables cannot be finer | City, county | Annual | — | Gross, taxable, tax, filers | — | — | XLSX | **FAIL (1)** | Verified (statewide 4-digit file) |
| Iowa | No: 12 business groups | County, city | Quarterly/annual | FY2000– | Taxable sales | "S" if fewer than 5 permits | — | data.iowa.gov | **FAIL (1)** | Documented |
| Ohio | No local industry detail found | — | — | — | — | — | — | — | **FAIL (1)** | Uncertain |
| North Carolina | No: major business groups (e.g. "Automotive") | County | Annual | FY2000– | Collections, taxable sales | — | — | PDF | **FAIL (1)** | Documented |
| Virginia | No: NAICS 441 | County, independent city | Quarterly, annual | NAICS since Q3 2005 | Taxable sales | — | — | XLSX (Cooper Center) | **FAIL (1)** | Verified (Q4 2025 file) |
| Oklahoma | **Unresolved:** OTC lists a "Tax Collections by NAICS" report on OkTAP; a private aggregator (MuniRevenue) shows city NAICS breakdowns sourced from OkTAP. The digit level is unknown | City (likely) | Monthly | Aggregator data 2020– | Tax collections, not sales | Unknown | Unknown | OkTAP web app: automated requests hit a redirect loop, so I stopped | **UNKNOWN: needs a manual check** | Uncertain |
| Arizona | No industry-by-place data found; TPT is reported by business class (e.g. "Retail") | — | — | — | — | — | — | — | **FAIL (1)** | Uncertain |
| Missouri | No local industry data found | — | — | — | — | — | — | — | **FAIL (1)** | Uncertain |
| Kansas | No: NAICS only for statewide collections; city/county reports are totals | — | — | — | — | — | — | — | **FAIL (1)** | Documented (report index) |
| Nebraska | No industry split found; monthly county/city totals only | — | — | — | — | — | — | — | **FAIL (1)** | Uncertain |
| Wisconsin | Not checked (time box) | — | — | — | — | — | — | — | Not checked | — |
| Idaho | Not checked (time box) | — | — | — | — | — | — | — | Not checked | — |
| Tennessee | No county-by-industry series found; statewide collections plus local distributions | — | — | — | — | — | — | — | **FAIL (1)** | Uncertain |
| Florida | No: kind code 24 is "Auto Accessories, Tires, Parts" | County | Monthly | — | Gross, taxable sales | — | — | Web tables | **FAIL (1)** | Documented |
| New York | No: 4413 "Automotive Parts, Accessories, and Tire Retailers" | County, some cities | Quarterly | 2013– (PDFs back to 1995) | Taxable sales and purchases | — | — | Socrata API | **FAIL (1)** | Verified |
| Georgia | No: commodity sectors (e.g. "Auto") | County | Monthly | — | LOST distributions, not sales | — | — | XLSX, georgiadata.org | **FAIL (1)** | Documented |
| Illinois | Not checked (time box) | — | — | — | — | — | — | — | Not checked | — |
| Michigan | Not checked (time box) | — | — | — | — | — | — | — | Not checked | — |

## Passing states, ranked

None.

## Next step if pursued

Check Oklahoma manually: open the OkTAP Public Reports page in a browser and look at the "Tax Collections by NAICS" report for one city (e.g. Tulsa). Find out whether it shows 6-digit NAICS 441320, and whether it reports tax collected (needs dividing by the local rate) or sales. Note two limits on comparability with Washington. Oklahoma's measure is tax remitted, which is not the gross receipts Washington reports. Oklahoma's sales tax on installation labour has not been checked.

## Sources

- California CDTFA OData API: https://cdtfa.ca.gov/dataportal/api/odata/ (sets `Taxable_Sales_Large_Counties`, `Taxable_Sales_Large_Cities`, `Taxable_Sales_by_Type_of_Business`). Research page: https://cdtfa.ca.gov/legal/research-and-statistics
- Colorado: https://cdor.colorado.gov/retail-sales-reports; 2024 county-by-industry report: https://spl.cde.state.co.us/artemis/revserials/rev13026internet/rev130262024internet.pdf; confidentiality note: https://spl.cde.state.co.us/artemis/revserials/rev13025internet/rev13025201707internet.pdf
- Utah: https://tax.utah.gov/econstats/sales; file: https://files.tax.utah.gov/tax/esu/sales-month/2025-04-monthly-sales.xlsx
- Minnesota: https://www.revenue.state.mn.us/mndor-pp/21281?type=html; file: https://www.revenue.state.mn.us/sites/default/files/2025-06/mn-state-4-digit-industry-code-2023.xlsx
- Iowa (report describing the data.iowa.gov 12-group dataset and its suppression rule): https://revenue.iowa.gov/media/3373/download
- North Carolina: https://ncdor.gov/documents/reports/fy14-15salesusestats/open
- Virginia: https://www.coopercenter.org/taxable-sales; file: https://www.coopercenter.org/sites/default/files/2026-04/QuarterlyTaxableSalesReport_2025_Q4.xlsx
- Oklahoma: https://oklahoma.gov/tax/reporting-resources/reports.html; OkTAP: https://oktap.tax.ok.gov/OkTAP/Web/?Link=PublicReports; aggregator (secondary): https://munirevenue.com/
- Kansas: https://www.ksrevenue.gov/prsalesreports.html
- Nebraska: https://revenue.nebraska.gov/node/1370
- Tennessee: https://www.tn.gov/content/dam/tn/revenue/documents/pubs/2025/Coll202506.pdf
- Florida: https://floridarevenue.com/dataportal/Pages/TaxResearch.aspx; kind code 24: https://floridarevenue.com/taxes/tables/f10cy2001r.html
- New York: https://data.ny.gov/resource/ny73-2j3u.json; https://www.tax.ny.gov/research/stats/stat_excise/taxable_sales_and_purchases/taxable_sales_and_purchases_open_data.htm
- Georgia: https://georgiadata.org/node/262

No `data/raw/survey_<state>_sample.csv` files were created, because no state passed.
