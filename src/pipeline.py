import io
import pandas as pd
from pathlib import Path
from typing import Union

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
    FAILED_DIR, HASHED_DIR, PROFILE_DIR, join_path
)


def _save_csv(df: pd.DataFrame, path: Union[Path, str]):
    """Write *df* as CSV to a local path or an s3:// URI via boto3."""
    if isinstance(path, str) and path.startswith("s3://"):
        import boto3
        without_scheme = path[len("s3://"):]
        bucket, _, key = without_scheme.partition("/")
        print(f"  Writing → s3://{bucket}/{key}")
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        boto3.client("s3").put_object(
            Bucket=bucket,
            Key=key,
            Body=buf.getvalue().encode("utf-8"),
            ContentType="text/csv",
        )
    else:
        df.to_csv(path, index=False)


def run_pipeline():
    # -----------------------------------------------------------------------
    # Ingest
    # -----------------------------------------------------------------------
    print("Loading input data…")
    raw = load_all_csv(INPUT_DIR)
    print(f"  Loaded {len(raw):,} rows from {raw['source_file'].nunique()} files.")

    _save_csv(raw, join_path(RAW_DIR, "raw_master.csv"))
    profile_dataframe(raw, join_path(PROFILE_DIR, "raw_profile.csv"))

    # -----------------------------------------------------------------------
    # Validate
    # -----------------------------------------------------------------------
    print("Validating data…")
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
    print(f"  Valid: {len(cleaned):,}  |  Failed: {len(failed_validation):,}")

    # -----------------------------------------------------------------------
    # Transform
    # -----------------------------------------------------------------------
    print("Transforming data…")
    cleaned = compute_remaining_lease(cleaned)
    cleaned, failed_duplicates = remove_duplicates_keep_highest(cleaned)

    failed = pd.concat([failed_validation, failed_duplicates], ignore_index=True, sort=False)

    _save_csv(cleaned, join_path(CLEANED_DIR, "cleaned_data.csv"))
    _save_csv(failed,  join_path(FAILED_DIR,  "failed_data.csv"))
    profile_dataframe(cleaned, join_path(PROFILE_DIR, "cleaned_profile.csv"))

    # -----------------------------------------------------------------------
    # Create identifiers & hash
    # -----------------------------------------------------------------------
    print("Creating identifiers and hashing…")
    transformed = create_resale_identifier(cleaned)
    transformed = transformed.drop(
        columns=["month_dt", "year_month", "block_digits", "block_digits3"],
        errors="ignore"
    )
    transformed = transformed.sort_values(["town", "flat_type", "month"])
    _save_csv(transformed, join_path(TRANSFORMED_DIR, "transformed_data.csv"))

    hashed = hash_identifier(transformed)
    _save_csv(hashed, join_path(HASHED_DIR, "hashed_cleaned_data.csv"))

    profile_dataframe(transformed, join_path(PROFILE_DIR, "transformed_profile.csv"))
    profile_dataframe(hashed,      join_path(PROFILE_DIR, "hashed_profile.csv"))

    print("Pipeline complete ✓")
    return raw, cleaned, transformed, failed, hashed
