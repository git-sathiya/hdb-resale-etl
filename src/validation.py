import pandas as pd
import numpy as np

ALLOWED_TOWNS = [
    "ANG MO KIO", "BEDOK", "BISHAN", "BUKIT BATOK", "BUKIT MERAH",
    "BUKIT PANJANG", "BUKIT TIMAH", "CENTRAL AREA", "CHOA CHU KANG",
    "CLEMENTI", "GEYLANG", "HOUGANG", "JURONG EAST", "JURONG WEST",
    "KALLANG/WHAMPOA", "MARINE PARADE", "PASIR RIS", "PUNGGOL",
    "QUEENSTOWN", "SEMBAWANG", "SENGKANG", "SERANGOON", "TAMPINES",
    "TOA PAYOH", "WOODLANDS", "YISHUN"
]

def validate_date(df: pd.DataFrame) -> pd.Series:
    """Validate that the transaction month matches a valid date format."""
    dt = pd.to_datetime(df["month"], errors="coerce")
    return dt.notna()

def validate_town(df: pd.DataFrame) -> pd.Series:
    """Verify that the town is in the list of allowed Singapore HDB towns."""
    return df["town"].astype(str).str.upper().isin(ALLOWED_TOWNS)

def validate_flat_type(df: pd.DataFrame) -> pd.Series:
    """Ensure flat_type matches standard HDB flat types."""
    allowed = {"1 ROOM", "2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE", "MULTI-GENERATION"}
    return df["flat_type"].astype(str).str.upper().isin(allowed)

def validate_flat_model(df: pd.DataFrame) -> pd.Series:
    """Ensure flat_model is not missing or empty."""
    return df["flat_model"].notna() & (df["flat_model"].astype(str).str.strip() != "")

def validate_storey_range(df: pd.DataFrame) -> pd.Series:
    """Verify storey_range has a valid range format (e.g., '01 TO 03') and low <= high."""
    s = df["storey_range"].astype(str).str.extract(r"(\d+)\s*TO\s*(\d+)")
    low = pd.to_numeric(s[0], errors="coerce")
    high = pd.to_numeric(s[1], errors="coerce")
    return low.notna() & high.notna() & (low <= high)

def validate_price(df: pd.DataFrame) -> pd.Series:
    """Check that resale_price is a numeric value greater than zero."""
    price = pd.to_numeric(df["resale_price"], errors="coerce")
    return price.notna() & (price > 0)

def detect_price_anomalies(df: pd.DataFrame) -> pd.Series:
    """Flag price outliers per town and flat_type using the Interquartile Range (IQR) method (3x threshold)."""
    price = pd.to_numeric(df["resale_price"], errors="coerce")
    g = df.groupby(["town", "flat_type"])["resale_price"]
    q1 = g.transform(lambda s: pd.to_numeric(s, errors="coerce").quantile(0.25))
    q3 = g.transform(lambda s: pd.to_numeric(s, errors="coerce").quantile(0.75))
    iqr = q3 - q1
    upper = q3 + 3 * iqr
    lower = q1 - 3 * iqr
    return price.notna() & ((price < lower) | (price > upper))

