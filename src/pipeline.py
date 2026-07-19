"""Data pipeline orchestrator."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from src.calculations.balance_sheet import compute_balance_sheet_totals
from src.calculations.financials import (
    build_monthly_pl,
    compute_ytd_summary,
    get_daily_trends,
    get_expense_breakdown,
    get_monthly_trends,
    get_payment_distribution,
)
from src.calculations.pl_builder import build_pl_display_rows, build_pl_display_rows_from_df
from src.config import DEFAULT_BS_FILE, EXPENSES_DIR, MONTHS, SALES_DIR, USE_SUPABASE
from src.data.cleaners import (
    clean_sales_data,
    empty_sales_for_months,
    merge_financial_data,
    months_from_expense_data,
)
from src.data.loaders import (
    load_balance_sheet_csv,
    load_daily_sales,
    load_expenses_folder,
    load_pl_workbook,
    load_sales_folder,
    parse_balance_sheet,
    parse_daily_expenses_cogs,
    parse_pl_statement,
    parse_recurring_costs,
)
from src.services.alerts import get_all_alerts
from src.services.receipts import apply_receipt_bs_impact, load_all_receipts, merge_receipt_expenses


class DashboardData:
    """Container for all processed dashboard data."""

    def __init__(self):
        self.sales_df: pd.DataFrame = pd.DataFrame()
        self.pl_df: pd.DataFrame = pd.DataFrame()
        self.recurring_costs: pd.DataFrame = pd.DataFrame()
        self.expense_breakdown: pd.DataFrame = pd.DataFrame()
        self.payment_dist: pd.DataFrame = pd.DataFrame()
        self.daily_trends: pd.DataFrame = pd.DataFrame()
        self.monthly_trends: pd.DataFrame = pd.DataFrame()
        self.ytd_summary: dict = {}
        self.pl_display_rows: list[dict] = []
        self.pl_workbook_data: dict = {}
        self.bs_data: dict = {}
        self.bs_totals: dict = {}
        self.alerts: list[dict] = []
        self.warnings: list[str] = []
        self.company_name: str = "Arcus"
        self.months: list[str] = []
        self.receipts: list[dict] = []
        self.receipt_cash_outflow: float = 0.0


def process_data(
    sales_source: str | Path | io.BytesIO | None = None,
    pl_source: str | Path | io.BytesIO | None = None,
) -> DashboardData:
    """Run the full data ingestion and calculation pipeline."""
    data = DashboardData()

    # --- Sales ---
    try:
        if USE_SUPABASE:
            from src.data.supabase_loaders import load_sales_from_supabase
            raw_sales = load_sales_from_supabase()
        elif sales_source is not None:
            raw_sales = load_daily_sales(sales_source)
        elif SALES_DIR.exists() and list(SALES_DIR.glob("*.csv")):
            raw_sales = load_sales_folder()
        else:
            from src.config import DEFAULT_SALES_FILE
            raw_sales = load_daily_sales(DEFAULT_SALES_FILE)

        data.sales_df, sales_warnings = clean_sales_data(raw_sales)
        data.warnings.extend(sales_warnings)
    except Exception as e:
        data.warnings.append(f"Sales load error: {e}")
        data.sales_df = pd.DataFrame()

    # --- Expenses & balance sheet ---
    cogs_df = pd.DataFrame()
    try:
        if USE_SUPABASE:
            from src.data.supabase_loaders import (
                load_balance_sheet_from_supabase,
                load_expenses_from_supabase,
            )
            data.recurring_costs, cogs_df = load_expenses_from_supabase()
            data.bs_data = load_balance_sheet_from_supabase()
        elif pl_source is not None:
            workbook = load_pl_workbook(pl_source)
            if "Recurring Cost" in workbook:
                data.recurring_costs = parse_recurring_costs(workbook["Recurring Cost"])
            if "Daily Expenses" in workbook:
                cogs_df = parse_daily_expenses_cogs(workbook["Daily Expenses"])
            if "P&L" in workbook:
                data.pl_workbook_data = parse_pl_statement(workbook["P&L"])
            if "Balance Sheet" in workbook:
                data.bs_data = parse_balance_sheet(workbook["Balance Sheet"])
        elif EXPENSES_DIR.exists():
            data.recurring_costs, cogs_df = load_expenses_folder()
            if DEFAULT_BS_FILE.exists():
                data.bs_data = load_balance_sheet_csv(DEFAULT_BS_FILE)
        else:
            from src.config import DEFAULT_PL_FILE
            workbook = load_pl_workbook(DEFAULT_PL_FILE)
            if "Recurring Cost" in workbook:
                data.recurring_costs = parse_recurring_costs(workbook["Recurring Cost"])
            if "Daily Expenses" in workbook:
                cogs_df = parse_daily_expenses_cogs(workbook["Daily Expenses"])
            if "Balance Sheet" in workbook:
                data.bs_data = parse_balance_sheet(workbook["Balance Sheet"])
    except Exception as e:
        data.warnings.append(f"Expenses load error: {e}")

    # --- OCR receipts → merge into expenses / COGS and balance sheet ---
    try:
        data.receipts = load_all_receipts()
        data.recurring_costs, cogs_df, data.receipt_cash_outflow = merge_receipt_expenses(
            data.recurring_costs, cogs_df
        )
        if data.bs_data and data.receipts:
            data.bs_data = apply_receipt_bs_impact(data.bs_data, data.receipts)
    except Exception as e:
        data.warnings.append(f"Receipt merge error: {e}")

    # --- Build P&L from sales + expenses (including OCR receipts) ---
    has_expenses = (
        not data.recurring_costs.empty
        or (not cogs_df.empty and "cogs" in cogs_df.columns and cogs_df["cogs"].sum() > 0)
        or (not cogs_df.empty and "month" in cogs_df.columns)
    )
    sales_for_pl = data.sales_df
    if sales_for_pl.empty and has_expenses:
        expense_months = months_from_expense_data(data.recurring_costs, cogs_df)
        if expense_months:
            sales_for_pl = empty_sales_for_months(expense_months)

    if not sales_for_pl.empty:
        merged = merge_financial_data(sales_for_pl, data.recurring_costs, cogs_df)
        data.pl_df = build_monthly_pl(merged)
        data.months = [m for m in MONTHS if m in data.pl_df["Month"].values]
        if not data.months:
            data.months = months_from_expense_data(data.recurring_costs, cogs_df)
        data.pl_display_rows = build_pl_display_rows_from_df(data.pl_df, months=data.months)
        data.ytd_summary = compute_ytd_summary(data.pl_df)
    elif data.pl_workbook_data and not data.receipts:
        data.months = [m.split()[0] for m in data.pl_workbook_data.get("months", [])]
        active_months = [m for m in MONTHS if m in data.months] or data.months[:2]
        data.pl_display_rows = build_pl_display_rows(data.pl_workbook_data, months=active_months)
        data.ytd_summary = _ytd_from_workbook(data)
        rev = data.ytd_summary["ytd_revenue"]
        np = data.ytd_summary["ytd_net_profit"]
        data.ytd_summary["ytd_operating_margin"] = (np / rev * 100) if rev else 0

    data.expense_breakdown = get_expense_breakdown(data.recurring_costs)
    data.payment_dist = get_payment_distribution(data.sales_df) if not data.sales_df.empty else pd.DataFrame()
    data.daily_trends = get_daily_trends(data.sales_df) if not data.sales_df.empty else pd.DataFrame()
    data.monthly_trends = get_monthly_trends(data.pl_df) if not data.pl_df.empty else pd.DataFrame()
    data.bs_totals = compute_balance_sheet_totals(
        data.bs_data, data.ytd_summary.get("ytd_net_profit", 0)
    )
    data.alerts = get_all_alerts(data.recurring_costs, data.pl_df)

    return data


def _ytd_from_workbook(data: DashboardData) -> dict:
    """Fallback YTD from parsed workbook P&L."""
    items = data.pl_workbook_data.get("line_items", {})
    return {
        "ytd_revenue": items.get("Net Sales Revenue", {}).get("ytd", 0),
        "ytd_gross_profit": items.get("Gross Profit", {}).get("ytd", 0),
        "ytd_total_expenses": items.get("Total Expenses", {}).get("ytd", 0),
        "ytd_net_profit": items.get("Net Profit (EBIT)", {}).get("ytd", 0),
        "ytd_operating_margin": 0,
        "ytd_cogs": items.get("Cost of Goods Sold", {}).get("ytd", 0),
        "ytd_operating_expenses": items.get("Total Expenses", {}).get("ytd", 0),
    }
