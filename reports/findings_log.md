# Findings log

Append-only. Each entry records what was decided or found, on which data, and when. Later entries do not edit earlier ones.

---

## v1 — county baseline (2026-10-15, tag `v1-county-baseline`, commit `d1e87e8`)

**Data** (snapshot details: `reports/data_snapshot.md`)
- WA DOR Taxable Retail Sales, tire dealers 441320→441340 and new-car dealers 441110, county × quarter 2015Q1–2026Q1; pulled 2026-10-12.
- WA DOL registrations (Passenger Vehicle + Truck), 2017–2025; pulled 2026-10-12.
- BLS CPI-U Tires and New vehicles, 2015–2026; pulled 2026-10-12.
- Census CBP 441110 employment, 2017–2023; pulled 2026-10-12.

**Model**
- OLS: log real tire-specialist sales ~ log vehicles + log dealer activity + year effects; SEs clustered by county. Train 2017–2021; test 2022 → last year of view. Predictions calibrated to each year's total.
- Two dealer-activity views: CBP employment (primary; 20 counties, test 2022–2023) and DOR dealer real sales (secondary; 29 counties, test 2022–2025). 10 counties excluded for tire-data suppression.
- Coefficients (train fit): CBP view vehicles 0.65 (p<0.001), dealer 0.15 (p=0.30). Sales view vehicles 0.40 (p=0.06), dealer 0.35 (p=0.035).

**Decision thresholds (frozen)**
- Residual flag: above expected in every recent test year (last ≤3) and mean recent log residual > 1.0 × median absolute test log error.
- Growth flag: top quartile on relative growth gap (tire vs registered-vehicle growth, 2019→2025), gap > 0, real tire growth > 0.
- Top candidate: both flags. Robust = top candidate in both views; Watch = one view.
- Concentration cap: Watch if one city > 50% of the county's real tire growth (unless that city is hidden in base/end year).

**Results**
- No Robust candidate.
- Kittitas: Watch (top candidate in both views; capped — Cle Elum 182% of growth). CBP residual 1.06× typical error, barely over threshold.
- Asotin: Watch (sales view only; not in CBP). Clarkston 95% of growth.

**Known limits**
- Rules refined post hoc on the same data → exploratory.
- Small samples (20 / 29 counties); CBP view has 2 test years.
- Target includes tire chains; big-box/online tire sales not observed; dealer tire sales not observed.
- Hidden cells make county totals lower bounds.
- No uncertainty quantification on ranks or flags (addressed in v1.1).

---

## v1.1 rigour checks — hypotheses (pre-registered 2026-10-15, before any v1.1 computation)

No new data; thresholds unchanged from v1. Coefficients and p-values in v1 were already seen, so H3 is a pre-stated expectation, not a blind test.

**Definitions fixed before running**
- Bootstrap: resample the view's counties with replacement (all years of a county move together), B = 2,000 draws, seed 20261015. Each draw: refit on train years, predict test years, recompute residual stats, growth gap, ranks and flags with v1 rules. A county drawn more than once is scored on its first copy; draws that do not include a county are not counted for it.
- "Top quartile of residuals": residual rank (by residual ÷ typical error, 1 = highest) ≤ ceil(0.25 × counties in the draw).
- H1 and H2 are evaluated in every view where the county is assessable (Kittitas: both; Asotin: sales only).
- Coefficient CIs: train-period fit, county-clustered SEs, t critical value with G − 1 degrees of freedom (G = clusters).

**Hypotheses**
- **H1:** Kittitas and Asotin are in the top quartile of residuals in ≥ 80% of bootstrap draws that include them.
- **H2:** Their v1 top-candidate flag does not depend on any single other county: it holds in every leave-one-county-out refit (each other county dropped once, from that view).
- **H3:** In each view, the vehicle coefficient's 95% CI excludes 0 and the dealer-activity coefficient's 95% CI includes 0.

**What would change the README:** a hypothesis failure is reported in this log and notebook 01b. The README summary changes only if a county's tier changes under the frozen rules, which v1.1 cannot do (same data, same rules); v1.1 changes confidence, not tiers.
