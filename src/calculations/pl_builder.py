"""P&L statement builder matching the Excel format."""

from __future__ import annotations

import pandas as pd

from src.config import OPERATING_EXPENSE_CATEGORIES
from src.data.validator import clean_numeric


PL_LINE_ORDER = [
    "Gross Sales Revenue",
    "Less : Discount",
    "Adhoc Revenue (Events)",
    "Net Sales Revenue",
    "Cost of Goods Sold",
    "Gross Profit",
    "Operating Expenses",
    " - Salaries",
    " - Rent",
    " - Utilities",
    " - Office Expenditure",
    " - Staff Expenses",
    " - Sundry Expenses",
    " - Taxes",
    "Total Expenses",
    "Net Profit (EBIT)",
    "Net Profit after Interest & Tax",
]

CATEGORY_TO_LABEL = {
    "Salaries": " - Salaries",
    "Rent": " - Rent",
    "Utilities": " - Utilities",
    "Office Expenditure": " - Office Expenditure",
    "Staff Expenses": " - Staff Expenses",
    "Sundry Expenses": " - Sundry Expenses",
    "Taxes": " - Taxes",
}


def build_pl_display_rows(pl_data: dict, months: list[str] | None = None) -> list[dict]:
    """Build rows for the P&L table display from parsed workbook data."""
    line_items = pl_data.get("line_items", {})
    if months is None:
        months = ["Jan", "Feb"]

    display_rows = []
    section_headers = {"Revenue", "Cost of Goods Sold ", "Operating Expenses"}

    for label, entry in line_items.items():
        if label in section_headers:
            display_rows.append({"type": "section", "label": label.strip()})
            continue

        row = {
            "type": "line",
            "label": label.strip(),
            "ytd": clean_numeric(entry.get("ytd", 0)),
        }
        for m in months:
            row[m] = clean_numeric(entry.get(m, 0))
        display_rows.append(row)

    return display_rows


def build_pl_display_rows_from_df(pl_df: pd.DataFrame, months: list[str] | None = None) -> list[dict]:
    """Build P&L display rows from computed monthly dataframe."""
    if pl_df.empty:
        return []

    if months is None:
        months = pl_df["Month"].tolist()

    def ytd(col: str) -> float:
        return float(pl_df[col].sum()) if col in pl_df.columns else 0.0

    def month_val(col: str, month: str) -> float:
        rows = pl_df[pl_df["Month"] == month]
        if rows.empty or col not in pl_df.columns:
            return 0.0
        return float(rows[col].iloc[0])

    rows: list[dict] = []

    def add_line(label: str, col: str, negate: bool = False):
        row: dict = {"type": "line", "label": label, "ytd": ytd(col) * (-1 if negate else 1)}
        for m in months:
            row[m] = month_val(col, m) * (-1 if negate else 1)
        rows.append(row)

    rows.append({"type": "section", "label": "Revenue"})
    add_line("Gross Sales Revenue", "gross_sales")
    add_line("Less : Discount", "discounts", negate=True)
    add_line("Net Sales Revenue", "net_sales")

    rows.append({"type": "section", "label": "Cost of Goods Sold"})
    add_line("Cost of Goods Sold", "cogs")
    add_line("Gross Profit", "gross_profit")

    rows.append({"type": "section", "label": "Operating Expenses"})
    for cat in OPERATING_EXPENSE_CATEGORIES:
        label = CATEGORY_TO_LABEL[cat]
        add_line(label, cat)

    add_line("Total Expenses", "operating_expenses")
    add_line("Net Profit (EBIT)", "net_profit")

    return rows
