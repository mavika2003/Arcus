"""Expense anomaly detection and alerting."""

from __future__ import annotations

import pandas as pd

ALERT_THRESHOLD_PCT = 50.0
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def detect_expense_anomalies(
    recurring_costs: pd.DataFrame,
    threshold_pct: float = ALERT_THRESHOLD_PCT,
) -> list[dict]:
    """Flag expense categories with month-over-month jumps above threshold."""
    if recurring_costs.empty:
        return []

    alerts = []
    for category in recurring_costs["category"].unique():
        cat_data = recurring_costs[recurring_costs["category"] == category].copy()
        cat_data["month"] = pd.Categorical(
            cat_data["month"], categories=MONTH_ORDER, ordered=True
        )
        cat_data = cat_data.sort_values("month")
        months = cat_data["month"].astype(str).tolist()
        amounts = cat_data["amount"].tolist()

        for i in range(1, len(amounts)):
            prev, curr = amounts[i - 1], amounts[i]
            if prev == 0 and curr > 0:
                pct_change = 100.0
            elif prev == 0:
                continue
            else:
                pct_change = ((curr - prev) / abs(prev)) * 100

            if pct_change >= threshold_pct:
                severity = "CRITICAL" if pct_change >= 75 else "WARNING"
                alerts.append({
                    "severity": severity,
                    "category": category,
                    "message": (
                        f"{category} increased {pct_change:.0f}% "
                        f"from {months[i-1]} ({prev:,.0f}) to {months[i]} ({curr:,.0f})"
                    ),
                    "pct_change": round(pct_change, 1),
                    "from_month": months[i - 1],
                    "to_month": months[i],
                    "from_amount": prev,
                    "to_amount": curr,
                })

    return sorted(alerts, key=lambda a: a["pct_change"], reverse=True)


def detect_revenue_anomalies(pl_df: pd.DataFrame, threshold_pct: float = 30.0) -> list[dict]:
    """Flag significant revenue drops month-over-month."""
    if len(pl_df) < 2:
        return []

    alerts = []
    sorted_pl = pl_df.sort_values("Month")
    for i in range(1, len(sorted_pl)):
        prev = sorted_pl.iloc[i - 1]["net_sales"]
        curr = sorted_pl.iloc[i]["net_sales"]
        if prev == 0:
            continue
        pct_change = ((curr - prev) / prev) * 100
        if pct_change <= -threshold_pct:
            alerts.append({
                "severity": "WARNING",
                "category": "Revenue",
                "message": (
                    f"Revenue dropped {abs(pct_change):.0f}% "
                    f"from {sorted_pl.iloc[i-1]['Month']} to {sorted_pl.iloc[i]['Month']}"
                ),
                "pct_change": round(pct_change, 1),
            })
    return alerts


def get_all_alerts(
    recurring_costs: pd.DataFrame,
    pl_df: pd.DataFrame,
) -> list[dict]:
    """Combine all alert types."""
    expense_alerts = detect_expense_anomalies(recurring_costs)
    revenue_alerts = detect_revenue_anomalies(pl_df)
    return expense_alerts + revenue_alerts
