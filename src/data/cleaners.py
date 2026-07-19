"""Data cleaning and merging pipeline."""

from __future__ import annotations

import pandas as pd

from src.data.validator import clean_numeric, validate_sales_df


def clean_sales_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Clean and standardize daily sales data."""
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    df, warnings = validate_sales_df(df)

    if "Discount" in df.columns:
        disc_cols = [c for c in df.columns if "Discount" in str(c)]
        if len(disc_cols) > 1:
            df["Discount"] = df[disc_cols].apply(
                lambda row: next((v for v in row if pd.notna(v) and v != 0), 0), axis=1
            )
            df = df.drop(columns=[c for c in disc_cols if c != "Discount"], errors="ignore")
        df["Discount"] = df["Discount"].apply(clean_numeric)

    payment_cols = ["Cash", "Master Card", "Visa Card", "Online Pay", "Zomato paid", "Pay Later"]
    for col in payment_cols:
        if col not in df.columns:
            df[col] = 0.0

    df["Card"] = df["Master Card"] + df["Visa Card"]
    df["Online"] = df["Online Pay"] + df["Zomato paid"]

    if "Month" not in df.columns:
        df["Month"] = df["Date"].dt.strftime("%b")

    return df, warnings


def empty_sales_for_months(months: list[str]) -> pd.DataFrame:
    """Zero-filled daily sales frame for months that only have expense/receipt data."""
    rows = []
    for m in months:
        rows.append({
            "Month": m,
            "Gross Sale": 0.0,
            "Discount": 0.0,
            "Net Sale BT": 0.0,
            "Tax": 0.0,
            "Cash": 0.0,
            "Master Card": 0.0,
            "Visa Card": 0.0,
            "Online Pay": 0.0,
            "Zomato paid": 0.0,
            "Pay Later": 0.0,
            "Card": 0.0,
            "Online": 0.0,
        })
    return pd.DataFrame(rows)


def months_from_expense_data(
    recurring_costs: pd.DataFrame,
    cogs_df: pd.DataFrame,
) -> list[str]:
    """Collect month labels present in expense / COGS frames."""
    from src.config import MONTHS

    found: set[str] = set()
    if not recurring_costs.empty and "month" in recurring_costs.columns:
        found.update(str(m) for m in recurring_costs["month"].dropna().unique())
    if not cogs_df.empty:
        col = "month" if "month" in cogs_df.columns else "Month"
        if col in cogs_df.columns:
            found.update(str(m) for m in cogs_df[col].dropna().unique())
    return sorted(found, key=lambda m: MONTHS.index(m) if m in MONTHS else 99)


def merge_financial_data(
    sales_df: pd.DataFrame,
    recurring_costs: pd.DataFrame,
    cogs_df: pd.DataFrame,
) -> dict:
    """Merge sales, recurring costs, and COGS into a unified dataset."""
    sales_monthly = (
        sales_df.groupby("Month", as_index=False)
        .agg(
            gross_sales=("Gross Sale", "sum"),
            discounts=("Discount", "sum"),
            net_sales=("Net Sale BT", "sum"),
            tax=("Tax", "sum"),
            cash=("Cash", "sum"),
            card=("Card", "sum"),
            online=("Online", "sum"),
        )
    )

    if not recurring_costs.empty:
        expense_monthly = (
            recurring_costs.groupby(["month", "category"], as_index=False)["amount"]
            .sum()
        )
        expense_pivot = expense_monthly.pivot_table(
            index="month", columns="category", values="amount", fill_value=0
        ).reset_index()
    else:
        expense_pivot = pd.DataFrame(columns=["month"])

    if not cogs_df.empty:
        cogs_monthly = cogs_df.rename(columns={"month": "Month"})
    else:
        cogs_monthly = pd.DataFrame(columns=["Month", "cogs"])

    return {
        "sales_monthly": sales_monthly,
        "expense_monthly": expense_pivot,
        "cogs_monthly": cogs_monthly,
        "sales_daily": sales_df,
    }
