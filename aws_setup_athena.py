#!/usr/bin/env python3
"""
AWS Athena Setup & Verification Script
HDB Technical Test for Senior Data Engineer

This script programmatically configures the Glue Data Catalog and Athena components
by executing SQL DDL statements directly in Athena. This bypasses the Glue Crawler 
AccessDenied restriction on sandbox/restricted accounts, while registering all 
stages directly in the Glue Data Catalog.

Steps performed:
1. Create Glue Database (hdb_resale_db)
2. Create Athena External Tables mapping directly to S3 outputs:
   - raw
   - cleaned
   - transformed
   - hashed
   - failed
3. Run verification SQL queries in Athena (Step 4 of task list)
"""

import os
import sys
import time
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# Load environment configurations
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    print(f"Loading environment from {env_file}...")
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()

# Configuration variables
STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "s3").lower()
S3_BUCKET = os.environ.get("S3_BUCKET", "")
S3_PREFIX = os.environ.get("S3_PREFIX", "hdb-resale").rstrip("/")
AWS_PROFILE = os.environ.get("AWS_PROFILE", "")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")

if STORAGE_TYPE != "s3" or not S3_BUCKET:
    print("Error: STORAGE_TYPE must be set to 's3' and S3_BUCKET must be configured.")
    sys.exit(1)

# Establish session using configured profile
if AWS_PROFILE:
    print(f"Using AWS Profile: {AWS_PROFILE} in region {AWS_REGION}")
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
else:
    print(f"Using default credentials in region {AWS_REGION}")
    session = boto3.Session(region_name=AWS_REGION)

athena = session.client("athena")
glue = session.client("glue")

DATABASE_NAME = "hdb_resale_db"
ATHENA_OUTPUT = f"s3://{S3_BUCKET}/{S3_PREFIX}/athena-query-results/"


def run_athena_query(query: str, database: str = None, description: str = "Query") -> str:
    """Submit query to Athena and wait for completion."""
    print(f"Executing: {description} ...")
    
    config = {"OutputLocation": ATHENA_OUTPUT}
    context = {"Catalog": "AwsDataCatalog"}
    if database:
        context["Database"] = database

    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext=context,
        ResultConfiguration=config
    )
    query_execution_id = response["QueryExecutionId"]
    
    # Poll query status
    while True:
        status_res = athena.get_query_execution(QueryExecutionId=query_execution_id)
        state = status_res["QueryExecution"]["Status"]["State"]
        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            if state == "SUCCEEDED":
                return query_execution_id
            else:
                reason = status_res["QueryExecution"]["Status"].get("StateChangeReason", "Unknown")
                raise RuntimeError(f"Athena query failed: {reason}")
        time.sleep(1.5)


def setup_database():
    """Create Glue Database via Athena DDL query."""
    print(f"\n--- Step 1: Setting up Glue Database '{DATABASE_NAME}' ---")
    query = f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME};"
    run_athena_query(query, description=f"Create database {DATABASE_NAME}")
    print(f"Glue Database '{DATABASE_NAME}' is ready.")


def setup_tables():
    """Create External Tables for raw, cleaned, failed, transformed, and hashed datasets."""
    print(f"\n--- Step 2: Setting up Catalog Tables ---")
    
    # 1. RAW
    raw_ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.raw (
      month STRING,
      town STRING,
      flat_type STRING,
      block STRING,
      street_name STRING,
      storey_range STRING,
      floor_area_sqm DOUBLE,
      flat_model STRING,
      lease_commence_date INT,
      resale_price DOUBLE,
      source_file STRING,
      remaining_lease STRING
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES (
      'separatorChar' = ',',
      'quoteChar' = '\"',
      'escapeChar' = '\\\\'
    )
    STORED AS TEXTFILE
    LOCATION 's3://{S3_BUCKET}/{S3_PREFIX}/raw/'
    TBLPROPERTIES ('skip.header.line.count'='1');
    """
    run_athena_query(raw_ddl, database=DATABASE_NAME, description="Create table 'raw'")

    # 2. CLEANED
    cleaned_ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.cleaned (
      month STRING,
      town STRING,
      flat_type STRING,
      block STRING,
      street_name STRING,
      storey_range STRING,
      floor_area_sqm DOUBLE,
      flat_model STRING,
      lease_commence_date INT,
      resale_price DOUBLE,
      source_file STRING,
      remaining_lease STRING
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES (
      'separatorChar' = ',',
      'quoteChar' = '\"',
      'escapeChar' = '\\\\'
    )
    STORED AS TEXTFILE
    LOCATION 's3://{S3_BUCKET}/{S3_PREFIX}/cleaned/'
    TBLPROPERTIES ('skip.header.line.count'='1');
    """
    run_athena_query(cleaned_ddl, database=DATABASE_NAME, description="Create table 'cleaned'")

    # 3. FAILED
    failed_ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.failed (
      month STRING,
      town STRING,
      flat_type STRING,
      block STRING,
      street_name STRING,
      storey_range STRING,
      floor_area_sqm DOUBLE,
      flat_model STRING,
      lease_commence_date INT,
      resale_price DOUBLE,
      source_file STRING,
      remaining_lease STRING
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES (
      'separatorChar' = ',',
      'quoteChar' = '\"',
      'escapeChar' = '\\\\'
    )
    STORED AS TEXTFILE
    LOCATION 's3://{S3_BUCKET}/{S3_PREFIX}/failed/'
    TBLPROPERTIES ('skip.header.line.count'='1');
    """
    run_athena_query(failed_ddl, database=DATABASE_NAME, description="Create table 'failed'")

    # 4. TRANSFORMED
    transformed_ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.transformed (
      month STRING,
      town STRING,
      flat_type STRING,
      block STRING,
      street_name STRING,
      storey_range STRING,
      floor_area_sqm DOUBLE,
      flat_model STRING,
      lease_commence_date INT,
      resale_price DOUBLE,
      source_file STRING,
      remaining_lease STRING,
      resale_identifier STRING
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES (
      'separatorChar' = ',',
      'quoteChar' = '\"',
      'escapeChar' = '\\\\'
    )
    STORED AS TEXTFILE
    LOCATION 's3://{S3_BUCKET}/{S3_PREFIX}/transformed/'
    TBLPROPERTIES ('skip.header.line.count'='1');
    """
    run_athena_query(transformed_ddl, database=DATABASE_NAME, description="Create table 'transformed'")

    # 5. HASHED
    hashed_ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.hashed (
      month STRING,
      town STRING,
      flat_type STRING,
      block STRING,
      street_name STRING,
      storey_range STRING,
      floor_area_sqm DOUBLE,
      flat_model STRING,
      lease_commence_date INT,
      resale_price DOUBLE,
      source_file STRING,
      remaining_lease STRING,
      resale_identifier STRING,
      hashed_identifier STRING
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES (
      'separatorChar' = ',',
      'quoteChar' = '\"',
      'escapeChar' = '\\\\'
    )
    STORED AS TEXTFILE
    LOCATION 's3://{S3_BUCKET}/{S3_PREFIX}/hashed/'
    TBLPROPERTIES ('skip.header.line.count'='1');
    """
    run_athena_query(hashed_ddl, database=DATABASE_NAME, description="Create table 'hashed'")
    
    print("All tables defined in Athena Catalog successfully.")


def run_verification_queries():
    """Verify that tables are queryable and display statistics."""
    print(f"\n--- Step 3: Executing Verification Queries in Athena ---")
    
    # 1. Fetch counts
    print("Checking counts in tables...")
    query = f"""
    SELECT 
      (SELECT COUNT(*) FROM {DATABASE_NAME}.raw) as total_raw,
      (SELECT COUNT(*) FROM {DATABASE_NAME}.cleaned) as total_cleaned,
      (SELECT COUNT(*) FROM {DATABASE_NAME}.transformed) as total_transformed,
      (SELECT COUNT(*) FROM {DATABASE_NAME}.hashed) as total_hashed,
      (SELECT COUNT(*) FROM {DATABASE_NAME}.failed) as total_failed
    """
    q_id = run_athena_query(query, database=DATABASE_NAME, description="Fetch dataset row counts")
    res = athena.get_query_results(QueryExecutionId=q_id)
    
    rows = res["ResultSet"]["Rows"]
    headers = [col["VarCharValue"] for col in rows[0]["Data"]]
    data_values = [col.get("VarCharValue", "0") for col in rows[1]["Data"]]
    
    print("\nDataset Row Counts (Verified via Athena Queries):")
    for name, val in zip(headers, data_values):
        print(f"  - {name}: {int(val):,}")

    # 2. Sample transformed rows to verify schema alignment
    print("\nRetrieving sample record from 'hashed' table...")
    sample_query = f"SELECT month, town, flat_type, resale_price, resale_identifier, hashed_identifier FROM {DATABASE_NAME}.hashed LIMIT 1;"
    q_id2 = run_athena_query(sample_query, database=DATABASE_NAME, description="Fetch sample hashed record")
    res2 = athena.get_query_results(QueryExecutionId=q_id2)
    rows2 = res2["ResultSet"]["Rows"]
    headers2 = [col["VarCharValue"] for col in rows2[0]["Data"]]
    values2 = [col.get("VarCharValue", "None") for col in rows2[1]["Data"]]
    
    for h, v in zip(headers2, values2):
        print(f"  {h}: {v}")


def main():
    print("Starting HDB Data Platform AWS Athena Configuration Process")
    setup_database()
    setup_tables()
    run_verification_queries()
    print("AWS Data Catalog and Athena setup completed successfully ✓")    print("=================================================================")


if __name__ == "__main__":
    main()
