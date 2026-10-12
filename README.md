# Washington tire market opportunity (POC)

We asked which Washington counties have independent tire-dealer sales above what registered vehicles and dealership activity predict, and growing faster than the local vehicle fleet. Using state taxable-sales data (2015–2026) and vehicle registrations, we modelled expected tire-dealer sales with two dealer-activity controls (Census dealer employment as primary, dealer taxable sales as secondary). We flagged counties above expectation beyond typical model error whose real tire-dealer growth beat registered-vehicle growth from 2019 to 2025. **Kittitas is the one robust candidate** (flagged under both controls) and **Asotin is on watch** (flagged under dealer sales only, no Census data). The main caveat: each county's growth comes mostly from a single city (Cle Elum 73%, Clarkston 96%), and a tire-dealer share gain could come from dealerships, big-box or online sellers alike, so these are **candidates to investigate, not proof** that dealerships are losing tire business.

## Question

Which Washington counties have tire-shop (independent tire dealer) sales **above** what registered vehicles and dealership activity would predict, and tire-shop sales **growing faster** than the local vehicle fleet?

## Candidates (tiered)

| County | Tier | Reason | Largest single source of growth |
|---|---|---|---|
| **Kittitas** | **Robust** | Flagged under both dealer measures. | Cle Elum, 73% |
| Asotin | Watch | Flagged under dealer sales only; it cannot be assessed under CBP dealer employment because CBP publishes no data for it. | Clarkston, 96% |

- **Robust** = top candidate under both dealer measures. **Watch** = top candidate under one measure only. The two views are not weighted equally.
- The last column is the share of the county's disclosed tire-sales growth (2019→2025) that comes from its largest single jurisdiction.
- Generated in `data/processed/candidate_tiers.csv`.

**Read Kittitas with care:**
- Its growth is a step change in Cle Elum from 2024Q2: quarterly tire-dealer sales went from about $20k to about $900k with the same 5–8 taxpayers. That points to one business opening, expanding, being reclassified or changing where it reports sales.
- Without Cle Elum, Kittitas's tire sales are flat to falling since 2022.
- Its CBP residual is 1.06× typical error, just over the 1× threshold.

### Signals by view

The growth gap is the same in both views: real tire-dealer growth minus registered-vehicle growth, 2019→2025, net of the view's county trend. Dealer activity enters only the level model, so the views differ in their residuals and in which counties they cover.

| County | View | Test years above expected | Residual (recent) | Residual ÷ typical error | Real tire growth 2019→25 | Vehicle growth 2019→25 | Relative gap (log) | Growth rank | Top candidate |
|---|---|---|---|---|---|---|---|---|---|
| **Kittitas** | CBP (20 counties) | 2 of 2 | +12% | 1.06× | +14% | −0.4% | +0.11 | 3 of 20 | **yes** |
| **Kittitas** | Sales (29 counties) | 4 of 4 | +50% | 2.3× | +14% | −0.4% | +0.11 | 6 of 29 | **yes** |
| Asotin | Sales (29 counties) | 4 of 4 | +121% | 4.5× | +16% | −5% | +0.17 | 3 of 29 | yes |
| Grant | both | all | +30% / +50% | 2.4× / 2.3× | +9% | +5% | +0.01 | 9 of 20 / 16 of 29 | no: tires grew about as fast as vehicles |
| Jefferson | Sales | 4 of 4 | +67% | 2.9× | +3% | −4% | +0.04 | 13 of 29 | no: gap outside the top quartile |

**What changed from comparing with dealer activity:**
- Grant (previously Robust) drops: its tire growth tracks its growing vehicle fleet.
- Kittitas rises: its tire growth beats a flat fleet in both views.
- Asotin enters: its tire growth beats a shrinking fleet.

Plausible explanations other than dealer loss are listed as **hypotheses** in notebook section 6: Kittitas's I-90 corridor and Cle Elum step change; Asotin's cross-border Lewiston–Clarkston market. **Dealer tire share is not observable**, so a tire-dealer share gain could come from dealerships, big-box or online sellers, or from higher tire spending per vehicle.

Full rankings: `data/processed/signals_cbp_emp.csv`, `signals_sales.csv`, `candidates_by_view.csv`. Notebook: `notebooks/wa_tire_opportunity.ipynb`.

## Other findings

In the CBP model, dealer employment adds little once vehicles are included: its coefficient is 0.15 (p = 0.30), against 0.65 for vehicles (p < 0.001). In this data, tire-dealer sales track cars on the road more than dealer presence. This is an observation from 20 Washington counties over 2017–2023, not a general conclusion.

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
3. **Model (level):** OLS of log real tire sales on log vehicles + log dealer activity + year effects, with standard errors clustered by county. This is the only place dealer activity is used.
   - CBP view: vehicles 0.65 (p < 0.001), dealer employment 0.15 (p = 0.30, not significant).
   - Sales view: vehicles 0.40, dealer sales 0.35.
4. **Split:** train 2017–2021; test 2022 to the last year of each view. Both methods are calibrated each year to the actual total of the counties in the view.
5. **Signals**, from out-of-sample test predictions:
   - **Residual flag:** above expected in every recent test year, and the mean recent log residual is more than 1× typical error. Typical error is the median absolute test log error: 0.11 in the CBP view, 0.18 in the sales view.
   - **Growth flag:** top quartile on the relative growth gap, with the gap > 0 and real tire growth > 0. The relative gap is (county − state tire growth) − (county − state registered-vehicle growth), 2019→2025. It ranks counties exactly like the raw gap; only the zero line moves. Dealer activity is not used here.
   - **Top candidate:** both flags.

## Evaluation (test years)

| View | Test years | County-years | Baseline MAPE | Model MAPE | Baseline MALE | Model MALE |
|---|---|---|---|---|---|---|
| CBP employment (primary) | 2022–2023 | 40 | 20.7% | 13.7% | 0.237 | 0.132 |
| Dealer sales (secondary) | 2022–2025 | 116 | 77.4% | 43.5% | 0.358 | 0.305 |

The views cover different counties: CBP excludes the smallest, noisiest counties. Their errors are therefore not directly comparable.

## Key caveats (full list with impacts: `CAVEATS.md`)

- One state; 20 (CBP) or 29 (sales) counties modelled; small samples.
- Dealer tire share is not observable. A tire-dealer share gain could come from dealerships, big-box or online sellers, or from higher tire spending per vehicle.
- One jurisdiction can drive a county's signal (Kittitas: Cle Elum 73%; Asotin: Clarkston 96%).
- Dealer activity is a weak control in the level model only. Dealer sales mostly reflect new-car sales, which fell nationally after 2019.
- CBP ends in 2023, so the primary view's level model has only 2 test years.
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
- `tests/`: 5 focused tests (code combining, no double counting, non-negative sales, error-scaled residual, growth gap vs vehicles).
- `reports/`: state data check, location-code rule, pipeline summary.
