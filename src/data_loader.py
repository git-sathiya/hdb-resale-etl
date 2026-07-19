from pathlib import Path
from typing import Union
import io
import pandas as pd

from .config import STORAGE_TYPE


def _parse_s3_uri(uri: str):
    """Split 's3://bucket/key/prefix' into (bucket, prefix)."""
    without_scheme = uri[len("s3://"):]
    bucket, _, prefix = without_scheme.partition("/")
    return bucket, prefix.rstrip("/")


def load_all_csv(input_dir: Union[Path, str]) -> pd.DataFrame:
    """Load all CSV files from *input_dir* (local path or s3:// URI) into a single DataFrame."""

    if isinstance(input_dir, str) and input_dir.startswith("s3://"):
        # -------------------------------------------------------------------
        # S3 mode: list keys under the prefix then stream each into pandas
        # via boto3 (no s3fs / aiobotocore dependency needed)
        # -------------------------------------------------------------------
        import boto3

        bucket, prefix = _parse_s3_uri(input_dir)
        prefix_with_slash = prefix + "/"

        s3 = boto3.client("s3")
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix_with_slash)

        csv_keys = []
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".csv"):
                    csv_keys.append(key)

        if not csv_keys:
            raise FileNotFoundError(f"No CSV files found in {input_dir}")

        dfs = []
        for key in sorted(csv_keys):
            print(f"  Loading s3://{bucket}/{key} …")
            obj = s3.get_object(Bucket=bucket, Key=key)
            body = obj["Body"].read()
            df = pd.read_csv(io.BytesIO(body))
            df["source_file"] = key.split("/")[-1]
            dfs.append(df)

    else:
        # -------------------------------------------------------------------
        # Local mode: original glob-based logic
        # -------------------------------------------------------------------
        local_dir = Path(input_dir)
        files = sorted(local_dir.glob("*.csv"))
        if not files:
            raise FileNotFoundError(f"No CSV files found in {local_dir}")

        dfs = []
        for f in files:
            df = pd.read_csv(f)
            df["source_file"] = f.name
            dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True, sort=False)
    return combined
