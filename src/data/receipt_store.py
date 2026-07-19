"""Local filesystem persistence for OCR receipt transactions.

Used when Supabase is not configured. Files live under data/receipts/.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import DATA_DIR

RECEIPTS_DIR = DATA_DIR / "receipts"


def _ensure_dir() -> Path:
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    return RECEIPTS_DIR


def save_receipt_local(record: dict[str, Any]) -> dict[str, Any]:
    """Persist a receipt dict as JSON and return the stored record with id."""
    _ensure_dir()
    receipt_id = record.get("id") or str(uuid.uuid4())
    stored = {
        **record,
        "id": receipt_id,
        "created_at": record.get("created_at") or datetime.utcnow().isoformat() + "Z",
    }
    path = RECEIPTS_DIR / f"{receipt_id}.json"
    path.write_text(json.dumps(stored, indent=2, default=str), encoding="utf-8")
    return stored


def load_receipts_local() -> list[dict[str, Any]]:
    """Load all locally stored receipts."""
    if not RECEIPTS_DIR.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(RECEIPTS_DIR.glob("*.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return rows


def delete_receipt_local(receipt_id: str) -> bool:
    """Delete a locally stored receipt JSON file."""
    path = RECEIPTS_DIR / f"{receipt_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def delete_latest_receipt_for_month(month_abbr: str) -> str | None:
    """Delete the most recently created receipt for a calendar month (e.g. Jul). Returns id or None."""
    from datetime import datetime

    rows = load_receipts_local()
    if not rows:
        return None

    target = month_abbr.strip()[:3].title()
    matching = []
    for row in rows:
        tx = row.get("transaction_date") or ""
        try:
            m = datetime.strptime(str(tx)[:10], "%Y-%m-%d").strftime("%b")
        except ValueError:
            continue
        if m == target:
            matching.append(row)

    if not matching:
        return None

    matching.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    rid = str(matching[0].get("id", ""))
    if rid and delete_receipt_local(rid):
        return rid
    return None
