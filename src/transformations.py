import pandas as pd
import numpy as np
from datetime import datetime

def compute_remaining_lease(df: pd.DataFrame) -> pd.DataFrame:
    """Compute remaining lease duration in years & months based on a 99-year lease from lease_commence_date."""
    df = df.copy()
    lease_col = "remaining_lease"

    if lease_col in df.columns:
        return df

    month_dt = pd.to_datetime(df["month"], errors="coerce")
    built_year = pd.to_numeric(df["lease_commence_date"], errors="coerce")
    end_dt = pd.to_datetime(built_year.astype("Int64").astype(str) + "-12-31", errors="coerce") + pd.DateOffset(years=99)

    today = pd.Timestamp.today().normalize()
    remaining_days = (end_dt - today).dt.days
    remaining_days = remaining_days.clip(lower=0)

    years = remaining_days // 365
    months = (remaining_days % 365) // 30

    df["remaining_lease"] = years.astype("Int64").astype(str) + " years " + months.astype("Int64").astype(str) + " months"
    return df

def create_resale_identifier(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a unique surrogate key (resale_identifier) based on block, average price, month, and town."""
    df = df.copy()

    month_dt = pd.to_datetime(df["month"], errors="coerce")
    df["month_dt"] = month_dt
    df["year_month"] = month_dt.dt.to_period("M").astype(str)

    df["block_digits"] = df["block"].astype(str).str.extract(r"(\d+)")[0].fillna("")
    df["block_digits3"] = df["block_digits"].str.zfill(3).str[:3]

    avg_price = (
        df.groupby(["year_month", "town", "flat_type"])["resale_price"]
        .transform(lambda s: pd.to_numeric(s, errors="coerce").mean())
    )
    avg_first2 = avg_price.fillna(0).astype(int).astype(str).str[:2].str.zfill(2)

    month2 = month_dt.dt.month.fillna(0).astype(int).astype(str).str.zfill(2)
    town_first = df["town"].astype(str).str.strip().str[0].str.upper()

    df["resale_identifier"] = "S" + df["block_digits3"] + avg_first2 + month2 + town_first
    return df

def remove_duplicates_keep_highest(df: pd.DataFrame):
    """De-duplicate records based on transaction characteristics, keeping the record with the highest price."""
    key_cols = [c for c in df.columns if c != "resale_price"]
    df = df.copy()
    df["resale_price_num"] = pd.to_numeric(df["resale_price"], errors="coerce")

    df = df.sort_values("resale_price_num", ascending=False)
    deduped = df.drop_duplicates(subset=key_cols, keep="first")

    dup_mask = df.duplicated(subset=key_cols, keep="first")
    failed = df.loc[dup_mask].drop(columns=["resale_price_num"])
    kept = deduped.drop(columns=["resale_price_num"])
    return kept, failed

