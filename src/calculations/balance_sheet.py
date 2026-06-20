"""Balance sheet calculations and display."""

from __future__ import annotations

from src.data.validator import clean_numeric


def compute_balance_sheet_totals(bs_data: dict, net_profit_ytd: float = 0) -> dict:
    """Compute balance sheet totals with retained earnings from P&L."""
    assets = bs_data.get("assets", [])
    liabilities = bs_data.get("liabilities", [])

    total_assets = sum(
        clean_numeric(a.get("amount", 0)) for a in assets if a.get("amount") is not None
    )
    total_liabilities = sum(
        clean_numeric(l.get("amount", 0))
        for l in liabilities
        if l.get("amount") is not None
        and "equity" not in l.get("item", "").lower()
        and "capital" not in l.get("item", "").lower()
        and "retained" not in l.get("item", "").lower()
    )

    shareholders_equity = 0.0
    for item in liabilities:
        label = item.get("item", "").lower()
        if "shareholders equity" in label or "common stock" in label or label == "capital":
            shareholders_equity += clean_numeric(item.get("amount", 0))

    retained_earnings = net_profit_ytd

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "shareholders_equity": shareholders_equity,
        "retained_earnings": retained_earnings,
        "total_equity": shareholders_equity + retained_earnings,
        "assets": assets,
        "liabilities": liabilities,
    }
