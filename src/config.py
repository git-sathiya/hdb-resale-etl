import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Storage backend selection
# ---------------------------------------------------------------------------
# Set STORAGE_TYPE=s3 to read/write all pipeline data from/to AWS S3.
# Default is "local" which preserves the original on-disk behaviour.
STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "local").lower()

# S3 settings – only used when STORAGE_TYPE=s3
S3_BUCKET  = os.environ.get("S3_BUCKET", "")           # e.g. "hdb-resale-etl-523947005862"
S3_PREFIX  = os.environ.get("S3_PREFIX", "hdb-resale") # key prefix inside the bucket
AWS_PROFILE = os.environ.get("AWS_PROFILE", "")        # e.g. "iceberg-demo" (SSO profile)

# Propagate AWS_PROFILE to boto3 / s3fs automatically
if AWS_PROFILE:
    os.environ["AWS_PROFILE"] = AWS_PROFILE

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

def _make_path(relative: str):
    """Return a local Path or an s3:// URI string depending on STORAGE_TYPE.

    Local paths use the full relative segment (e.g. ``data/input``).
    S3 URIs strip the leading ``data/`` or ``output/`` segment so that the
    bucket layout stays flat under the prefix, e.g.:
        data/input      →  s3://<bucket>/<prefix>/input
        data/raw        →  s3://<bucket>/<prefix>/raw
        output/profiling →  s3://<bucket>/<prefix>/profiling
    """
    if STORAGE_TYPE == "s3":
        if not S3_BUCKET:
            raise EnvironmentError(
                "S3_BUCKET environment variable must be set when STORAGE_TYPE=s3"
            )
        # Strip leading data/ or output/ for a cleaner S3 key structure
        s3_relative = relative
        for strip_prefix in ("data/", "output/"):
            if s3_relative.startswith(strip_prefix):
                s3_relative = s3_relative[len(strip_prefix):]
                break
        return f"s3://{S3_BUCKET}/{S3_PREFIX}/{s3_relative}"
    return BASE_DIR / relative

def join_path(base, filename: str) -> str:
    """Concatenate a base path (local Path or s3 URI string) with a filename."""
    if isinstance(base, str) and base.startswith("s3://"):
        return f"{base.rstrip('/')}/{filename}"
    return str(Path(base) / filename)

# ---------------------------------------------------------------------------
# Pipeline directories / S3 prefixes
# ---------------------------------------------------------------------------
INPUT_DIR   = _make_path("data/input")
RAW_DIR     = _make_path("data/raw")
CLEANED_DIR = _make_path("data/cleaned")
TRANSFORMED_DIR = _make_path("data/transformed")
FAILED_DIR  = _make_path("data/failed")
HASHED_DIR  = _make_path("data/hashed")
PROFILE_DIR = _make_path("output/profiling")
LOG_DIR     = _make_path("output/logs")

# Create local directories only when running in local mode
if STORAGE_TYPE == "local":
    for d in [
        RAW_DIR, CLEANED_DIR, TRANSFORMED_DIR,
        FAILED_DIR, HASHED_DIR, PROFILE_DIR, LOG_DIR
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Column name constants (unchanged)
# ---------------------------------------------------------------------------
DATE_COL      = "month"
TOWN_COL      = "town"
FLAT_TYPE_COL = "flat_type"
FLAT_MODEL_COL = "flat_model"
STOREY_COL    = "storey_range"
BLOCK_COL     = "block"
PRICE_COL     = "resale_price"
LEASE_COL     = "remaining_lease"
