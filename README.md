# Washington tire market opportunity (POC)

We modelled expected tire-specialist sales (WA taxable sales of tire dealers, NAICS 441320 → 441340) from registered vehicles and two dealer-activity controls (Census dealer employment as primary, dealer taxable sales as secondary), using 2017–2025. We flagged counties whose tire-specialist sales sit above expectation beyond typical model error and grew faster than registered vehicles from 2019 to 2025, and capped any county at Watch when one city drives more than half of its growth. **No county is a robust candidate:** Kittitas passes under both dealer controls but is capped at Watch because Cle Elum alone accounts for 182% of its real tire-specialist growth, and Asotin is on Watch (dealer-sales view only; Clarkston 95%). The main caveat: both signals rest on one city each, and dealer tire sales are not observable, so these are **candidates to investigate, not proof** that dealerships are losing tire business.

## Question

Where in Washington do tire-specialist retailers (independent shops and tire chains) capture more tire sales than cars on the road and dealer activity would predict, and are they gaining share faster than vehicle growth? These are candidate markets where dealerships may be losing tire business.

"Tire specialists" below means tire-specialist retailers: independent shops and tire chains.

## Candidates (tiered)

> Markets where tire specialists capture more than cars on the road explain and are gaining share faster than vehicle growth. Dealers may be among those losing share; confirming this needs dealer-level tire sales.

| County | Tier | Reason | Largest single source of real growth 2019→2025 |
|---|---|---|---|
| Kittitas | Watch (capped) | Flagged under both dealer measures. Capped at Watch: Cle Elum accounts for 182% of real tire-specialist sales growth (more than all of it; the rest of the county fell). | Cle Elum, 182% |
| Asotin | Watch | Flagged under dealer sales only; it cannot be assessed under CBP dealer employment because CBP publishes no data for it. Also concentrated: Clarkston accounts for 95% of real tire-specialist sales growth. | Clarkston, 95% |

- **Robust** = top candidate under both dealer measures, and no single city accounts for more than 50% of the county's real tire-specialist growth 2019→2025. **Watch** = top candidate under one measure only, or capped by the concentration rule. The two views are not weighted equally.
- **Concentration cap:** if one city accounts for more than 50% of a county's real tire-specialist growth, the county is capped at Watch and the reason names the city and its share. The cap is not applied when that city's data is hidden ("D") in 2019 or 2025, and the reason says so. Cle Elum and Clarkston are disclosed in every quarter of both years, so the cap applies.
- Generated in `data/processed/candidate_tiers.csv`.

### City-level breakdown (flagged counties)

Real tire-specialist sales (2025 dollars), disclosed cells only. "Hidden quarters" counts quarters in which a city's cell was suppressed. Full table: `data/processed/city_breakdown.csv`.

| County | City | 2019 | 2025 | Change | Share of county change | Hidden quarters 2019 / 2025 |
|---|---|---|---|---|---|---|
| Kittitas | Cle Elum | $0.05M | $3.99M | +$3.94M | 182% | 0 / 0 |
| Kittitas | Kittitas City | $0 | $0.03M | +$0.03M | 2% | 2 / 1 |
| Kittitas | Roslyn | $0.01M | $0.01M | +$0.004M | 0% | 2 / 3 |
| Kittitas | South Cle Elum | $0.003M | $0 | −$0.003M | 0% | 1 / 3 |
| Kittitas | Unincorporated | $0.91M | $0.63M | −$0.28M | −13% | 0 / 0 |
| Kittitas | Ellensburg | $14.81M | $13.28M | −$1.53M | −71% | 0 / 0 |
| Asotin | Clarkston | $4.45M | $5.15M | +$0.70M | 95% | 0 / 0 |
| Asotin | Asotin City | $0 | $0.03M | +$0.03M | 4% | 4 / 1 |
| Asotin | Unincorporated | $0.18M | $0.19M | +$0.004M | 1% | 0 / 0 |

- **Kittitas:** Cle Elum's tire-specialist sales went from about $20k to about $900k a quarter starting 2024Q2, with the same 5–8 taxpayers. That points to one business opening, expanding, being reclassified or changing where it reports sales. Ellensburg, the county's main market, fell 10% in real terms. Each hidden quarter in the small towns holds at most 2 taxpayers, so they are unlikely to change the picture (inference: their dollar amounts are unknown).
- **Kittitas's CBP residual** is 1.06× typical error, just over the 1× threshold.

### Signals by view

The growth gap is the same in both views: real tire-specialist growth minus registered-vehicle growth, 2019→2025, net of the view's county trend. Dealer activity enters only the level model, so the views differ in their residuals and in which counties they cover. All 39 counties have vehicle data for 2019 and 2025; none were imputed.

| County | View | Test years above expected | Residual (recent) | Residual ÷ typical error | Real tire-specialist growth 2019→25 | Vehicle growth 2019→25 | Relative gap (log) | Growth rank | Top candidate |
|---|---|---|---|---|---|---|---|---|---|
| **Kittitas** | CBP (20 counties) | 2 of 2 | +12% | 1.06× | +14% | −0.4% | +0.11 | 3 of 20 | **yes** |
| **Kittitas** | Sales (29 counties) | 4 of 4 | +50% | 2.3× | +14% | −0.4% | +0.11 | 6 of 29 | **yes** |
| Asotin | Sales (29 counties) | 4 of 4 | +121% | 4.5× | +16% | −5% | +0.17 | 3 of 29 | yes |
| Grant | both | all | +30% / +50% | 2.4× / 2.3× | +9% | +5% | +0.01 | 9 of 20 / 16 of 29 | no: tire specialists grew about as fast as vehicles |
| Jefferson | Sales | 4 of 4 | +67% | 2.9× | +3% | −4% | +0.04 | 13 of 29 | no: gap outside the top quartile |

Plausible explanations other than dealer loss are listed as **hypotheses** in notebook section 6: Kittitas's I-90 corridor and the Cle Elum step change; Asotin's cross-border Lewiston–Clarkston market.

Full rankings: `data/processed/signals_cbp_emp.csv`, `signals_sales.csv`, `candidates_by_view.csv`. Notebook: `notebooks/wa_tire_opportunity.ipynb`.

## Other findings

In the CBP model, dealer employment adds little once vehicles are included: its coefficient is 0.15 (p = 0.30), against 0.65 for vehicles (p < 0.001). In this data, tire-specialist sales track cars on the road more than dealer presence. This is an observation from 20 Washington counties over 2017–2023, not a general conclusion.

## How the signal definition changed

The tiers moved twice since commit `0189d21`, which flagged Grant (Robust) and Kittitas and Jefferson (Watch). The residual flag never changed; all four counties pass it wherever they are assessed. Both moves came from the growth flag and the new cap:
1. **Growth gap base: dealer activity → registered vehicles.** The CBP view's window also moved from 2019→2023 to 2019→2025.
   - **Grant** drops: its old gap came from falling dealer activity, and its tire-specialist growth (+9%) roughly matches its vehicle growth (+5%).
   - **Jefferson** drops: +3% tire-specialist growth against a −4% fleet ranks only 13th of 29.
   - **Kittitas** passes under CBP: its growth arrives in 2024–25, after the old 2023 cut-off.
   - **Asotin** enters: its dealer sales rose, which made the old gap negative, but its tire specialists grew 16% while its fleet shrank 5%.
2. **Concentration cap (> 50% from one city).** This moves Kittitas from Robust to Watch.

Full before/after table with every rule, per county and view: `reports/signal_definition_change.md`.

## Data sources

| Data | Source | Coverage |
|---|---|---|
| **Target:** WA taxable retail sales, tire dealers (NAICS 441320 → 441340): sales captured by tire-specialist retailers (independent shops + tire chains) | [WA DOR Taxable Retail Sales builder](https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal/Report.aspx) | County × quarter; available 2005–2026Q1; 2017–2025 used because vehicle registrations start in 2017 (pulled from 2015Q1 for charts) |
| Dealer sales: WA taxable retail sales, new-car dealers (NAICS 441110) | Same builder | County × quarter, 2015Q1–2026Q1 |
| New-car dealer employment, NAICS 441110 | [Census County Business Patterns API](https://api.census.gov/data/2023/cbp) (`CENSUS_API_KEY`) | 22–24 WA counties published per year, 2017–2023 (2024 not yet released) |
| Cars on the road: vehicle registrations (Passenger Vehicle + Truck, by owner's county) | [WA DOL via data.wa.gov `hmzg-s6q4`](https://data.wa.gov/resource/hmzg-s6q4.json) | 39 counties, 2017–2025 |
| CPI-U Tires `CUUR0000SETC01`; New vehicles `CUUR0000SETA01` | [BLS API](https://api.bls.gov/publicAPI/v1/timeseries/data/) | 2015–2026, U.S. city average |

DOR reports cities and unincorporated areas; these are summed to counties using the rule in `reports/location_codes.md`.

## Method

1. **Build.**
   - County × quarter disclosed sales, plus a count of hidden ("D") cells.
   - Deflated to 2025 dollars; aggregated to county × year.
   - 10 counties are excluded from all views for tire-specialist data suppression.
   - Each view also drops counties missing its dealer measure in any model year.
   - No jump at the 2022 NAICS switch.
2. **Baseline:** real tire-specialist sales per registered vehicle × county vehicles.
3. **Model (level):** OLS of log real tire-specialist sales on log vehicles + log dealer activity + year effects, with standard errors clustered by county. This is the only place dealer activity is used.
   - CBP view: vehicles 0.65 (p < 0.001), dealer employment 0.15 (p = 0.30, not significant).
   - Sales view: vehicles 0.40, dealer sales 0.35.
4. **Split:** train 2017–2021; test 2022 to the last year of each view. Both methods are calibrated each year to the actual total of the counties in the view.
5. **Signals**, from out-of-sample test predictions:
   - **Residual flag:** above expected in every recent test year, and the mean recent log residual is more than 1× typical error. Typical error is the median absolute test log error: 0.11 in the CBP view, 0.18 in the sales view.
   - **Growth flag:** top quartile on the relative growth gap, with the gap > 0 and real tire-specialist growth > 0. The relative gap is (county − state tire-specialist growth) − (county − state registered-vehicle growth), 2019→2025. It ranks counties exactly like the raw gap; only the zero line moves. Counties missing 2019 or 2025 data would be reported, not imputed; none are.
   - **Top candidate:** both flags.
6. **Tiers:** Robust = top candidate in both views; Watch = one view only. Any county where one city accounts for more than 50% of real tire-specialist growth 2019→2025 is capped at Watch, unless that city's data is hidden in 2019 or 2025.

## Evaluation (test years)

| View | Test years | County-years | Baseline MAPE | Model MAPE | Baseline MALE | Model MALE |
|---|---|---|---|---|---|---|
| CBP employment (primary) | 2022–2023 | 40 | 20.7% | 13.7% | 0.237 | 0.132 |
| Dealer sales (secondary) | 2022–2025 | 116 | 77.4% | 43.5% | 0.358 | 0.305 |

The views cover different counties: CBP excludes the smallest, noisiest counties. Their errors are therefore not directly comparable.

## Key caveats (full list with impacts: `CAVEATS.md`)

- The target includes large tire chains (e.g. Les Schwab, Discount Tire), not only independent shops.
- Big-box stores (warehouse clubs, supercenters), general auto-repair chains and online sellers sell tires but are classified elsewhere; they are not in the target.
- Dealer tire sales are not observable, so dealer tire share cannot be measured. Tire-specialist share gains may come from dealers, big-box or online sellers.
- The growth gap assumes tire spending per vehicle is roughly stable across counties over time.
- Taxable retail sales only; tax-exempt sales (e.g. for resale) are excluded. Hidden cells make county totals lower bounds.
- One city can drive a county's signal (Kittitas: Cle Elum 182% of real growth; Asotin: Clarkston 95%). Counties above 50% are capped at Watch.
- One state; 20 (CBP) or 29 (sales) counties modelled; small samples. CBP ends in 2023, so the primary view's level model has only 2 test years.
- **Results are candidates, not proof.**

## With company data

With a company's dealer-level data, this becomes a **dealer-level target list**:
- Each dealership's tire and service revenue and its customer addresses replace the county proxies.
- Dealers that under-capture tire demand relative to their vehicles sold or serviced, and relative to tire-specialist sales in their area, are ranked as targets.

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
- `tests/`: 6 focused tests (code combining, no double counting, non-negative sales, error-scaled residual, growth gap vs vehicles, concentration cap).
- `reports/`: state data check, location-code rule, signal-definition change, pipeline summary.
