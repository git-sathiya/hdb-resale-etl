import pandas as pd
import hashlib

def hash_identifier(df: pd.DataFrame, col: str = "resale_identifier") -> pd.DataFrame:
    """Generate SHA-256 hash of the unique resale identifier for data masking/anonymization."""
    df = df.copy()
    df["hashed_identifier"] = df[col].astype(str).apply(
        lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()
    )
    return df

