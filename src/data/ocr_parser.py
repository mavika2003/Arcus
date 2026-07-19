"""Tesseract-based receipt OCR and structured field extraction."""

from __future__ import annotations

import logging
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from io import BytesIO
from typing import Any

from src.services.categorizer import categorize_expense

logger = logging.getLogger(__name__)

_HEIF_REGISTERED = False


@dataclass
class ReceiptLineItem:
    name: str
    quantity: float = 1.0
    unit_price: float | None = None
    amount: float | None = None
    barcode: str | None = None


@dataclass
class ParsedReceipt:
    vendor_name: str | None = None
    transaction_date: str | None = None  # ISO YYYY-MM-DD
    total_amount: float | None = None
    currency: str = "AED"
    tax_amount: float | None = None
    taxable_amount: float | None = None
    payment_method: str | None = None
    category: str = "Uncategorized"
    category_confidence: float = 0.0
    description: str | None = None
    line_items: list[ReceiptLineItem] = field(default_factory=list)
    raw_text: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# Receipt signals used to score OCR attempts
_OCR_KEYWORDS = re.compile(
    r"bill\s*amount|tax\s*invoice|supermarket|trn|visa|master|"
    r"taxable|fruits|vegetables|milk|total|dubai|mankhool",
    re.IGNORECASE,
)

_VENDOR_HINTS = re.compile(
    r"(supermarket|hypermarket|restaurant|families|llc|l\.l\.c|"
    r"grocery|trading|star|maya|carrefour|lulu|spinneys|minimart)",
    re.IGNORECASE,
)

_HEADER_SKIP = re.compile(
    r"^(tax\s*invoice|trn|tel|phone|manager|dubai|uae|llc|branch|"
    r"cashier|till|trans|invoice|bill\s*no|clerk|machine|m#|admin|"
    r"thank|visit|keep\s*bill|no\s*cash|product|qty|price|amount|"
    r"barcode|rate|taxable|tax\s*amt|date|time|bill#)",
    re.IGNORECASE,
)


def _parse_amount(raw: str) -> float | None:
    try:
        return float(raw.replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _normalize_year(year: int) -> int:
    return 2000 + year if year < 100 else year


def _parse_date_text(text: str) -> date | None:
    """Parse common UAE receipt date formats."""
    patterns = [
        # 01-Jul-2026, 01/Jul/2026
        re.compile(
            r"\b(\d{1,2})[\-/]([A-Za-z]{3,9})[\-/](\d{2,4})\b",
            re.IGNORECASE,
        ),
        # Date: 01-Jul-2026
        re.compile(
            r"date\s*[:\-]?\s*(\d{1,2})[\-/]([A-Za-z]{3,9})[\-/](\d{2,4})",
            re.IGNORECASE,
        ),
        # 02/07/2026 DD/MM/YYYY
        re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            g1, g2, g3 = match.group(1), match.group(2), match.group(3)
            try:
                if g2.isalpha():
                    month = _MONTH_MAP.get(g2.lower()[:3])
                    if not month:
                        continue
                    return date(_normalize_year(int(g3)), month, int(g1))
                a, b, c = int(g1), int(g2), _normalize_year(int(g3))
                if a > 12:
                    return date(c, b, a)
                if b > 12:
                    return date(c, a, b)
                return date(c, b, a)
            except (ValueError, TypeError):
                continue
    return None


def _latin_ratio(text: str) -> float:
    if not text:
        return 0.0
    latin = sum(1 for c in text if c.isascii() and (c.isalpha() or c.isdigit() or c in " .,-:$#%&*"))
    return latin / max(len(text), 1)


def _score_ocr_text(text: str) -> int:
    if not text or not text.strip():
        return 0
    score = len(_OCR_KEYWORDS.findall(text)) * 10
    score += int(_latin_ratio(text) * 50)
    if re.search(r"\d+\.\d{2}", text):
        score += 5
    if re.search(r"bill\s*amount", text, re.I):
        score += 20
    if re.search(r"supermarket|families", text, re.I):
        score += 15
    return score


def _is_constrained_runtime() -> bool:
    """Render and similar hosts have less RAM — use a lighter OCR path."""
    return bool(os.getenv("RENDER") or os.getenv("ARCUS_FAST_OCR"))


def _register_heif_opener() -> bool:
    global _HEIF_REGISTERED
    if _HEIF_REGISTERED:
        return True
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        _HEIF_REGISTERED = True
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("HEIF opener unavailable: %s", exc)
        return False


def _find_tesseract_binary() -> str | None:
    """Locate a working Tesseract binary (Docker, Homebrew, or PATH)."""
    import subprocess

    candidates: list[str] = []
    env_cmd = (os.getenv("TESSERACT_CMD") or "").strip()
    if env_cmd:
        candidates.append(env_cmd)

    which = shutil.which("tesseract")
    if which:
        candidates.append(which)

    candidates.extend([
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ])

    seen: set[str] = set()
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)
        if not os.path.isfile(path) or not os.access(path, os.X_OK):
            continue
        try:
            subprocess.run(
                [path, "--version"],
                capture_output=True,
                check=True,
                timeout=10,
            )
            return path
        except Exception:
            continue
    return None


def check_ocr_runtime() -> dict[str, Any]:
    """Report whether OCR dependencies are available (for /health)."""
    tesseract_path = _find_tesseract_binary()
    heif = _register_heif_opener()
    ok = bool(tesseract_path)
    detail = None
    if not ok:
        on_render = bool(os.getenv("RENDER"))
        in_docker = os.path.exists("/.dockerenv")
        if on_render and not in_docker:
            detail = (
                "Render is using Native Python (not Docker). Tesseract requires Docker. "
                "Fix: Render Dashboard → your API service → Settings → set Language/Runtime "
                "to Docker, Dockerfile Path = ./Dockerfile, clear any custom Start Command, "
                "then Manual Deploy (clear build cache)."
            )
        else:
            detail = (
                "Tesseract binary not found. Deploy with Docker (see Dockerfile + render.yaml) "
                "or set TESSERACT_CMD to the tesseract binary path."
            )
    return {
        "available": ok,
        "tesseract": tesseract_path,
        "heif": heif,
        "docker": os.path.exists("/.dockerenv"),
        "render": bool(os.getenv("RENDER")),
        "detail": detail,
    }


def _configure_tesseract() -> str:
    import pytesseract

    tesseract_cmd = _find_tesseract_binary()
    if not tesseract_cmd:
        raise RuntimeError(
            "Tesseract is not installed on the server. "
            "On Render: set the web service Runtime to Docker and redeploy "
            "(Dockerfile installs tesseract-ocr). "
            "Or set TESSERACT_CMD=/usr/bin/tesseract in environment variables."
        )
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    return tesseract_cmd


def _load_image_from_bytes(image_bytes: bytes):
    """Open receipt bytes as a PIL image (JPEG/PNG/WEBP/HEIC)."""
    from PIL import Image, UnidentifiedImageError

    _register_heif_opener()

    if not image_bytes:
        raise ValueError("Empty image file")

    try:
        image = Image.open(BytesIO(image_bytes))
        image.load()
    except UnidentifiedImageError as exc:
        header = image_bytes[:32]
        if b"ftyp" in header and any(
            marker in header for marker in (b"heic", b"heix", b"mif1", b"hevc")
        ):
            raise ValueError(
                "HEIC/HEIF photos are not supported on this server. "
                "On iPhone: Settings → Camera → Formats → Most Compatible, then retake, "
                "or export/save the photo as JPEG before uploading."
            ) from exc
        raise ValueError(
            "Could not read image. Upload a JPG, PNG, or WEBP photo of the receipt."
        ) from exc
    except Exception as exc:
        raise ValueError(f"Could not read image: {exc}") from exc

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    w, h = image.size
    max_edge = 2400 if _is_constrained_runtime() else 3200
    if max(w, h) > max_edge:
        scale = max_edge / max(w, h)
        image = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    return image


def _preprocess_variants(image) -> list:
    """Generate multiple preprocessed images for OCR attempts."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    variants = []
    w, h = image.size
    if max(w, h) < 1600:
        scale = 1600 / max(w, h)
        image = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)

    # Standard contrast
    v1 = ImageEnhance.Contrast(gray).enhance(2.0)
    v1 = v1.filter(ImageFilter.SHARPEN)
    variants.append(v1)

    if not _is_constrained_runtime():
        # High contrast + threshold (thermal receipt friendly)
        v2 = ImageEnhance.Contrast(gray).enhance(2.8)
        v2 = v2.point(lambda p: 255 if p > 140 else 0)
        variants.append(v2)

        # Slightly softer — helps when photo is overexposed
        v3 = ImageEnhance.Brightness(gray).enhance(1.1)
        v3 = ImageEnhance.Contrast(v3).enhance(1.8)
        variants.append(v3)

    return variants


def extract_text_from_image(image_bytes: bytes) -> str:
    """Run Tesseract OCR with multiple preprocess + config attempts; pick best text."""
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR dependencies missing. Install pillow and pytesseract "
            "(and the system Tesseract binary)."
        ) from exc

    _configure_tesseract()
    image = _load_image_from_bytes(image_bytes)

    # Receipt photos are often rotated — try original + 90° if tall
    orientations = [image]
    if not _is_constrained_runtime() and image.height > image.width * 1.2:
        orientations.append(image.rotate(90, expand=True))

    configs = [("eng", "--oem 3 --psm 6")]
    if not _is_constrained_runtime():
        configs.extend([
            ("eng", "--oem 3 --psm 4"),   # single column
            ("eng", "--oem 3 --psm 11"),  # sparse text
        ])

    best_text = ""
    best_score = -1
    last_error: Exception | None = None

    for oriented in orientations:
        for variant in _preprocess_variants(oriented):
            for lang, config in configs:
                try:
                    text = pytesseract.image_to_string(variant, lang=lang, config=config)
                    score = _score_ocr_text(text)
                    if score > best_score:
                        best_score = score
                        best_text = text
                    if _is_constrained_runtime() and score >= 25:
                        return best_text
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    logger.warning("OCR attempt failed (%s %s): %s", lang, config, exc)

    if not best_text.strip() and last_error:
        raise RuntimeError(
            f"Tesseract OCR failed: {last_error}. "
            "Ensure tesseract-ocr is installed on the server."
        )
    return best_text


def _guess_vendor(lines: list[str]) -> str | None:
    """Pick the store name from header lines — prefer English supermarket names."""
    candidates: list[tuple[int, str]] = []

    for i, line in enumerate(lines[:20]):
        raw = line.strip()
        if len(raw) < 4:
            continue
        if _HEADER_SKIP.search(raw):
            continue
        if re.fullmatch(r"[\d\s./\-#*]+", raw):
            continue

        # Skip lines that are mostly non-Latin (Arabic OCR noise)
        latin_chars = sum(1 for c in raw if c.isascii() and c.isalpha())
        if latin_chars < 4 and not _VENDOR_HINTS.search(raw):
            continue

        cleaned = re.sub(r"[^\w\s&.'\-]", " ", raw).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if len(cleaned) < 4:
            continue

        score = 0
        if _VENDOR_HINTS.search(cleaned):
            score += 30
        if cleaned.isupper() or cleaned.upper() == cleaned:
            score += 10
        if i < 5:
            score += 8 - i
        score += min(len(cleaned), 40)
        candidates.append((score, cleaned))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1][:120]


def _extract_total(text: str) -> float | None:
    """Extract bill total — prioritize labelled totals over random numbers."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # 1. Bill Amount on same line (UAE tax invoices)
    for line in lines:
        m = re.search(
            r"bill\s*amount\s*[:\-]?\s*(?:AED\s*)?([\d,]+\.\d{2})",
            line, re.IGNORECASE,
        )
        if m:
            return _parse_amount(m.group(1))

    # 2. Bill Amount on next line
    for i, line in enumerate(lines):
        if re.search(r"bill\s*amount", line, re.IGNORECASE):
            for j in range(i, min(i + 3, len(lines))):
                m = re.search(r"([\d,]+\.\d{2})\s*$", lines[j])
                if m:
                    val = _parse_amount(m.group(1))
                    if val and val > 1:
                        return val

    # 3. VISA / card payment line total
    for line in lines:
        if re.search(r"\*{2,}\s*visa|visa\s*payment|magnati|master\s*card", line, re.I):
            amounts = re.findall(r"([\d,]+\.\d{2})", line)
            if amounts:
                return _parse_amount(amounts[-1])

    # 4. Other labelled totals
    label_patterns = [
        r"grand\s*total\s*[:\-]?\s*(?:AED\s*)?([\d,]+\.\d{2})",
        r"total\s*amount\s*[:\-]?\s*(?:AED\s*)?([\d,]+\.\d{2})",
        r"net\s*total\s*[:\-]?\s*(?:AED\s*)?([\d,]+\.\d{2})",
        r"amount\s*due\s*[:\-]?\s*(?:AED\s*)?([\d,]+\.\d{2})",
    ]
    found: list[float] = []
    for pat in label_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            val = _parse_amount(m.group(1))
            if val and val > 0:
                found.append(val)

    # 5. Last resort: largest amount >= 5 near bottom third (avoid unit prices)
    if not found:
        bottom = "\n".join(lines[len(lines) * 2 // 3:])
        for m in re.finditer(r"\b([\d,]+\.\d{2})\b", bottom):
            val = _parse_amount(m.group(1))
            if val and val >= 5:
                found.append(val)

    return max(found) if found else None


def _is_product_name_line(line: str) -> bool:
    if not line or len(line) < 3:
        return False
    cleaned = re.sub(r"\(tax[^)]*\)", "", line, flags=re.I).strip()
    cleaned = re.sub(r"tax\s*\d+%?", "", cleaned, flags=re.I).strip()
    if not cleaned or re.fullmatch(r"[\d\s.,\-]+", cleaned):
        return False
    if re.search(r"thank|visit|visa|bill|qty|price|amount|product", cleaned, re.I):
        return False
    return bool(re.search(r"[A-Za-z]{2,}", cleaned))


def _clean_product_name(line: str) -> str:
    name = re.sub(r"\(tax[^)]*\)", "", line, flags=re.I).strip()
    name = re.sub(r"tax\s*\d+%?", "", name, flags=re.I).strip()
    return re.sub(r"\s+", " ", name)[:80]


def _parse_item_block(barcode: str, block_lines: list[str]) -> ReceiptLineItem | None:
    """Parse lines following a barcode into one line item."""
    decimal_amounts: list[float] = []
    qty = 1.0
    names: list[str] = []
    pending_int: list[str] = []

    for raw in block_lines:
        line = raw.strip()
        if not line or line.startswith("(Tax"):
            continue
        if re.search(r"visa|bill\s*amount|taxable|payment", line, re.I):
            break

        if re.fullmatch(r"\d+\.\d{2}", line):
            val = float(line)
            if val > 100:  # skip bill totals leaking into block
                continue
            decimal_amounts.append(val)
            pending_int = []
        elif re.fullmatch(r"\d+\.\d{3}", line):
            qty = float(line)
        elif re.fullmatch(r"\d{1,2}", line):
            val = int(line)
            if not decimal_amounts and not pending_int:
                if val <= 9:
                    qty = float(val)
                else:
                    pending_int.append(line)
            elif len(pending_int) == 1 and len(line) == 2:
                merged = float(f"{pending_int[0]}.{line}")
                decimal_amounts.append(merged)
                pending_int = []
            else:
                pending_int.append(line)
        elif _is_product_name_line(line):
            names.append(_clean_product_name(line))
            pending_int = []
        else:
            pending_int = []

    if not decimal_amounts:
        return None

    amount = decimal_amounts[-1]
    unit_price = decimal_amounts[0] if len(decimal_amounts) >= 2 else amount
    if len(decimal_amounts) >= 2 and decimal_amounts[-2] == decimal_amounts[-1]:
        unit_price = amount

    name = names[0] if names else f"Item {barcode[-4:]}"

    return ReceiptLineItem(
        name=name,
        quantity=qty,
        unit_price=unit_price,
        amount=amount,
        barcode=barcode,
    )


def _starts_new_item(line: str) -> bool:
    """True if line begins a new product (barcode row)."""
    return bool(re.match(r"^\d{8,14}\b", line))


def _extract_line_items(text: str) -> list[ReceiptLineItem]:
    """Extract product lines from UAE supermarket receipts (multi-line OCR tolerant)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    items: list[ReceiptLineItem] = []
    seen: set[str] = set()

    skip_zone = re.compile(
        r"taxable\s*amount|bill\s*amount|bal\.?\s*amount|thank\s*you|keep\s*bill|"
        r"no\s*cash|tax\s*#|rate\s*taxable|^\*{2,}\s*visa",
        re.I,
    )

    i = 0
    while i < len(lines):
        line = lines[i]

        if skip_zone.search(line):
            i += 1
            continue

        barcode: str | None = None
        extra_block: list[str] = []

        combo = re.match(r"^(\d{8,14})\s+(\d+(?:\.\d+)?)$", line)
        if combo:
            barcode, qty_line = combo.groups()
            extra_block = [qty_line]
            i += 1
        elif re.fullmatch(r"\d{8,14}", line):
            barcode = line
            i += 1
        else:
            i += 1
            continue

        block: list[str] = list(extra_block)
        while i < len(lines) and len(block) < 10:
            if _starts_new_item(lines[i]):
                break
            if skip_zone.search(lines[i]):
                break
            block.append(lines[i])
            i += 1

        item = _parse_item_block(barcode, block)
        if item:
            key = f"{barcode}:{item.amount}"
            if key not in seen:
                seen.add(key)
                items.append(item)

        if len(items) >= 40:
            break

    return items


def _line_items_subtotal(items: list[ReceiptLineItem]) -> float:
    return sum(float(i.amount or 0) for i in items)


def parse_receipt_text(raw_text: str) -> ParsedReceipt:
    """Parse OCR text into structured receipt fields."""
    receipt = ParsedReceipt(raw_text=raw_text or "")
    if not raw_text or not raw_text.strip():
        receipt.warnings.append("OCR returned empty text")
        return receipt

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    receipt.vendor_name = _guess_vendor(lines)

    parsed_date = _parse_date_text(raw_text)
    if parsed_date:
        receipt.transaction_date = parsed_date.isoformat()

    receipt.total_amount = _extract_total(raw_text)

    m = re.search(
        r"tax\s*amount\s*[:\-]?\s*(?:AED\s*)?([\d,]+\.\d{2})",
        raw_text, re.IGNORECASE,
    )
    if m:
        receipt.tax_amount = _parse_amount(m.group(1))

    m = re.search(
        r"taxable\s*amount\s*[:\-]?\s*(?:AED\s*)?([\d,]+\.\d{2})",
        raw_text, re.IGNORECASE,
    )
    if m:
        receipt.taxable_amount = _parse_amount(m.group(1))

    for pat in [
        re.compile(r"\*{2,}\s*(visa)", re.I),
        re.compile(r"\b(visa|master\s*card|mastercard|magnati|eft|cash)\b", re.I),
    ]:
        pay = pat.search(raw_text)
        if pay:
            receipt.payment_method = pay.group(1).upper().replace(" ", "")
            break

    if re.search(r"\bAED\b|\bDhs\.?\b", raw_text, re.IGNORECASE):
        receipt.currency = "AED"

    receipt.line_items = _extract_line_items(raw_text)

    # Reconcile total with line items when bill total missing
    items_sum = _line_items_subtotal(receipt.line_items)
    if receipt.total_amount is None and items_sum > 0:
        receipt.total_amount = round(items_sum, 2)
    if receipt.line_items and receipt.total_amount:
        diff = abs(items_sum - float(receipt.total_amount))
        if diff > 0.05 and items_sum > 0:
            receipt.warnings.append(
                f"Line items sum ({items_sum:.2f}) differs from bill total "
                f"({receipt.total_amount:.2f}) — verify products"
            )

    desc_parts: list[str] = []
    if receipt.vendor_name:
        desc_parts.append(receipt.vendor_name)
    for item in receipt.line_items[:6]:
        desc_parts.append(item.name)
    if re.search(
        r"supermarket|hypermarket|grocery|fruits?\s*&?\s*vegetables?|"
        r"milk|rawabi|parle|britannia",
        raw_text, re.I,
    ):
        desc_parts.append("supermarket grocery purchases")
    receipt.description = " ".join(desc_parts) or raw_text[:300]

    cat = categorize_expense(receipt.description)
    receipt.category = cat["category"]
    receipt.category_confidence = float(cat.get("confidence", 0))

    if receipt.total_amount is None:
        receipt.warnings.append("Could not detect total amount — please verify")
    if receipt.transaction_date is None:
        receipt.transaction_date = datetime.utcnow().date().isoformat()
        receipt.warnings.append("Could not detect date — defaulted to today")
    if not receipt.vendor_name:
        receipt.warnings.append("Could not detect vendor name")
    if not receipt.line_items:
        receipt.warnings.append("No product line items detected — add them manually below")
    if receipt.category == "Uncategorized":
        receipt.warnings.append("Low confidence categorization — check P&L category")

    return receipt


def process_receipt_image(image_bytes: bytes) -> ParsedReceipt:
    """Full OCR pipeline: image bytes → structured receipt."""
    text = extract_text_from_image(image_bytes)
    return parse_receipt_text(text)
