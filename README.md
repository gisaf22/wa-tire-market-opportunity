# Washington tire market opportunity (POC)

## Question

Which Washington counties have tire-shop (independent tire dealer) sales **above** what registered vehicles and dealership activity would predict, and/or tire-shop sales **growing faster** than dealership activity?

These are *candidate* markets where dealerships may be losing tire business to independents. **They are not proof.**

## Answer

**Grant County is the one robust candidate.** It is flagged under both dealer measures.

**Primary view** (dealer activity = Census CBP new-car dealer employment, 2017–2023, 20 counties):

| County | Test years above expected | Residual (recent) | Residual ÷ typical error | Real tire growth 2019→23 | Dealer employment growth 2019→23 | Relative gap (log) | Top candidate |
|---|---|---|---|---|---|---|---|
| **Grant** | 2 of 2 | +30% | 2.4× | +12% | −16% | +0.17 | **yes** |
| Kittitas | 2 of 2 | +12% | 1.1× | −1% | +16% | −0.27 | no (growth flag fails) |
| Jefferson | – | – | – | – | – | – | not assessable: no CBP data |

**Secondary view** (dealer activity = DOR new-car-dealer real taxable sales, 2017–2025, 29 counties):

| County | Test years above expected | Residual (recent) | Residual ÷ typical error | Real tire growth 2019→25 | Dealer sales growth 2019→25 | Relative gap (log) |
|---|---|---|---|---|---|---|
| Grant | 4 of 4 | +50% | 2.3× | +9% | −9% | +0.19 |
| Kittitas | 4 of 4 | +50% | 2.3× | +14% | −28% | +0.47 |
| Jefferson | 4 of 4 | +67% | 2.9× | +3% | −23% | +0.30 |

**Why the list changes between views:** the difference comes from the shorter window and narrower county coverage, not from the employment measure itself. A one-off check, not part of the pipeline, ran dealer sales on CBP's 20 counties through 2023, and it also flags only Grant.
- Kittitas's tire growth came in 2024–25, after CBP's last year.
- Jefferson is not published in CBP.

Plausible non-dealer explanations for each flagged county are listed as **hypotheses** in notebook section 6. Examples: Grant's agricultural and fleet buyers; Kittitas's I-90 corridor; Jefferson's small, volatile, often-hidden data.

Full rankings: `data/processed/signals_cbp_emp.csv`, `signals_sales.csv`, `candidates_by_view.csv`. Notebook: `notebooks/wa_tire_opportunity.ipynb`.

## Data sources

| Data | Source | Coverage |
|---|---|---|
| Taxable retail sales by NAICS: tire dealers 441320 (to 2022Q1) + 441340 (from 2022Q2); new-car dealers 441110 | [WA DOR Taxable Retail Sales builder](https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal/Report.aspx) | 325 cities and unincorporated areas → 39 counties, 2015Q1–2026Q1 |
| New-car dealer employment, NAICS 441110 | [Census County Business Patterns API](https://api.census.gov/data/2023/cbp) (`CENSUS_API_KEY`) | 22–24 WA counties published per year, 2017–2023 (2024 not yet released) |
| Vehicle registrations (Passenger Vehicle + Truck, by owner's county) | [WA DOL via data.wa.gov `hmzg-s6q4`](https://data.wa.gov/resource/hmzg-s6q4.json) | 39 counties, 2017–2025 |
| CPI-U Tires `CUUR0000SETC01`; New vehicles `CUUR0000SETA01` | [BLS API](https://api.bls.gov/publicAPI/v1/timeseries/data/) | 2015–2026, U.S. city average |

Jurisdictions are summed to counties using the rule in `reports/location_codes.md`.

## Method

1. **Build.**
   - County × quarter disclosed sales, plus a count of hidden ("D") cells.
   - Deflated to 2025 dollars; aggregated to county × year.
   - 10 counties are excluded from all views for tire-data suppression.
   - Each view also drops counties missing its dealer measure in any model year.
   - No jump at the 2022 NAICS switch.
2. **Baseline:** real tire sales per registered vehicle × county vehicles.
3. **Model:** OLS of log real tire sales on log vehicles + log dealer activity + year effects, with standard errors clustered by county.
   - CBP view: vehicles 0.65 (p < 0.001), dealer employment 0.15 (p = 0.30, not significant).
   - Sales view: vehicles 0.40, dealer sales 0.35.
4. **Split:** train 2017–2021; test 2022 to the last year of each view. Both methods are calibrated each year to the actual total of the counties in the view.
5. **Signals**, from out-of-sample test predictions:
   - **Residual flag:** above expected in every recent test year, and the mean recent log residual is more than 1× typical error. Typical error is the median absolute test log error: 0.11 in the CBP view, 0.18 in the sales view.
   - **Growth flag:** top quartile on the relative growth gap, with the gap > 0 and real tire growth > 0. The relative gap is (county − state tire growth) − (county − state dealer growth). It ranks counties exactly like the raw gap; only the zero line moves.
   - **Top candidate:** both flags.

## Evaluation (test years)

| View | Test years | County-years | Baseline MAPE | Model MAPE | Baseline MALE | Model MALE |
|---|---|---|---|---|---|---|
| CBP employment (primary) | 2022–2023 | 40 | 20.7% | 13.7% | 0.237 | 0.132 |
| Dealer sales (secondary) | 2022–2025 | 116 | 77.4% | 43.5% | 0.358 | 0.305 |

The views cover different counties: CBP excludes the smallest, noisiest counties. Their errors are therefore not directly comparable.

## Key caveats (full list with impacts: `CAVEATS.md`)

- One state; 20 (CBP) or 29 (sales) counties modelled; small samples.
- Dealer sales mostly reflect new-car sales, which fell nationally after 2019. CBP employment is less sensitive to this but still measures the whole dealership, not its tire business.
- CBP ends in 2023, so the primary view has only 2 test years and misses 2024–25.
- Taxable sales only. Hidden cells make county totals lower bounds.
- Big-box, warehouse-club and online tire sellers are not captured.
- Demand comes from registration transactions starting in 2017.
- Residuals can reflect cross-county shopping, fleet buyers, vehicle mix or where a business reports its sales.
- National CPIs.
- **Results are candidates, not proof.**

## With company data

With a company's dealer-level data, this becomes a **dealer-level target list**:
- Each dealership's tire and service revenue and its customer addresses replace the county proxies.
- Dealers that under-capture tire demand relative to their vehicles sold or serviced, and relative to independent tire-dealer sales in their area, are ranked as targets.

## Run order

```zsh
pip install -e ".[dev]"
python3 scripts/run_pipeline.py      # uses cached pulls in data/raw/; add --refresh to re-pull (needs CENSUS_API_KEY)
pytest
jupyter execute --inplace notebooks/wa_tire_opportunity.ipynb
```

The notebook runs on a Jupyter kernel named `wa-tire` that points at the Python where the package is installed. If that kernel does not exist on your machine, register it once with `python3 -m ipykernel install --user --name wa-tire --display-name "Python (wa-tire)"`.

## Layout

- `src/wa_tire/`: all logic (config, pulls including CBP, build, model, evaluate, signals, plots).
- `scripts/run_pipeline.py`: end-to-end pipeline for both dealer views. It writes `data/processed/` and `reports/results_summary.md`.
- `tests/`: 5 focused tests (code combining, no double counting, non-negative sales, error-scaled residual, relative growth gap).
- `reports/`: state data check, location-code rule, pipeline summary.
