"""Data validation utilities."""

from __future__ import annotations

import pandas as pd


def clean_numeric(value) -> float:
    """Convert a value to float, returning 0.0 for invalid entries."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("$", "").replace("\u20c3", "").replace("AED", "").strip()
        if cleaned in ("", "-", "nan", "None"):
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def clean_numeric_series(series: pd.Series) -> pd.Series:
    """Apply numeric cleaning to an entire pandas Series."""
    return series.apply(clean_numeric)


def validate_sales_df(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Validate and clean daily sales data. Returns cleaned df and warnings."""
    warnings: list[str] = []
    required = {"Date", "Gross Sale", "Net Sale BT", "Tax"}
    missing = required - set(df.columns)
    if missing:
        warnings.append(f"Missing columns: {', '.join(sorted(missing))}")

    df = df.copy()
    numeric_cols = [
        "Restaurant", "keeta", "Careem", "SMILE", "Talabat", "Noon",
        "Discount", "Gross Sale", "Net Sale BT", "Tax", "Net Sale AT",
        "Cash", "Master Card", "Visa Card", "Zomato paid", "Pay Later",
        "Online Pay", "Total", "Delta",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        invalid_dates = df["Date"].isna().sum()
        if invalid_dates:
            warnings.append(f"{invalid_dates} rows have invalid dates and were dropped.")
            df = df.dropna(subset=["Date"])

    return df, warnings


def validate_expense_amount(value) -> float:
    """Validate a single expense amount."""
    result = clean_numeric(value)
    if result < 0:
        return abs(result)
    return result
