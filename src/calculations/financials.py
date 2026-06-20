"""Core financial calculations matching the P&L workbook formulas."""

from __future__ import annotations

import pandas as pd

from src.config import MONTHS, OPERATING_EXPENSE_CATEGORIES
from src.data.validator import clean_numeric


def calculate_gross_profit(revenue: float, cogs: float) -> float:
    return revenue - cogs


def calculate_net_profit(gross_profit: float, operating_expenses: float) -> float:
    return gross_profit - operating_expenses


def calculate_operating_margin(net_profit: float, revenue: float) -> float:
    if revenue == 0:
        return 0.0
    return (net_profit / revenue) * 100


def _month_sort_key(month: str) -> int:
    try:
        return MONTHS.index(month)
    except ValueError:
        return 99


def build_monthly_pl(merged_data: dict) -> pd.DataFrame:
    """
    Build monthly P&L from sales, COGS, and recurring operating expenses.

    Formulas (matching P&L - Sheet1.csv):
      Net Sales Revenue = Gross Sales − Discounts
      Gross Profit = Net Sales − COGS
      Net Profit (EBIT) = Gross Profit − Operating Expenses
      Total Cost (for overview) = COGS + Operating Expenses
    """
    sales = merged_data["sales_monthly"].copy()
    cogs = merged_data["cogs_monthly"].copy()
    expenses = merged_data["expense_monthly"].copy()

    pl = sales.merge(cogs, on="Month", how="left")
    if not expenses.empty and "month" in expenses.columns:
        expenses = expenses.rename(columns={"month": "Month"})
        pl = pl.merge(expenses, on="Month", how="left")

    pl["cogs"] = pl["cogs"].fillna(0)
    pl["gross_profit"] = pl["net_sales"] - pl["cogs"]

    for cat in OPERATING_EXPENSE_CATEGORIES:
        if cat not in pl.columns:
            pl[cat] = 0.0
        pl[cat] = pl[cat].fillna(0)

    pl["operating_expenses"] = pl[OPERATING_EXPENSE_CATEGORIES].sum(axis=1)
    pl["total_expenses"] = pl["cogs"] + pl["operating_expenses"]
    pl["net_profit"] = pl["gross_profit"] - pl["operating_expenses"]
    pl["operating_margin"] = pl.apply(
        lambda r: calculate_operating_margin(r["net_profit"], r["net_sales"]), axis=1
    )

    pl = pl.sort_values("Month", key=lambda s: s.map(_month_sort_key)).reset_index(drop=True)
    return pl


def compute_ytd_summary(pl_df: pd.DataFrame) -> dict:
    """Compute year-to-date financial summary metrics."""
    return {
        "ytd_revenue": float(pl_df["net_sales"].sum()),
        "ytd_gross_profit": float(pl_df["gross_profit"].sum()),
        "ytd_total_expenses": float(pl_df["total_expenses"].sum()),
        "ytd_net_profit": float(pl_df["net_profit"].sum()),
        "ytd_operating_margin": calculate_operating_margin(
            pl_df["net_profit"].sum(), pl_df["net_sales"].sum()
        ),
        "ytd_cogs": float(pl_df["cogs"].sum()),
        "ytd_operating_expenses": float(pl_df["operating_expenses"].sum()),
    }


def get_payment_distribution(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales by payment mode."""
    totals = {
        "Cash": sales_df["Cash"].sum(),
        "Card": sales_df["Card"].sum(),
        "Online": sales_df["Online"].sum(),
    }
    return pd.DataFrame([
        {"mode": k, "amount": v} for k, v in totals.items() if v > 0
    ])


def get_expense_breakdown(recurring_costs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate expenses by category for charting."""
    if recurring_costs.empty:
        return pd.DataFrame(columns=["category", "amount"])
    return (
        recurring_costs.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )


def get_daily_trends(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Get daily sales trends for line chart."""
    daily = (
        sales_df.groupby("Date", as_index=False)
        .agg(sales=("Net Sale BT", "sum"), tax=("Tax", "sum"))
    )
    return daily.sort_values("Date")


def get_monthly_trends(pl_df: pd.DataFrame) -> pd.DataFrame:
    """Get monthly revenue, total cost, and profit for overview charts."""
    if pl_df.empty:
        return pd.DataFrame(columns=["Month", "net_sales", "total_expenses", "net_profit"])
    trends = pl_df[["Month", "net_sales", "total_expenses", "net_profit"]].copy()
    return trends.sort_values("Month", key=lambda s: s.map(_month_sort_key))


def format_currency(value: float) -> str:
    """Format a number as currency."""
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value:,.0f}"
    return f"${value:,.2f}"
