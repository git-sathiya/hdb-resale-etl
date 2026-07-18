from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = BASE_DIR / "data" / "input"
RAW_DIR = BASE_DIR / "data" / "raw"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
TRANSFORMED_DIR = BASE_DIR / "data" / "transformed"
FAILED_DIR = BASE_DIR / "data" / "failed"
HASHED_DIR = BASE_DIR / "data" / "hashed"
PROFILE_DIR = BASE_DIR / "output" / "profiling"
LOG_DIR = BASE_DIR / "output" / "logs"

for d in [RAW_DIR, CLEANED_DIR, TRANSFORMED_DIR, FAILED_DIR, HASHED_DIR, PROFILE_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DATE_COL = "month"
TOWN_COL = "town"
FLAT_TYPE_COL = "flat_type"
FLAT_MODEL_COL = "flat_model"
STOREY_COL = "storey_range"
BLOCK_COL = "block"
PRICE_COL = "resale_price"
LEASE_COL = "remaining_lease"
