"""Load dashboard source data from Supabase Postgres."""

from __future__ import annotations

import os

import pandas as pd

from src.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL


def _client():
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _company_id(client) -> str:
    company_id = os.getenv("ARCUS_COMPANY_ID")
    if company_id:
        return company_id
    res = client.table("companies").select("id").eq("name", "Arcus").limit(1).execute()
    if not res.data:
        raise RuntimeError("No company named Arcus in Supabase — run supabase/schema.sql first")
    return res.data[0]["id"]


def load_sales_from_supabase() -> pd.DataFrame:
    client = _client()
    cid = _company_id(client)
    res = (
        client.table("sales_transactions")
        .select("*")
        .eq("company_id", cid)
        .order("sale_date")
        .execute()
    )
    rows = res.data or []
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.rename(columns={
        "sale_date": "Date",
        "restaurant": "Restaurant",
        "careem": "Careem",
        "smile": "SMILE",
        "talabat": "Talabat",
        "noon": "Noon",
        "discount": "Discount",
        "gross_sale": "Gross Sale",
        "net_sale_bt": "Net Sale BT",
        "tax": "Tax",
        "net_sale_at": "Net Sale AT",
        "cash": "Cash",
        "master_card": "Master Card",
        "visa_card": "Visa Card",
        "zomato_paid": "Zomato paid",
        "pay_later": "Pay Later",
        "online_pay": "Online Pay",
        "month": "Month",
    })
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


def load_expenses_from_supabase() -> tuple[pd.DataFrame, pd.DataFrame]:
    client = _client()
    cid = _company_id(client)

    recurring_res = (
        client.table("recurring_expenses")
        .select("category, month, amount")
        .eq("company_id", cid)
        .execute()
    )
    recurring = pd.DataFrame(recurring_res.data or [])

    cogs_res = (
        client.table("monthly_cogs")
        .select("month, cogs")
        .eq("company_id", cid)
        .execute()
    )
    cogs = pd.DataFrame(cogs_res.data or [])

    return recurring, cogs


def load_balance_sheet_from_supabase() -> dict:
    client = _client()
    cid = _company_id(client)
    res = (
        client.table("balance_sheet_items")
        .select("side, item, amount")
        .eq("company_id", cid)
        .execute()
    )
    assets = []
    liabilities = []
    for row in res.data or []:
        entry = {"item": row["item"], "amount": row.get("amount")}
        side = row.get("side", "")
        if side == "asset":
            assets.append(entry)
        else:
            liabilities.append(entry)
    return {"assets": assets, "liabilities": liabilities}


def insert_receipt_to_supabase(record: dict) -> dict:
    """Insert one OCR receipt into receipt_transactions and return the row."""
    client = _client()
    cid = _company_id(client)
    payload = {
        "company_id": cid,
        "transaction_date": record["transaction_date"],
        "vendor_name": record.get("vendor_name"),
        "total_amount": float(record.get("total_amount") or 0),
        "currency": record.get("currency") or "AED",
        "tax_amount": record.get("tax_amount"),
        "taxable_amount": record.get("taxable_amount"),
        "payment_method": record.get("payment_method"),
        "category": record.get("category") or "Sundry Expenses",
        "pl_category": record.get("pl_category") or "Sundry Expenses",
        "description": record.get("description"),
        "line_items": record.get("line_items") or [],
        "image_url": record.get("image_url"),
        "raw_ocr_text": record.get("raw_ocr_text"),
        "category_confidence": record.get("category_confidence"),
    }
    res = client.table("receipt_transactions").insert(payload).execute()
    if not res.data:
        raise RuntimeError("Failed to insert receipt into Supabase")
    return res.data[0]


def load_receipts_from_supabase() -> list[dict]:
    client = _client()
    cid = _company_id(client)
    res = (
        client.table("receipt_transactions")
        .select("*")
        .eq("company_id", cid)
        .order("transaction_date")
        .execute()
    )
    return list(res.data or [])


def apply_receipt_to_expense_tables(record: dict) -> None:
    """Upsert receipt amount into monthly_cogs or recurring_expenses by pl_category."""
    from datetime import datetime

    client = _client()
    cid = _company_id(client)
    amount = float(record.get("total_amount") or 0)
    if amount <= 0:
        return

    tx_date = record.get("transaction_date") or datetime.utcnow().date().isoformat()
    try:
        month = datetime.strptime(str(tx_date)[:10], "%Y-%m-%d").strftime("%b")
    except ValueError:
        month = datetime.utcnow().strftime("%b")

    pl_cat = record.get("pl_category") or "Sundry Expenses"

    if pl_cat == "COGS":
        existing = (
            client.table("monthly_cogs")
            .select("id, cogs")
            .eq("company_id", cid)
            .eq("month", month)
            .limit(1)
            .execute()
        )
        if existing.data:
            row = existing.data[0]
            new_cogs = float(row.get("cogs") or 0) + amount
            client.table("monthly_cogs").update({"cogs": new_cogs}).eq("id", row["id"]).execute()
        else:
            client.table("monthly_cogs").insert({
                "company_id": cid,
                "month": month,
                "cogs": amount,
            }).execute()
        return

    # Operating expense category → append a recurring_expenses row
    client.table("recurring_expenses").insert({
        "company_id": cid,
        "category": pl_cat,
        "month": month,
        "amount": amount,
    }).execute()


def adjust_balance_sheet_cash(delta: float) -> None:
    """Decrease Cash asset by |delta| when money leaves the business (expense paid)."""
    if not delta:
        return
    client = _client()
    cid = _company_id(client)
    res = (
        client.table("balance_sheet_items")
        .select("id, amount")
        .eq("company_id", cid)
        .eq("side", "asset")
        .eq("item", "Cash")
        .limit(1)
        .execute()
    )
    if not res.data:
        return
    row = res.data[0]
    current = row.get("amount")
    if current is None:
        return
    new_amount = float(current) - abs(float(delta))
    client.table("balance_sheet_items").update({"amount": new_amount}).eq("id", row["id"]).execute()
