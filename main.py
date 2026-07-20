"""
Main entry point for HDB Resale ETL Pipeline.
Configurable to run locally or migrate/load to AWS S3.
"""

from src.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline()
    print("ETL completed successfully.")

