# Walkthrough - Programmatic Ingest & ETL Execution Verify

All tasks have been successfully completed! Below is a summary of the accomplishments and verification metrics.

## Changes Made

### Ingestion Component
*   **[src/ingest.py](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/src/ingest.py)**: Rewrote the file to dynamically initiate and download the 5 target HDB resale datasets using the `api-open.data.gov.sg` public API:
    - Automatically skips files that are already downloaded locally.
    - Adds a `time.sleep(3)` delay between requests to bypass `429 Too Many Requests` API limits.
    - Successfully downloaded all 5 HDB datasets into the `data/input/` directory.

### Pipeline Revert
*   **[main.py](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/main.py)**: Reverted to the repository version importing `run_pipeline` from `src.pipeline` instead of importing from non-existent modules.

---

## Verification Results

### 1. Ingestion Output
All 5 datasets downloaded successfully to `data/input/`:
*   `d_ebc5ab87086db484f88045b47411ebc5.csv` (1990 - 1999)
*   `d_ea9ed51da2787afaf8e51f827c304208.csv` (2000 - Feb 2012)
*   `d_43f493c6c50d54243cc1eab0df142d6a.csv` (Mar 2012 - Dec 2014)
*   `d_2d5ff9ea31397b66239f245f57751537.csv` (Jan 2015 - Dec 2016)
*   `d_8b84c4ee58e3cfc0ece0d773c8ca6abc.csv` (Jan 2017 - Present)

### 2. ETL Processing Output
The execution of the main script (`hdb-etl-env/bin/python3 main.py`) processed all files and successfully created the following outputs:
*   **Raw Master Table:** [raw_master.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/data/raw/raw_master.csv) (~125 MB)
*   **Cleaned Table:** [cleaned_data.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/data/cleaned/cleaned_data.csv) (~121 MB)
*   **Transformed Table:** [transformed_data.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/data/transformed/transformed_data.csv) (~130 MB)
*   **Hashed Table:** [hashed_cleaned_data.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/data/hashed/hashed_cleaned_data.csv) (~192 MB)
*   **Failed Records:** [failed_data.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/data/failed/failed_data.csv) (~3.8 MB)

### 3. Profiling Data Reports
The pipeline successfully output the following profiling statistics to `output/profiling/`:
*   [raw_profile.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/output/profiling/raw_profile.csv)
*   [cleaned_profile.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/output/profiling/cleaned_profile.csv)
*   [transformed_profile.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/output/profiling/transformed_profile.csv)
*   [hashed_profile.csv](file:///Users/sathiya/Data-Engineering/hdb-resale-etl/output/profiling/hashed_profile.csv)
