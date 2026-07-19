"""Optional cloud OCR providers (much better quality/speed than free-tier Tesseract).

Set OCR_SPACE_API_KEY on Render for production-quality receipt scans (~2–5s).
Free tier: https://ocr.space/ocrapi (25k requests/month with free key).
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

_OCR_SPACE_URL = "https://api.ocr.space/parse/image"


def cloud_ocr_configured() -> bool:
    return bool((os.getenv("OCR_SPACE_API_KEY") or "").strip())


def extract_text_ocr_space(image_bytes: bytes, filename: str | None = None) -> str:
    """OCR via OCR.space API. Raises RuntimeError on failure."""
    api_key = (os.getenv("OCR_SPACE_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OCR_SPACE_API_KEY is not set")

    if not image_bytes:
        raise ValueError("Empty image")

    # Keep payload under free-tier limits (~1 MB base64)
    payload_b64 = base64.b64encode(image_bytes).decode("ascii")
    if len(payload_b64) > 900_000:
        raise RuntimeError("Image too large for OCR.space free tier — compress and retry")

    name = (filename or "receipt.jpg").rsplit("/", 1)[-1]
    if "." not in name:
        name = f"{name}.jpg"

    form = {
        "apikey": api_key,
        "base64Image": f"data:image/jpeg;base64,{payload_b64}",
        "language": "eng",
        "isOverlayRequired": "false",
        "OCREngine": "2",  # engine 2 is better for receipts / mixed layouts
        "scale": "true",
        "detectOrientation": "true",
        "filetype": name.rsplit(".", 1)[-1].upper(),
    }

    body = "&".join(
        f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in form.items()
    ).encode("utf-8")

    req = urllib.request.Request(
        _OCR_SPACE_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"OCR.space HTTP {exc.code}: {detail}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"OCR.space request failed: {exc}") from exc

    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OCR.space returned invalid JSON") from exc

    if data.get("IsErroredOnProcessing"):
        msgs = data.get("ErrorMessage") or data.get("ErrorDetails") or "unknown error"
        if isinstance(msgs, list):
            msgs = "; ".join(str(m) for m in msgs)
        raise RuntimeError(f"OCR.space error: {msgs}")

    parts: list[str] = []
    for result in data.get("ParsedResults") or []:
        text = (result.get("ParsedText") or "").strip()
        if text:
            parts.append(text)

    text = "\n".join(parts).strip()
    if not text:
        raise RuntimeError("OCR.space returned empty text")

    logger.info("OCR.space extracted %d chars", len(text))
    return text
