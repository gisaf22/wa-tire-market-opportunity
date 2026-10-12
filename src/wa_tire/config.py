"""Paths, codes, year ranges and thresholds. Everything tunable lives here."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

# WA DOR Taxable Retail Sales (local) builder.
DOR_BASE = "https://apps.dor.wa.gov/ResearchStats/Content/TaxableRetailSalesLocal"
DOR_TAX_TYPE = "45"  # retail sales tax (not use tax)
REQUEST_PAUSE_S = 1.5

# NAICS: tire dealers changed code with DOR's move to 2022 NAICS in 2022Q2.
TIRE_CODES = {"441320": ("2005Q1", "2022Q1"), "441340": ("2022Q2", None)}
NEWCAR_CODE = "441110"
SERIES = {"441320": "tire", "441340": "tire", "441110": "newcar"}
QUERY_CODE_RANGE = ("441110", "441340")  # one query covers all three codes

FIRST_QUARTER = "2015Q1"

# DOL registrations start January 2017, so modelling starts in 2017.
DOL_DATASET = "https://data.wa.gov/resource/hmzg-s6q4.json"
DOL_USE_CLASSES = ["Passenger Vehicle", "Truck"]
MODEL_FIRST_YEAR = 2017
TRAIN_YEARS = range(2017, 2022)  # 2017-2021
TEST_FIRST_YEAR = 2022           # 2022-last full year
GROWTH_BASE_YEAR = 2019
RECENT_YEARS_N = 3               # residual flag uses the last 3 test years (fewer if the view has fewer)

# Dealer activity measures ("views"), primary first. Primary: Census CBP new-car dealer employment
# (2017-2023; 2024 not yet released). Secondary: DOR new-car-dealer real taxable sales.
CBP_NAICS_VAR = "NAICS2017"  # 441110 is unchanged in NAICS 2022
DEALER_VIEWS = {
    "cbp_emp": {"col": "newcar_emp", "label": "New-car dealer employment (CBP)", "short": "CBP dealer employment"},
    "sales": {"col": "newcar_real", "label": "New-car dealer real taxable sales (DOR)", "short": "dealer sales"},
}

# BLS CPI-U, U.S. city average, not seasonally adjusted.
CPI_TIRES = "CUUR0000SETC01"         # Tires
CPI_NEW_VEHICLES = "CUUR0000SETA01"  # New vehicles (deflates new-car-dealer sales)
CPI_BASE_YEAR = 2025                 # constant 2025 dollars

# Suppression: a "D" cell hides 1-2 taxpayers (DOR rule: fewer than 3 firms).
MAX_HIDDEN_PER_CELL = 2
HIDDEN_QUARTER_SHARE = 0.25   # quarter counts as hidden if D cells could be >25% of taxpayers
MAX_HIDDEN_QUARTERS = 0.25    # exclude county if >25% of its quarters are hidden

QOQ_OUTLIER_LOG = 0.5         # flag |county QoQ log change - statewide QoQ log change| > 0.5
TOP_SHARE = 0.25              # growth flag: top quartile on relative growth gap
RESIDUAL_Z_MIN = 1.0          # residual flag: mean recent log residual > 1x typical (median abs) test log error
