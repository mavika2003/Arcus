"""AI-powered expense categorization engine."""

from __future__ import annotations

import re

CATEGORY_RULES: dict[str, list[str]] = {
    "COGS": [
        "flour", "dairy", "grocery", "supermarket", "vegetable", "meat", "fish",
        "spice", "oil", "rice", "pack", "nfpc", "refreshment", "plastic",
        "farsan", "swadesh", "shield gas", "gas", "purchased", "stock",
    ],
    "Utilities": [
        "dewa", "electricity", "water", "wifi", "internet", "du wifi", "utility",
        "power", "gas bill", "electric",
    ],
    "Salaries": [
        "salary", "salaries", "wage", "payroll", "staff pay",
    ],
    "Rent": [
        "rent", "lease", "landlord",
    ],
    "Marketing": [
        "advertising", "marketing", "social media", "promotion", "zomato",
        "talabat", "careem", "noon", "deliveroo",
    ],
    "Office Expenditure": [
        "maintenance", "pest control", "flowers", "knife", "sign board",
        "office", "repair", "cleaning",
    ],
    "Staff Expenses": [
        "tips", "conveyance", "taxi", "visa", "staff food", "uniform",
    ],
    "Sundry Expenses": [
        "settlement", "sundry", "misc", "miscellaneous", "holiday",
    ],
    "Taxes": [
        "tax", "vat", "gst", "filing",
    ],
}


def categorize_expense(description: str) -> dict:
    """Categorize an expense description using keyword matching."""
    if not description or not isinstance(description, str):
        return {"category": "Uncategorized", "confidence": 0.0, "method": "default"}

    desc_lower = description.lower().strip()
    best_category = "Uncategorized"
    best_score = 0

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in desc_lower:
                score = len(keyword) / len(desc_lower) if desc_lower else 0
                if score > best_score or (score == best_score and len(keyword) > 0):
                    best_score = max(score, 0.5)
                    best_category = category

    confidence = min(best_score * 2, 1.0) if best_category != "Uncategorized" else 0.1

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "method": "keyword_match",
        "original": description,
    }


def categorize_batch(descriptions: list[str]) -> list[dict]:
    """Categorize a batch of expense descriptions."""
    return [categorize_expense(d) for d in descriptions]


def suggest_category(description: str) -> str:
    """Quick category suggestion for a single description."""
    return categorize_expense(description)["category"]
