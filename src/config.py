"""Application configuration and constants."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
UPLOAD_DIR = DATA_DIR / "uploads"

SALES_DIR = ROOT_DIR / "Sales"
EXPENSES_DIR = ROOT_DIR / "Expenses"
DEFAULT_BS_FILE = ROOT_DIR / "Balance Sheet - Sheet1.csv"

# Legacy fallbacks (uploads / older workbook layout)
DEFAULT_PL_FILE = RAW_DIR / "P&L Account.xlsx"
DEFAULT_SALES_FILE = RAW_DIR / "Daily Sales 2.numbers"

OPERATING_EXPENSE_CATEGORIES = [
    "Salaries",
    "Rent",
    "Utilities",
    "Office Expenditure",
    "Staff Expenses",
    "Sundry Expenses",
    "Taxes",
]

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

MONTH_LABELS = [f"{m} 2026" for m in MONTHS]

PAYMENT_MODES = ["Cash", "Card", "Online"]
CARD_MODES = ["Master Card", "Visa Card"]

FORGE_COLORS = {
    "bg": "#0a0a0a",
    "surface": "#111111",
    "border": "#222222",
    "text": "#ffffff",
    "text_muted": "#888888",
    "accent": "#ff5722",
    "accent_dim": "#cc4520",
    "green": "#22c55e",
    "amber": "#f59e0b",
    "red": "#ef4444",
}

CHART_COLORS = [
    "#ff5722", "#ff8a65", "#ffab91", "#4ade80",
    "#60a5fa", "#a78bfa", "#f472b6", "#fbbf24",
]
