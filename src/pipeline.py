import pandas as pd
from pathlib import Path

from .data_loader import load_all_csv
from .profiling import profile_dataframe
from .validation import (
    validate_date, validate_town, validate_flat_type,
    validate_flat_model, validate_storey_range, validate_price,
    detect_price_anomalies
)
from .transformations import (
    compute_remaining_lease, create_resale_identifier,
    remove_duplicates_keep_highest
)
from .hashing import hash_identifier
from .config import (
    INPUT_DIR, RAW_DIR, CLEANED_DIR, TRANSFORMED_DIR,
    FAILED_DIR, HASHED_DIR, PROFILE_DIR
)

def run_pipeline():
    raw = load_all_csv(INPUT_DIR)
    raw.to_csv(RAW_DIR / "raw_master.csv", index=False)
    profile_dataframe(raw, PROFILE_DIR / "raw_profile.csv")

    valid_mask = (
        validate_date(raw) &
        validate_town(raw) &
        validate_flat_type(raw) &
        validate_flat_model(raw) &
        validate_storey_range(raw) &
        validate_price(raw) &
        ~detect_price_anomalies(raw)
    )

    cleaned = raw.loc[valid_mask].copy()
    failed_validation = raw.loc[~valid_mask].copy()

    cleaned = compute_remaining_lease(cleaned)

    cleaned, failed_duplicates = remove_duplicates_keep_highest(cleaned)

    failed = pd.concat([failed_validation, failed_duplicates], ignore_index=True, sort=False)

    cleaned.to_csv(CLEANED_DIR / "cleaned_data.csv", index=False)
    failed.to_csv(FAILED_DIR / "failed_data.csv", index=False)
    profile_dataframe(cleaned, PROFILE_DIR / "cleaned_profile.csv")

    transformed = create_resale_identifier(cleaned)
    transformed = transformed.drop(columns=["month_dt", "year_month", "block_digits", "block_digits3"], errors="ignore")
    transformed = transformed.sort_values(["town", "flat_type", "month"])
    transformed.to_csv(TRANSFORMED_DIR / "transformed_data.csv", index=False)

    hashed = hash_identifier(transformed)
    hashed.to_csv(HASHED_DIR / "hashed_cleaned_data.csv", index=False)

    profile_dataframe(transformed, PROFILE_DIR / "transformed_profile.csv")
    profile_dataframe(hashed, PROFILE_DIR / "hashed_profile.csv")

    return raw, cleaned, transformed, failed, hashed
