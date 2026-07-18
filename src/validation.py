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
    dt = pd.to_datetime(df["month"], errors="coerce")
    return dt.notna()

def validate_town(df: pd.DataFrame) -> pd.Series:
    return df["town"].astype(str).str.upper().isin(ALLOWED_TOWNS)

def validate_flat_type(df: pd.DataFrame) -> pd.Series:
    allowed = {"1 ROOM", "2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE", "MULTI-GENERATION"}
    return df["flat_type"].astype(str).str.upper().isin(allowed)

def validate_flat_model(df: pd.DataFrame) -> pd.Series:
    return df["flat_model"].notna() & (df["flat_model"].astype(str).str.strip() != "")

def validate_storey_range(df: pd.DataFrame) -> pd.Series:
    s = df["storey_range"].astype(str).str.extract(r"(\d+)\s*TO\s*(\d+)")
    low = pd.to_numeric(s[0], errors="coerce")
    high = pd.to_numeric(s[1], errors="coerce")
    return low.notna() & high.notna() & (low <= high)

def validate_price(df: pd.DataFrame) -> pd.Series:
    price = pd.to_numeric(df["resale_price"], errors="coerce")
    return price.notna() & (price > 0)

def detect_price_anomalies(df: pd.DataFrame) -> pd.Series:
    price = pd.to_numeric(df["resale_price"], errors="coerce")
    g = df.groupby(["town", "flat_type"])["resale_price"]
    q1 = g.transform(lambda s: pd.to_numeric(s, errors="coerce").quantile(0.25))
    q3 = g.transform(lambda s: pd.to_numeric(s, errors="coerce").quantile(0.75))
    iqr = q3 - q1
    upper = q3 + 3 * iqr
    lower = q1 - 3 * iqr
    return price.notna() & ((price < lower) | (price > upper))
