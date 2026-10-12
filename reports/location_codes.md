# WA DOR location-code rule

How jurisdiction-level taxable retail sales from the DOR Taxable Retail Sales (local) builder are summed to counties without missing or double-counting anything. Implemented in `src/wa_tire/pull_wa.py` (`classify_location`); the full code list with the rule applied is in `reports/location_codes.csv`.

## Rule

Codes are `CCNN`: `CC` = county number 01–39 (alphabetical), `NN` = jurisdiction.

| Code pattern | Meaning | Count | Treatment |
|---|---|---|---|
| `CC00` | Unincorporated county area | 39 | **keep** |
| other `CCNN` | City or town (cities spanning counties are already split, e.g. 1702 "Auburn/King Only") | 286 | **keep** |
| label contains "PTBA" (e.g. 2727 Pierce County PTBA, 3434 Thurston PTBA) | Public transportation benefit area: a tax overlay on cities and unincorporated areas already counted | 12 | **drop** (would double count) |
| `CC99`: 3099 "Skamina County", 3499 "Thurston County", 3599 "Wahkiakum County", 3899 "Whitman County" | Not documented by DOR | 4 | **drop**: they hold no data (below) |

County total = sum of its `CC00` and city codes.

## Evidence (checked 2026-10-12)

1. **`CC99` codes are empty.** These queries return "That request does not appear to match any records":
   - all four codes, all two-digit NAICS (100000–999999), 2005Q1–2026Q1;
   - the same codes for NAICS 441110–441340, 2015Q1–2026Q1.

   A control query on 3400 (Unincorporated Thurston) with the same parameters returns data.
2. **Jurisdiction sums match DOR's own county totals.** QBR Tables 3 and 4 give county totals for NAICS 441 (Motor Vehicles & Parts), 2025Q4. Summing the kept codes at three-digit NAICS gives:

   | County | Sum of kept codes | QBR county total | Ratio | Hidden cells |
   |---|---|---|---|---|
   | Skamania (30) | $718,747 | $718,747 | 1.0000 | 0 |
   | Whitman (38) | $16,960,212 | $16,960,917 | 1.0000 | 1 |
   | Thurston (34) | $189,380,053 | $191,123,596 | 0.9909 | 0 |

   No county sums *above* its official total, so nothing is double counted. Thurston's 0.9% shortfall has no hidden cells to explain it and is **unexplained**. It may be amounts DOR assigns at county level only. It is small and is listed in CAVEATS.md.
3. **Name matching.** Results label each table by name, not code, and the names differ from the form's (e.g. "Spokane City" vs "Spokane (City)"). The form also contains a typo: 3305 "Nothport" vs "Northport" in results. Matching normalises names, falls back to the closest name within the same county, and fails loudly if nothing is close.
