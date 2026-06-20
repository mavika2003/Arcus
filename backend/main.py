"""FastAPI backend for Arcus financial dashboard."""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline import process_data
from src.services.categorizer import categorize_expense
from src.services.export import export_to_excel, export_to_pdf

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

  return _json_safe({
    "company_name": data.company_name,
    "ytd_summary": data.ytd_summary,
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
