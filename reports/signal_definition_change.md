# How the signal definition changed

Why the candidate tiers moved between commit `0189d21`, which flagged Grant (Robust) and Kittitas and Jefferson (Watch), and the current results. Values come from `data/processed/signals_*.csv` at `0189d21` and at the current commit.

## What changed

| | `0189d21` (old) | Current |
|---|---|---|
| Level model and residual flag | Out-of-sample, error-scaled; above expected in all recent test years and > 1× typical error | **Unchanged** |
| Growth gap comparison base | Dealer activity: CBP employment or dealer taxable sales | **Registered vehicles** (cars on the road) |
| Growth window, CBP view | 2019→2023 (CBP's last year) | **2019→2025** (registrations do not depend on CBP) |
| Growth window, sales view | 2019→2025 | 2019→2025 |
| Growth flag | Top quartile on relative gap, gap > 0, tire growth > 0 | Same rule, on the new gap |
| Concentration cap | None | **Capped at Watch if one city accounts for > 50% of real tire-specialist growth**, unless that city's data is hidden |

**Every change in the candidate list comes from the growth flag.** All four counties pass the residual flag in every view where they are assessed, in both commits.

## The four counties

Log growth values; relative gap = (county − view's trend) for tire specialists minus the same for the comparison base. Growth rank is out of 20 (CBP) or 29 (sales); the growth flag needs the top 5 / top 8.

### CBP dealer employment view (20 counties)

| County | Residual | Scaled residual | Residual flag | Old: tire growth 2019→23 | Old: dealer-employment growth | Old: relative gap (rank) | Old growth flag | New: tire growth 2019→25 | New: vehicle growth | New: relative gap (rank) | New growth flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Grant | +30% | 2.37× | pass | +0.110 | −0.170 | +0.171 (5) | **pass** | +0.085 | +0.049 | +0.013 (9) | **fail**: not top 5 |
| Kittitas | +12% | 1.06× | pass | −0.014 | +0.144 | −0.268 (19) | **fail**: tire growth ≤ 0, gap < 0 | +0.128 | −0.004 | +0.109 (3) | **pass** |
| Jefferson | – | – | – | – | – | – | not assessable (no CBP data) | – | – | – | not assessable |
| Asotin | – | – | – | – | – | – | not assessable (no CBP data) | – | – | – | not assessable |

### Dealer taxable sales view (29 counties)

| County | Residual | Scaled residual | Residual flag | Old: tire growth 2019→25 | Old: dealer-sales growth | Old: relative gap (rank) | Old growth flag | New: vehicle growth | New: relative gap (rank) | New growth flag |
|---|---|---|---|---|---|---|---|---|---|---|
| Grant | +50% | 2.29× | pass | +0.085 | −0.096 | +0.192 (8) | **pass** | +0.049 | +0.010 (16) | **fail**: not top 8 |
| Kittitas | +50% | 2.30× | pass | +0.128 | −0.332 | +0.472 (5) | **pass** | −0.004 | +0.107 (6) | **pass** |
| Jefferson | +67% | 2.93× | pass | +0.026 | −0.257 | +0.295 (6) | **pass** | −0.038 | +0.038 (13) | **fail**: not top 8 |
| Asotin | +121% | 4.52× | pass | +0.147 | +0.180 | −0.021 (20) | **fail**: gap < 0 | −0.048 | +0.169 (3) | **pass** |

Tire-specialist growth over 2019→2025 is the same in both commits. Only the comparison base, and the CBP view's window, changed.

## County by county

- **Grant: Robust → dropped.** Its old gap came from falling dealer activity: dealer employment −16%, dealer sales −9%. Against its growing vehicle fleet (+5%), tire-specialist growth (+9%) is about average.
- **Kittitas: Watch → Robust → Watch.** Under CBP, the old window ended in 2023, before its tire-specialist growth, which arrives in 2024–25. Against vehicles over 2019→2025 it passes in both views, so it became Robust. The concentration cap then moves it back to Watch: Cle Elum alone accounts for 182% of the county's real tire-specialist growth, because the rest of the county fell.
- **Jefferson: Watch → dropped.** Its old gap came from dealer sales falling 23%. Its tire-specialist growth (+3%) only slightly beats a shrinking fleet (−4%), which ranks 13th of 29.
- **Asotin: not flagged → Watch.** Its dealer sales rose (+20%), so the old gap was negative. Against a shrinking fleet (−5%), its tire-specialist growth (+16%) ranks 3rd. Clarkston accounts for 95% of the growth, so it would be capped anyway. It cannot be assessed under CBP.
