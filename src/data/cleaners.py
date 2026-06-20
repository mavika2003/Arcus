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
