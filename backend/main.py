"""FastAPI backend for Arcus financial dashboard."""

import io
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline import process_data
from src.services.categorizer import categorize_expense
from src.services.export import export_to_excel, export_to_pdf
from src.services.receipts import (
  confirm_receipt_record,
  ingest_receipt_bytes,
  load_all_receipts,
  preview_receipt_bytes,
)

app = FastAPI(title="Arcus Financial API", version="1.0.0")

router = APIRouter(prefix="/api")

# CORS — allow Vercel frontend + custom domains via ALLOWED_ORIGINS (comma-separated)
_default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
]
_extra = os.getenv("ALLOWED_ORIGINS", "")
if _extra:
    _default_origins.extend(o.strip() for o in _extra.split(",") if o.strip())
if frontend_url := os.getenv("FRONTEND_URL"):
    _default_origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins,
    allow_origin_regex=r"https://.*\.(vercel\.app|onrender\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _json_safe(obj):
  """Convert numpy/pandas types to JSON-serializable Python types."""
  if isinstance(obj, (np.integer,)):
    return int(obj)
  if isinstance(obj, (np.floating,)):
    return float(obj)
  if isinstance(obj, np.ndarray):
    return obj.tolist()
  if isinstance(obj, pd.Timestamp):
    return obj.isoformat()
  if isinstance(obj, dict):
    return {k: _json_safe(v) for k, v in obj.items()}
  if isinstance(obj, list):
    return [_json_safe(v) for v in obj]
  if pd.isna(obj):
    return None
  return obj


def _serialize_dashboard(data) -> dict:
  pl_records = data.pl_df.to_dict(orient="records") if not data.pl_df.empty else []
  daily_records = []
  if not data.daily_trends.empty:
    for _, row in data.daily_trends.iterrows():
      daily_records.append({
        "date": row["Date"].strftime("%Y-%m-%d") if pd.notna(row["Date"]) else None,
        "sales": float(row["sales"]),
        "tax": float(row.get("tax", 0)),
      })

  receipt_summaries = []
  for r in getattr(data, "receipts", []) or []:
    receipt_summaries.append({
      "id": r.get("id"),
      "vendor_name": r.get("vendor_name"),
      "transaction_date": r.get("transaction_date"),
      "total_amount": r.get("total_amount"),
      "category": r.get("category"),
      "pl_category": r.get("pl_category"),
      "currency": r.get("currency", "AED"),
    })

  return _json_safe({
    "company_name": data.company_name,
    "ytd_summary": data.ytd_summary or {
      "ytd_revenue": 0,
      "ytd_gross_profit": 0,
      "ytd_total_expenses": 0,
      "ytd_net_profit": 0,
      "ytd_operating_margin": 0,
      "ytd_cogs": 0,
      "ytd_operating_expenses": 0,
    },
    "pl_monthly": pl_records,
    "pl_display_rows": data.pl_display_rows,
    "months": data.months,
    "expense_breakdown": data.expense_breakdown.to_dict(orient="records")
    if not data.expense_breakdown.empty else [],
    "payment_distribution": data.payment_dist.to_dict(orient="records")
    if not data.payment_dist.empty else [],
    "daily_trends": daily_records,
    "monthly_trends": data.monthly_trends.to_dict(orient="records")
    if not data.monthly_trends.empty else [],
    "alerts": data.alerts,
    "balance_sheet": data.bs_totals,
    "warnings": data.warnings,
    "transaction_count": len(data.sales_df),
    "receipts": receipt_summaries,
    "receipt_count": len(receipt_summaries),
    "receipt_cash_outflow": getattr(data, "receipt_cash_outflow", 0),
  })


@router.get("/health")
def health():
  return {"status": "ok"}


@router.get("/dashboard")
def get_dashboard():
  data = process_data()
  return _serialize_dashboard(data)


@router.post("/dashboard/upload")
async def upload_dashboard(
  sales_file: Optional[UploadFile] = File(None),
  pl_file: Optional[UploadFile] = File(None),
):
  sales_bytes = await sales_file.read() if sales_file else None
  pl_bytes = await pl_file.read() if pl_file else None

  sales_source = io.BytesIO(sales_bytes) if sales_bytes else None
  pl_source = io.BytesIO(pl_bytes) if pl_bytes else None

  data = process_data(sales_source=sales_source, pl_source=pl_source)
  return _serialize_dashboard(data)


@router.post("/categorize")
def categorize(body: dict):
  description = body.get("description", "")
  return categorize_expense(description)


@router.post("/upload-receipt")
async def upload_receipt(file: UploadFile = File(...)):
  """OCR a receipt image — returns editable preview only (human-in-the-loop before save)."""
  image_bytes, filename = await _read_receipt_upload(file)
  try:
    preview = preview_receipt_bytes(image_bytes, filename=filename)
  except RuntimeError as exc:
    raise HTTPException(status_code=500, detail=str(exc)) from exc
  except Exception as exc:  # noqa: BLE001
    raise HTTPException(status_code=500, detail=f"Failed to process receipt: {exc}") from exc

  return _json_safe({"receipt": preview, "dashboard": None})


@router.post("/receipts/confirm")
def confirm_receipt(body: dict):
  """Save user-reviewed (and possibly edited) receipt into P&L / balance sheet."""
  try:
    result = confirm_receipt_record(body)
  except Exception as exc:  # noqa: BLE001
    raise HTTPException(status_code=400, detail=str(exc)) from exc

  try:
    dashboard = _serialize_dashboard(process_data())
  except Exception:
    dashboard = None

  return _json_safe({"receipt": result, "dashboard": dashboard})


async def _read_receipt_upload(file: UploadFile) -> Tuple[bytes, Optional[str]]:
  if not file.filename:
    raise HTTPException(status_code=400, detail="No file provided")

  content_type = (file.content_type or "").lower()
  name_lower = file.filename.lower()
  ok_ext = name_lower.endswith((".jpg", ".jpeg", ".png", ".webp", ".heic", ".pdf"))
  ok_mime = content_type.startswith("image/") or content_type == "application/pdf"
  if content_type and not (ok_mime or ok_ext):
    raise HTTPException(
      status_code=400,
      detail="Unsupported file type. Upload a JPG, PNG, WEBP, or PDF receipt image.",
    )

  image_bytes = await file.read()
  if not image_bytes:
    raise HTTPException(status_code=400, detail="Empty file uploaded")

  if name_lower.endswith(".pdf") or content_type == "application/pdf":
    try:
      from pdf2image import convert_from_bytes
      pages = convert_from_bytes(image_bytes, first_page=1, last_page=1, dpi=200)
      buf = io.BytesIO()
      pages[0].save(buf, format="PNG")
      image_bytes = buf.getvalue()
    except Exception as exc:
      raise HTTPException(
        status_code=400,
        detail="PDF receipts require poppler + pdf2image. Please upload a JPG/PNG photo of the receipt.",
      ) from exc

  return image_bytes, file.filename


@router.post("/receipts/scan")
async def scan_receipt(file: UploadFile = File(...)):
  """Alias for upload-receipt — OCR preview without persisting."""
  return await upload_receipt(file)


@router.get("/receipts")
def list_receipts():
  rows = load_all_receipts()
  return _json_safe({
    "receipts": [
      {
        "id": r.get("id"),
        "vendor_name": r.get("vendor_name"),
        "transaction_date": r.get("transaction_date"),
        "total_amount": r.get("total_amount"),
        "category": r.get("category"),
        "pl_category": r.get("pl_category"),
        "currency": r.get("currency", "AED"),
        "payment_method": r.get("payment_method"),
      }
      for r in rows
    ],
    "count": len(rows),
  })


@router.delete("/receipts/latest")
def delete_latest_receipt(month: Optional[str] = None):
  """Delete the most recently added receipt, optionally filtered by month (e.g. Jul)."""
  from src.config import USE_SUPABASE
  if USE_SUPABASE:
    raise HTTPException(status_code=501, detail="Delete via Supabase not implemented yet")

  from src.data.receipt_store import delete_latest_receipt_for_month, load_receipts_local

  deleted_id: Optional[str] = None
  if month:
    deleted_id = delete_latest_receipt_for_month(month)
  else:
    rows = load_receipts_local()
    if rows:
      rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
      from src.data.receipt_store import delete_receipt_local
      rid = str(rows[0].get("id", ""))
      if rid and delete_receipt_local(rid):
        deleted_id = rid

  if not deleted_id:
    raise HTTPException(status_code=404, detail="No matching receipt to delete")

  return _json_safe({
    "deleted": deleted_id,
    "dashboard": _serialize_dashboard(process_data()),
  })


@router.delete("/receipts/{receipt_id}")
def delete_receipt(receipt_id: str):
  from src.config import USE_SUPABASE
  if USE_SUPABASE:
    raise HTTPException(status_code=501, detail="Delete via Supabase not implemented yet")
  from src.data.receipt_store import delete_receipt_local
  if not delete_receipt_local(receipt_id):
    raise HTTPException(status_code=404, detail="Receipt not found")
  return _json_safe({"deleted": receipt_id, "dashboard": _serialize_dashboard(process_data())})


@router.get("/export/excel")
def export_excel():
  data = process_data()
  content = export_to_excel(
    data.pl_df, data.sales_df, data.expense_breakdown,
    data.ytd_summary, data.pl_display_rows,
  )
  return StreamingResponse(
    io.BytesIO(content),
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    headers={"Content-Disposition": "attachment; filename=arcus_financial_report.xlsx"},
  )


@router.get("/export/pdf")
def export_pdf():
  data = process_data()
  content = export_to_pdf(data.ytd_summary, data.pl_df, data.company_name)
  return Response(
    content=content,
    media_type="application/pdf",
    headers={"Content-Disposition": "attachment; filename=arcus_financial_report.pdf"},
  )


app.include_router(router)
