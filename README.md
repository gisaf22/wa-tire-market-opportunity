# Washington tire market opportunity (POC)

## Question

Which Washington counties have tire-shop (independent tire dealer) sales **above** what registered vehicles and dealership activity would predict, and/or tire-shop sales **growing faster** than dealership activity?

These are *candidate* markets where dealerships may be losing tire business to independents. **They are not proof.**

## Answer

Three of the 29 modelled counties are in the top quartile on both signals:

| County | Residual 2023–25 (actual vs expected) | Real tire-dealer growth 2019→25 | Real new-car-dealer growth 2019→25 | Growth gap (log points) |
|---|---|---|---|---|
| **Kittitas** | +46% | +14% | −28% | 0.46 |
| **Grant** | +47% | +9% | −9% | 0.18 |
| **Jefferson** | +54% | +3% | −23% | 0.28 |

**Most of the growth gap comes from falling new-car-dealer taxable sales, not booming tire shops.**
- Kittitas has the most convincing pattern: tire sales grew 14% while dealer sales fell.
- Jefferson's signal is fragile. Its dealer sales are tiny (about $1M a year), volatile and often suppressed.

Two other counties have the largest gaps (Stevens 2.11, Island 0.94), but there tire sales were flat and dealer sales collapsed. Neither is flagged, because their residuals are near zero.

Full ranking: `data/processed/signals.csv`. Notebook: `notebooks/wa_tire_opportunity.ipynb`.

## Data sources

| Data | Source | Coverage |
|---|---|---|
| Taxable retail sales by NAICS: tire dealers 441320 (to 2022Q1) + 441340 (from 2022Q2); new-car dealers 441110 | [WA DOR Taxable Retail Sales builder](https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal/Report.aspx) | 325 cities and unincorporated areas → 39 counties, 2015Q1–2026Q1 |
| Vehicle registrations (Passenger Vehicle + Truck, by owner's county) | [WA DOL via data.wa.gov `hmzg-s6q4`](https://data.wa.gov/resource/hmzg-s6q4.json) | 39 counties, 2017–2025 (monthly data start January 2017) |
| CPI-U Tires `CUUR0000SETC01`; New vehicles `CUUR0000SETA01` | [BLS API](https://api.bls.gov/publicAPI/v1/timeseries/data/) | 2015–2026, U.S. city average |

Jurisdictions are summed to counties using the rule in `reports/location_codes.md`. Transit-area (PTBA) codes and empty `xx99` codes are dropped. The sums match DOR's own county totals to within 1%.

## Method

1. **Build.**
   - County × quarter disclosed sales, plus a count of hidden ("D", fewer than 3 taxpayers) cells.
   - Deflated to 2025 dollars: tire CPI for tire sales, new-vehicle CPI for dealer sales.
   - Aggregated to county × year for modelling.
   - Counties are excluded where suppressed cells could hold more than 25% of tire-dealer taxpayers in more than 25% of quarters, or where a model year has no disclosed sales. This excludes 10 counties: Columbia, Douglas, Garfield, Grays Harbor, Lincoln, Pacific, Pend Oreille, Skamania, Wahkiakum, Whitman.
   - Checks: no level jump at the 2022 NAICS switch (statewide Q2/Q1 = 1.08 in 2022 vs 0.99–1.12 in other years). Quarter-over-quarter outliers are flagged in `qoq_outliers.csv`; 44 are flagged, mostly in small counties where cells flip between hidden and disclosed.
2. **Baseline:** statewide real tire sales per registered vehicle × county vehicles.
3. **Model:** OLS of log real tire sales on log vehicles + log real new-car-dealer sales + year effects, with standard errors clustered by county. Full-sample elasticities are 0.41 for vehicles and 0.33 for dealer sales (R² 0.84).
4. **Split:** train 2017–2021, test 2022–2025. Both methods are calibrated each year to the actual statewide total, so the test measures how well each method allocates sales across counties.
5. **Signals.**
   - Residual: mean log(actual/expected) over 2023–2025, from the full-sample model.
   - Growth gap: real tire log growth minus real new-car-dealer log growth, 2019→2025.
   - Top candidate: top quartile on both signals, with both positive.

## Evaluation (test years 2022–2025, 29 counties × 4 years)

| Method | MAPE | Mean abs. log error |
|---|---|---|
| Baseline (sales per vehicle) | 77.4% | 0.358 |
| Log-linear model | 43.5% | 0.305 |

The model beats the baseline in every test year, but its county errors remain large.

## Key caveats (full list with impacts: `CAVEATS.md`)

- One state; 29 of 39 counties modelled; small sample.
- Taxable sales only. Hidden cells make county totals lower bounds.
- Dealer tire sales cannot be separated from car sales, so the growth gap mostly tracks dealer decline.
- Big-box, warehouse-club and online tire sellers are not captured.
- Demand comes from registration transactions, which start in 2017, so training is 2017–2021 rather than 2015–2021.
- Residuals can reflect cross-county shopping, fleet buyers, vehicle mix or where a business reports its sales.
- National CPIs; the October 2025 tire CPI was not published.
- **Results are candidates, not proof.**

## With company data

With a company's dealer-level data, this becomes a **dealer-level target list**:
- Each dealership's tire and service revenue and its customer addresses replace the county proxies.
- Dealers that under-capture tire demand relative to their vehicles sold or serviced, and relative to independent tire-dealer sales in their area, are ranked as targets.

## Run order

```zsh
pip install -e ".[dev]"
python3 scripts/run_pipeline.py      # uses cached pulls in data/raw/; add --refresh to re-pull
pytest
python3 -m ipykernel install --user --name wa-tire --display-name "Python (wa-tire)"   # once: the notebook uses this kernel
jupyter nbconvert --to notebook --execute --inplace notebooks/wa_tire_opportunity.ipynb
```

If `jupyter nbconvert` fails at startup with `No module named 'notebook.services'` (a stale `jupyter_contrib_nbextensions` install), run `jupyter execute --inplace notebooks/wa_tire_opportunity.ipynb` instead. It executes the same notebook through nbclient.

## Layout

- `src/wa_tire/`: all logic (config, pulls, build, model, evaluate, signals, plots).
- `scripts/run_pipeline.py`: end-to-end pipeline. It writes `data/processed/` and `reports/results_summary.md`.
- `tests/`: 5 focused tests (code combining, no double counting, non-negative sales, residual and growth-gap math).
- `reports/`: state data check, location-code rule, pipeline summary.
