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

---

## v1.1 rigour checks — results (2026-10-15)

Same snapshot and frozen v1 rules. Code: `src/wa_tire/rigour.py`, `scripts/run_rigour.py`; notebook `notebooks/01b_rigour.ipynb`. The rigour baseline reproduces v1 ranks and flags exactly.

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1 top-quartile residual in ≥80% of draws | **Not supported** | Kittitas: CBP 72%, sales 92%. Asotin: sales 96% |
| H2 flag independent of any single county | **Not supported** | Kittitas CBP flag removed by dropping Benton, King, Pierce, Snohomish or Walla Walla (residual flag). Kittitas and Asotin under sales: no single county changes them |
| H3 vehicles CI excludes 0, dealer CI includes 0 | **Not supported** | CBP (G=20): vehicles 0.65 [0.31, 0.99], dealer 0.15 [−0.15, 0.45], as expected. Sales (G=29): vehicles 0.40 [−0.04, 0.84], dealer 0.35 [0.01, 0.69], reversed |

**Bootstrap (2,000 draws; 90% intervals)**
- Kittitas, CBP view: median rank 4 [1, 9]; flagged as top candidate in 54% of draws. Recent log residual 0.11 [0.01, 0.21].
- Kittitas, sales view: median rank 5 [1, 9]; top candidate in 84% of draws. Log residual 0.38 [0.19, 0.61].
- Asotin, sales view: median rank 2 [1, 8]; top candidate in 91% of draws. Log residual 0.67 [0.12, 1.48].

**Tiers:** unchanged. Kittitas and Asotin stay Watch in every leave-one-out refit. If Kittitas loses its CBP flag, it becomes "sales view only", which is still Watch. The only tier-table change in any refit: Island enters as Watch (sales only) when Adams, Asotin or Klickitat is dropped.

**What changed in confidence**
- Kittitas's primary-view (CBP) flag is fragile. It rests on a residual just over the threshold (1.06×) and on which large counties set the typical error. Its sales-view flag is stable.
- Asotin's flag is stable within the one view that can assess it.
- v1 read the coefficients as "tire sales track vehicles, not dealers". That holds in the CBP view only. Under dealer sales with small-cluster CIs, vehicles and dealer activity are not cleanly separable. The README's "Other findings" sentence is scoped to the CBP model, so it stands.
- Results remain exploratory. v1.1 adds uncertainty measures; it does not validate the signal.

---

## State survey: local tire-dealer sales outside Washington (2026-10-15)

Surveyed 21 states (CA first, then CO, UT, MN, IA, OH, NC, VA, OK, AZ, MO, KS, NE, WI, ID, TN, FL, NY, GA, IL, MI). Test: tire dealers as a separate category (NAICS 44132/441320/441340), at county or city level, with at least 5 years of history. Details: `reports/state_survey.md`; checks: `scripts/survey/check_categories.py`.

- **No state passes.** The finest local detail found is NAICS 4413, which combines tires with parts and accessories (CA counties, NY), or FL kind code 24 (also combined). Most states publish only 3-digit 441, business groups, or no local industry split.
- **One unresolved lead:** Oklahoma's OkTAP "Tax Collections by NAICS" report, which may be city-level. Automated access hit a redirect loop, so it needs a manual browser check. It reports tax collected, not sales.
- WI, ID, IL and MI were not checked within the time box. Several fails are marked uncertain in the report.
- Implication: the analysis cannot be extended to other states with like-for-like tire-dealer sales from the states surveyed. Washington's 441320 local detail appears unusual.
