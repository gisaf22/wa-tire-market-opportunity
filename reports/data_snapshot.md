# Data snapshot

Raw pulls live in `data/raw/` (git-ignored). Dates are the cached files' modification times, i.e. when each source was last pulled. All v1 results (`v1-county-baseline`) and v1.1 rigour checks use this snapshot; `run_pipeline.py` without `--refresh` reuses it.

| Source | Cached file(s) | Pulled | Coverage in snapshot |
|---|---|---|---|
| WA DOR Taxable Retail Sales, tire dealers (441320/441340) and new-car dealers (441110) | `wa_dor_cache/*.csv` (39 counties), `wa_dor_trs_jurisdiction.csv`, `wa_dor_locations.csv` | 2026-10-12 | 2015Q1–2026Q1 |
| WA DOL vehicle registrations (data.wa.gov `hmzg-s6q4`) | `wa_dol_registrations.csv` | 2026-10-12 | 2017–2025, 39 counties |
| BLS CPI-U Tires `CUUR0000SETC01`, New vehicles `CUUR0000SETA01` | `bls_cpi.csv` | 2026-10-12 | 2015–2026 |
| Census CBP, NAICS 441110 employment | `census_cbp_441110.csv` | 2026-10-12 | 2017–2023 (2024 not released at pull) |

`wa_dor_trs_tire_sample_*.csv` (2026-10-12) are from the earlier sample script and are not used by the pipeline.
