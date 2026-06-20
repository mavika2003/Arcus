"""Data loading from Excel, Numbers, and CSV sources."""

from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd

from src.config import EXPENSES_DIR, MONTHS, SALES_DIR
from src.data.validator import clean_numeric


def _month_from_filename(name: str) -> str:
    """Extract month abbreviation from filenames like Jan-Sales - Sheet1.csv."""
    match = re.match(r"^([A-Za-z]+)", name)
    if not match:
        return "Unknown"
    raw = match.group(1).lower()
    for month in MONTHS:
        if month.lower().startswith(raw[:3]):
            return month
    return raw[:3].capitalize()


def load_sales_folder(sales_dir: Path | None = None) -> pd.DataFrame:
    """Load all monthly sales CSV files from the Sales folder."""
    directory = sales_dir or SALES_DIR
    if not directory.exists():
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for path in sorted(directory.glob("*.csv")):
        df = pd.read_csv(path, header=1)
        df = df.loc[:, ~df.columns.duplicated(keep="first")]
        if "Date" not in df.columns:
            continue
        df = df[df["Date"].notna()]
        df = df[~df["Date"].astype(str).str.strip().isin(("", "-", "nan"))]
        df["Month"] = _month_from_filename(path.name)
        frames.append(df)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_expenses_folder(expenses_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load recurring costs and daily COGS CSV files from the Expenses folder."""
    directory = expenses_dir or EXPENSES_DIR
    if not directory.exists():
        return pd.DataFrame(), pd.DataFrame()

    recurring = pd.DataFrame()
    cogs = pd.DataFrame()

    for path in directory.glob("*.csv"):
        name = path.name.lower()
        if "recurring" in name:
            recurring = parse_recurring_costs_csv(path)
        elif "daily" in name or "expense" in name:
            cogs = parse_daily_expenses_csv(path)

    return recurring, cogs


def load_daily_sales(source: str | Path | io.BytesIO) -> pd.DataFrame:
    """Load daily sales from .numbers, .xlsx, or .csv."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.is_dir():
            return load_sales_folder(path)
        suffix = path.suffix.lower()
        if suffix == ".numbers":
            return _load_sales_from_numbers(path)
        if suffix in (".xlsx", ".xls"):
            return _load_sales_from_excel(path)
        if suffix == ".csv":
            return _load_sales_from_csv(path)
        raise ValueError(f"Unsupported file type: {suffix}")

    return _load_sales_from_csv(source)


def _load_sales_from_numbers(path: Path) -> pd.DataFrame:
    from numbers_parser import Document

    doc = Document(str(path))
    frames = []
    for sheet in doc.sheets:
        table = sheet.tables[0]
        rows = list(table.rows(values_only=True))
        if len(rows) < 3:
            continue
        headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(rows[1])]
        data_rows = []
        for row in rows[2:]:
            if row[0] is not None:
                data_rows.append(row)
        if data_rows:
            df = pd.DataFrame(data_rows, columns=headers[: len(data_rows[0])])
            df = df.loc[:, ~df.columns.duplicated(keep="first")]
            df["Month"] = sheet.name.replace("Revised ", "").strip()
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _load_sales_from_excel(path: Path | io.BytesIO) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    frames = []
    for sheet in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet, header=1)
        df["Month"] = sheet.replace("Revised ", "").strip()
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _load_sales_from_csv(source: Path | io.BytesIO) -> pd.DataFrame:
    df = pd.read_csv(source, header=1)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    if "Month" not in df.columns and isinstance(source, Path):
        df["Month"] = _month_from_filename(source.name)
    elif "Month" not in df.columns:
        df["Month"] = "Unknown"
    return df


def load_pl_workbook(source: str | Path | io.BytesIO) -> dict[str, pd.DataFrame]:
    """Load all sheets from the P&L Account workbook."""
    sheets = {}
    xl = pd.ExcelFile(source)
    for name in xl.sheet_names:
        sheets[name] = pd.read_excel(source, sheet_name=name, header=None)
    return sheets


def parse_recurring_costs_csv(path: Path) -> pd.DataFrame:
    """Parse recurring cost CSV (Expenses/Recurring Cost - Sheet1.csv)."""
    df = pd.read_csv(path, header=None)
    return parse_recurring_costs(df)


def parse_daily_expenses_csv(path: Path) -> pd.DataFrame:
    """Parse daily expenses CSV for monthly COGS totals."""
    df = pd.read_csv(path, header=None)
    return parse_daily_expenses_cogs(df)


def parse_recurring_costs(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the Recurring Cost sheet into structured monthly data."""
    header_row = df.iloc[1]
    month_cols = {}
    for i, val in enumerate(header_row):
        if isinstance(val, str) and val.strip() in MONTHS:
            month_cols[val.strip()] = i

    records = []
    for _, row in df.iterrows():
        sr = row.iloc[0]
        name = row.iloc[1]
        if pd.isna(name) or pd.isna(sr):
            continue
        sr_str = str(sr).strip()
        if not sr_str.isdigit():
            continue
        name_str = str(name).strip()
        if not name_str or name_str.startswith("-"):
            continue
        for month, col_idx in month_cols.items():
            amount = clean_numeric(row.iloc[col_idx])
            if amount != 0:
                records.append({
                    "category": name_str,
                    "month": month,
                    "amount": amount,
                })

    return pd.DataFrame(records)


def parse_daily_expenses_cogs(df: pd.DataFrame) -> pd.DataFrame:
    """Extract monthly COGS totals from the Daily Expenses sheet."""
    records = []
    for _, row in df.iterrows():
        desc = row.iloc[1]
        if pd.isna(desc):
            continue
        desc_str = str(desc).strip()
        if desc_str.startswith("COST OF GOODS SOLD"):
            month_part = desc_str.split("-")[-1].strip() if "-" in desc_str else "Unknown"
            records.append({
                "month": month_part[:3],
                "cogs": clean_numeric(row.iloc[34]),
            })
    return pd.DataFrame(records)


def parse_pl_statement(df: pd.DataFrame) -> dict:
    """Parse the P&L sheet into structured line items."""
    month_cols = {}
    for i, val in enumerate(df.iloc[0]):
        if isinstance(val, str) and any(m in val for m in MONTHS):
            month_cols[val.strip()] = i

    ytd_col = 2
    line_items = {}
    for _, row in df.iterrows():
        label = row.iloc[0]
        if pd.isna(label):
            continue
        label_str = str(label).strip()
        if not label_str or label_str.startswith("Company") or label_str.startswith("For the"):
            continue

        entry = {"ytd": clean_numeric(row.iloc[ytd_col])}
        for month_label, col_idx in month_cols.items():
            month_key = month_label.split()[0]
            entry[month_key] = clean_numeric(row.iloc[col_idx + 1])
        line_items[label_str] = entry

    return {"line_items": line_items, "months": list(month_cols.keys())}


def parse_balance_sheet(df: pd.DataFrame) -> dict:
    """Parse the Balance Sheet into assets and liabilities."""
    assets = []
    liabilities = []
    for _, row in df.iterrows():
        left_label = row.iloc[0]
        left_amount = clean_numeric(row.iloc[1]) if pd.notna(row.iloc[1]) else None
        right_label = row.iloc[3] if len(row) > 3 else None
        right_amount = clean_numeric(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else None

        if isinstance(left_label, str) and left_label.strip():
            label = left_label.strip()
            if label not in ("Assets", "Current Assets", "BALANCE SHEET") and not label.startswith("Company") and not label.startswith("For the"):
                if left_amount != 0 or label in ("Cash", "Accounts Receivable", "Inventory", "Furniture & Fixture"):
                    assets.append({"item": label, "amount": left_amount if left_amount != 0 else None})

        if isinstance(right_label, str) and right_label.strip():
            label = right_label.strip()
            if label not in ("Liabilities & Equity", "Current Liabilities", "Long-term Liabilities"):
                liabilities.append({"item": label, "amount": right_amount if right_amount != 0 else None})

    return {"assets": assets, "liabilities": liabilities}


def load_balance_sheet_csv(path: Path) -> dict:
    """Load balance sheet from CSV reference file."""
    df = pd.read_csv(path, header=None)
    return parse_balance_sheet(df)
