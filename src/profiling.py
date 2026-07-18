import pandas as pd
from pathlib import Path

def profile_dataframe(df: pd.DataFrame, output_path: Path):
    profile = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[c].dtype) for c in df.columns],
        "non_null_count": [df[c].notna().sum() for c in df.columns],
        "null_count": [df[c].isna().sum() for c in df.columns],
        "null_pct": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
        "unique_count": [df[c].nunique(dropna=True) for c in df.columns]
    })
    profile.to_csv(output_path, index=False)
    return profile
