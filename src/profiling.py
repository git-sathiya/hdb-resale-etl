import io
import pandas as pd
from pathlib import Path
from typing import Union


def _write_csv(df: pd.DataFrame, output_path: Union[Path, str]):
    """Write *df* as CSV to a local path or an s3:// URI.

    Uses boto3 directly for S3 writes to avoid the s3fs / aiobotocore
    version-conflict problem.
    """
    if isinstance(output_path, str) and output_path.startswith("s3://"):
        import boto3
        without_scheme = output_path[len("s3://"):]
        bucket, _, key = without_scheme.partition("/")
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        boto3.client("s3").put_object(
            Bucket=bucket,
            Key=key,
            Body=buf.getvalue().encode("utf-8"),
            ContentType="text/csv",
        )
    else:
        df.to_csv(output_path, index=False)


def profile_dataframe(df: pd.DataFrame, output_path: Union[Path, str]):
    """Compute and save column-level profiling stats to *output_path*.

    *output_path* may be a local ``Path`` object or an ``s3://`` URI string.
    """
    profile = pd.DataFrame({
        "column":         df.columns,
        "dtype":          [str(df[c].dtype) for c in df.columns],
        "non_null_count": [df[c].notna().sum() for c in df.columns],
        "null_count":     [df[c].isna().sum()  for c in df.columns],
        "null_pct":       [round(df[c].isna().mean() * 100, 2) for c in df.columns],
        "unique_count":   [df[c].nunique(dropna=True) for c in df.columns],
    })
    _write_csv(profile, output_path)
    return profile
