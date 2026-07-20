# HDB Resale ETL Pipeline (Local → AWS S3 Migration)

All tasks have been successfully completed across two phases:
1. **Phase 1 – Local ETL**: Programmatic data ingestion and pipeline execution on local disk.
2. **Phase 2 – AWS Migration**: Full migration to AWS S3 as a configurable storage backend.

---

## Phase 1 — Local ETL (Baseline)

### Ingestion Component
- **[src/ingest.py](src/ingest.py)**: Downloads 5 HDB resale datasets from the `api-open.data.gov.sg` public API.
  - Skips files already downloaded locally.
  - `time.sleep(3)` delay between requests avoids `429 Too Many Requests` rate limits.
  - Uses absolute path resolution (`Path(__file__).resolve()`) so the script works from any working directory.

### ETL Pipeline (`main.py` → `src/pipeline.py`)
Steps executed in sequence:

| Step | Script | Output |
|---|---|---|
| Load all CSVs | `data_loader.py` | Combined DataFrame (982,011 rows) |
| Validate | `validation.py` | 980,780 valid · 1,231 failed |
| Compute remaining lease | `transformations.py` | Added `remaining_lease` column |
| De-duplicate | `transformations.py` | Kept highest-priced record per key |
| Create resale identifier | `transformations.py` | Added `resale_identifier` column |
| Hash identifiers | `hashing.py` | Added `hashed_identifier` (SHA-256) |
| Profile reports | `profiling.py` | Column-level stats at each stage |

### Local Verification Results
All 5 datasets successfully downloaded to `data/input/`:
- `d_ebc5ab87086db484f88045b47411ebc5.csv` — 1990–1999
- `d_ea9ed51da2787afaf8e51f827c304208.csv` — 2000–Feb 2012
- `d_43f493c6c50d54243cc1eab0df142d6a.csv` — Mar 2012–Dec 2014
- `d_2d5ff9ea31397b66239f245f57751537.csv` — Jan 2015–Dec 2016
- `d_8b84c4ee58e3cfc0ece0d773c8ca6abc.csv` — Jan 2017–Present

---

## Phase 2 — AWS S3 Migration

### Architecture

![AWS Architecture Data Pipeline](Images%20-%20Run_Audits/Part_2-AWS%20Architecture%20Data%20Pipeline.png)

```
data.gov.sg API
      │  HTTP download (requests)
      ▼
Local temp file  ──boto3.upload_file──▶  S3: hdb-resale/input/*.csv
                                                    │
                                    boto3.get_object (stream to BytesIO)
                                                    │
                                             Pandas ETL pipeline
                                                    │
                                         boto3.put_object (CSV bytes)
                                                    │
                              ┌─────────────────────┼──────────────────────┐
                              ▼                     ▼                      ▼
                     S3: hdb-resale/raw/   S3: hdb-resale/cleaned/   S3: hdb-resale/failed/
                     S3: hdb-resale/transformed/   S3: hdb-resale/hashed/
                     S3: hdb-resale/profiling/
```

### AWS Resources Created

| Resource | Details |
|---|---|
| **S3 Bucket** | `hdb-resale-etl-523947005862` |
| **Region** | `ap-south-1` (Mumbai) |
| **AWS Profile** | `iceberg-demo` (SSO via `d-9f6754cd71.awsapps.com`) |

### Files Modified for AWS Support

#### [src/config.py](src/config.py)
- Reads `STORAGE_TYPE`, `S3_BUCKET`, `S3_PREFIX`, `AWS_PROFILE` from environment variables.
- `_make_path(relative)` — returns a local `Path` or `s3://` URI based on `STORAGE_TYPE`.
  - S3 URIs strip `data/` and `output/` prefixes so bucket layout stays flat under the prefix.
- `join_path(base, filename)` — safely concatenates both `Path` objects and `s3://` URI strings.
- Local `mkdir()` calls skipped when running in S3 mode.

#### [src/ingest.py](src/ingest.py)
- **S3 mode**: Checks if CSV key already exists in S3 → downloads to temp file → uploads via `boto3.upload_file` → deletes temp file.
- **Local mode**: Original download-to-disk logic preserved.

#### [src/data_loader.py](src/data_loader.py)
- **S3 mode**: Lists keys with `boto3.list_objects_v2`, reads each CSV via `boto3.get_object` streamed into `io.BytesIO` → `pd.read_csv`.
- **Local mode**: Original `Path.glob("*.csv")` logic preserved.
- No `s3fs` dependency — avoids the `aiobotocore` / `botocore` version conflict.

#### [src/pipeline.py](src/pipeline.py)
- All path concatenation uses `join_path()` helper.
- `_save_csv(df, path)` — uses `boto3.put_object` for S3 destinations, `df.to_csv()` for local.
- Progress print statements added for visibility during long S3 runs.

#### [src/profiling.py](src/profiling.py)
- `_write_csv(df, path)` — uses `boto3.put_object` to write profiling CSVs to S3.
- Accepts `Union[Path, str]` for `output_path`.

#### [requirements.txt](requirements.txt)
- Added `boto3` (the only AWS dependency — `s3fs` was intentionally excluded).

#### [.env](/.env) *(git-ignored)*
- Pre-filled with S3 bucket, prefix, SSO profile, and region for one-command S3 activation.

---

## AWS S3 Pipeline Run Results (2026-07-19)

```
Loading input data…
  Loading s3://hdb-resale-etl-523947005862/hdb-resale/input/d_2d5ff9... ✓
  Loading s3://hdb-resale-etl-523947005862/hdb-resale/input/d_43f493... ✓
  Loading s3://hdb-resale-etl-523947005862/hdb-resale/input/d_8b84c4... ✓
  Loading s3://hdb-resale-etl-523947005862/hdb-resale/input/d_ea9ed5... ✓
  Loading s3://hdb-resale-etl-523947005862/hdb-resale/input/d_ebc5ab... ✓
  Loaded 982,011 rows from 5 files.
Validating data…   → Valid: 980,780  |  Failed: 1,231
Transforming data… → cleaned_data.csv, failed_data.csv written to S3
Creating identifiers and hashing… → transformed + hashed CSVs written to S3
Pipeline complete ✓
```

### S3 Bucket Output Structure
```
s3://hdb-resale-etl-523947005862/
└── hdb-resale/
    ├── input/           (78.7 MiB)  ← 5 raw HDB CSVs from data.gov.sg
    ├── raw/             (119.3 MiB) ← raw_master.csv (all 982,011 rows)
    ├── cleaned/         (115.7 MiB) ← cleaned_data.csv (980,780 rows)
    ├── transformed/     (124.8 MiB) ← with resale_identifier column
    ├── hashed/          (183.7 MiB) ← with SHA-256 hashed_identifier
    ├── failed/          (3.7 MiB)   ← rejected / anomaly records
    └── profiling/                   ← raw, cleaned, transformed, hashed profiles
```

---

## Phase 3 — AWS Data Catalog & Athena Integration

To make S3 outputs queryable, we configure a **Glue Data Catalog Database** and define **Athena External Tables** directly mapping each storage path.

### Schema Configuration Script
- **[aws_setup_athena.py](aws_setup_athena.py)**: Auto-provisions the Glue Database (`hdb_resale_db`) and creates tables using Hive DDL (with OpenCSV SerDe for CSV processing). Bypasses Glue Crawler service restrictions for robustness.

### Data Catalog & Query Verification (2026-07-19)
The tables were successfully registered and verified via programmatic SQL queries executed on Athena:

```
Database: hdb_resale_db
Tables Registered: raw, cleaned, transformed, hashed, failed

Dataset Row Counts (Verified via Athena SQL):
  - total_raw_rows:         982,011
  - total_cleaned_rows:     951,468
  - total_transformed_rows: 951,468
  - total_hashed_rows:      951,468
  - total_failed_rows:       30,543
```

A sample query verifying the final hashed identifier returns correctly aligned values:
```
month:             1990-01
town:              ANG MO KIO
flat_type:         1 ROOM
resale_price:      9000.0
resale_identifier: S3097001A
hashed_identifier: c8f96282cefd12811cf41a908da692d5d87f8e19598f53e66d5a045021959a3b
```

---

## How to Run

### Local Mode (default, no AWS needed)
```bash
python main.py
```

### S3 Mode
```bash
# Option A: load from .env file
export $(grep -v '^#' .env | xargs)
python main.py

# Option B: inline env vars
STORAGE_TYPE=s3 \
S3_BUCKET=hdb-resale-etl-523947005862 \
S3_PREFIX=hdb-resale \
AWS_PROFILE=iceberg-demo \
AWS_DEFAULT_REGION=ap-south-1 \
python main.py
```

### Re-ingest from data.gov.sg directly to S3
```bash
export $(grep -v '^#' .env | xargs)
python src/ingest.py
```

### Provision Glue Data Catalog Database, Tables & Run Athena Verification
```bash
export $(grep -v '^#' .env | xargs)
python aws_setup_athena.py
```

