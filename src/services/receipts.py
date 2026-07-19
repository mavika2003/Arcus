"""Receipt ingestion: OCR → categorize → persist → P&L / BS impact."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.config import MONTHS, USE_SUPABASE
from src.data.ocr_parser import ParsedReceipt, process_receipt_image
from src.data.receipt_store import load_receipts_local, save_receipt_local
from src.services.categorizer import map_to_pl_category


def _month_from_iso(iso_date: str | None) -> str:
    if not iso_date:
        return datetime.utcnow().strftime("%b")
    try:
        return datetime.strptime(str(iso_date)[:10], "%Y-%m-%d").strftime("%b")
    except ValueError:
        return datetime.utcnow().strftime("%b")


def receipt_to_record(parsed: ParsedReceipt, image_url: str | None = None) -> dict[str, Any]:
    pl_category = map_to_pl_category(parsed.category)
    return {
        "transaction_date": parsed.transaction_date or datetime.utcnow().date().isoformat(),
        "vendor_name": parsed.vendor_name,
        "total_amount": float(parsed.total_amount or 0),
        "currency": parsed.currency or "AED",
        "tax_amount": parsed.tax_amount,
        "taxable_amount": parsed.taxable_amount,
        "payment_method": parsed.payment_method,
        "category": parsed.category,
        "pl_category": pl_category,
        "description": parsed.description,
        "line_items": [
            {
                "name": li.name,
                "quantity": li.quantity,
                "unit_price": li.unit_price,
                "amount": li.amount,
                "barcode": li.barcode,
            }
            for li in parsed.line_items
        ],
        "image_url": image_url,
        "raw_ocr_text": parsed.raw_text,
        "category_confidence": parsed.category_confidence,
        "warnings": list(parsed.warnings),
    }


def parsed_to_preview(parsed: ParsedReceipt, filename: str | None = None) -> dict[str, Any]:
    """Build a preview payload from OCR — not persisted."""
    record = receipt_to_record(parsed)
    if filename:
        record["source_filename"] = filename
    return {
        "vendor_name": record["vendor_name"],
        "transaction_date": record["transaction_date"],
        "total_amount": record["total_amount"],
        "currency": record["currency"],
        "tax_amount": record.get("tax_amount"),
        "taxable_amount": record.get("taxable_amount"),
        "payment_method": record.get("payment_method"),
        "category": record["category"],
        "pl_category": record["pl_category"],
        "category_confidence": record.get("category_confidence"),
        "description": record.get("description"),
        "line_items": record.get("line_items") or [],
        "warnings": record.get("warnings") or [],
        "raw_ocr_text": record.get("raw_ocr_text"),
        "source_filename": record.get("source_filename"),
    }


def preview_receipt_bytes(image_bytes: bytes, filename: str | None = None) -> dict[str, Any]:
    """OCR only — returns editable preview, does not save."""
    parsed = process_receipt_image(image_bytes, filename=filename)
    return parsed_to_preview(parsed, filename=filename)


def confirm_receipt_record(data: dict[str, Any]) -> dict[str, Any]:
    """Persist user-confirmed (possibly edited) receipt data."""
    import logging

    logger = logging.getLogger(__name__)

    pl_category = data.get("pl_category") or map_to_pl_category(data.get("category") or "Uncategorized")
    category = data.get("category") or pl_category

    record: dict[str, Any] = {
        "transaction_date": data.get("transaction_date") or datetime.utcnow().date().isoformat(),
        "vendor_name": data.get("vendor_name"),
        "total_amount": float(data.get("total_amount") or 0),
        "currency": data.get("currency") or "AED",
        "tax_amount": data.get("tax_amount"),
        "taxable_amount": data.get("taxable_amount"),
        "payment_method": data.get("payment_method"),
        "category": category,
        "pl_category": pl_category,
        "description": data.get("description"),
        "line_items": data.get("line_items") or [],
        "image_url": data.get("image_url"),
        "raw_ocr_text": data.get("raw_ocr_text"),
        "category_confidence": data.get("category_confidence"),
        "warnings": data.get("warnings") or [],
        "source_filename": data.get("source_filename"),
    }

    persisted_to = "local"
    if USE_SUPABASE:
        try:
            from src.data.supabase_loaders import insert_receipt_to_supabase
            stored = insert_receipt_to_supabase(record)
            persisted_to = "supabase"
        except Exception as exc:  # noqa: BLE001
            # Common on first deploy: schema.sql receipt_transactions not applied yet
            logger.warning("Supabase receipt insert failed, using local store: %s", exc)
            stored = save_receipt_local(record)
            record.setdefault("warnings", []).append(
                "Saved locally — create public.receipt_transactions in Supabase "
                "(run supabase/schema.sql) for cloud persistence."
            )
    else:
        stored = save_receipt_local(record)

    return {
        "id": stored.get("id"),
        **{k: record[k] for k in (
            "vendor_name", "transaction_date", "total_amount", "currency",
            "tax_amount", "payment_method", "category", "pl_category",
            "description", "line_items",
        )},
        "warnings": record.get("warnings") or [],
        "persisted_to": persisted_to,
    }


def ingest_receipt_bytes(image_bytes: bytes, filename: str | None = None) -> dict[str, Any]:
    """Legacy: OCR + immediate save. Prefer preview + confirm flow."""
    preview = preview_receipt_bytes(image_bytes, filename=filename)
    return confirm_receipt_record(preview)


def load_all_receipts() -> list[dict[str, Any]]:
    if USE_SUPABASE:
        try:
            from src.data.supabase_loaders import load_receipts_from_supabase
            return load_receipts_from_supabase()
        except Exception:
            return load_receipts_local()
    return load_receipts_local()


def receipts_to_expense_frames(
    receipts: list[dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Aggregate receipts into (recurring_expenses-like df, cogs df, total cash outflow).

    recurring columns: category, month, amount
    cogs columns: month, cogs
    """
    rows = receipts if receipts is not None else load_all_receipts()
    expense_rows: list[dict] = []
    cogs_by_month: dict[str, float] = {}
    cash_out = 0.0

    for r in rows:
        amount = float(r.get("total_amount") or 0)
        if amount <= 0:
            continue
        cash_out += amount
        month = _month_from_iso(r.get("transaction_date"))
        pl_cat = r.get("pl_category") or map_to_pl_category(r.get("category") or "Uncategorized")
        if pl_cat == "COGS":
            cogs_by_month[month] = cogs_by_month.get(month, 0.0) + amount
        else:
            expense_rows.append({
                "category": pl_cat,
                "month": month,
                "amount": amount,
            })

    recurring = pd.DataFrame(expense_rows) if expense_rows else pd.DataFrame(
        columns=["category", "month", "amount"]
    )
    cogs_rows = [
        {"month": m, "cogs": v} for m, v in cogs_by_month.items() if v > 0
    ]
    cogs = pd.DataFrame(cogs_rows) if cogs_rows else pd.DataFrame(columns=["month", "cogs"])
    return recurring, cogs, cash_out


def merge_receipt_expenses(
    recurring: pd.DataFrame,
    cogs: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """Merge OCR receipt aggregates into existing expense / COGS frames."""
    r_extra, c_extra, cash_out = receipts_to_expense_frames()

    if not r_extra.empty:
        recurring = pd.concat([recurring, r_extra], ignore_index=True) if not recurring.empty else r_extra

    if not c_extra.empty:
        if cogs.empty:
            cogs = c_extra.copy()
        else:
            cogs = cogs.copy()
            # normalize column name
            if "Month" in cogs.columns and "month" not in cogs.columns:
                cogs = cogs.rename(columns={"Month": "month"})
            merged = (
                pd.concat([cogs, c_extra], ignore_index=True)
                .groupby("month", as_index=False)["cogs"]
                .sum()
            )
            cogs = merged

    return recurring, cogs, cash_out


def apply_receipt_bs_impact(bs_data: dict, receipts: list[dict[str, Any]]) -> dict:
    """
    Reflect receipt purchases on the balance sheet:
    - COGS / grocery → increase Inventory
    - Card payment → increase Accounts Payable (short-term liability)
    - Cash payment → decrease Cash
    """
    if not bs_data or not receipts:
        return bs_data

    assets = [dict(a) for a in bs_data.get("assets", [])]
    liabilities = [dict(l) for l in bs_data.get("liabilities", [])]

    def _bump(items: list[dict], item_name: str, delta: float) -> None:
        for row in items:
            if str(row.get("item", "")).strip().lower() == item_name.lower():
                base = row.get("amount")
                current = float(base) if base is not None else 0.0
                row["amount"] = round(current + delta, 2)
                return
        items.append({"item": item_name, "amount": round(delta, 2)})

    for r in receipts:
        amount = float(r.get("total_amount") or 0)
        if amount <= 0:
            continue
        pl_cat = r.get("pl_category") or map_to_pl_category(r.get("category") or "")
        pay = (r.get("payment_method") or "").upper()
        is_card = pay in ("VISA", "MASTERCARD", "CARD", "MAGNATI", "EFT")

        if pl_cat == "COGS":
            _bump(assets, "Inventory", amount)

        if is_card:
            _bump(liabilities, "Accounts Payable", amount)
        else:
            _bump(assets, "Cash", -amount)

    return {"assets": assets, "liabilities": liabilities}


def apply_cash_outflow_to_bs(bs_data: dict, cash_out: float) -> dict:
    """Legacy helper — prefer apply_receipt_bs_impact for itemized updates."""
    if not cash_out or not bs_data:
        return bs_data
    assets = []
    for item in bs_data.get("assets", []):
        entry = dict(item)
        if str(entry.get("item", "")).strip().lower() == "cash" and entry.get("amount") is not None:
            try:
                entry["amount"] = float(entry["amount"]) - abs(cash_out)
            except (TypeError, ValueError):
                pass
        assets.append(entry)
    return {
        "assets": assets,
        "liabilities": list(bs_data.get("liabilities", [])),
    }
