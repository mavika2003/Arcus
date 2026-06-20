"""Plotly chart builders with FORGE dark theme."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.config import FORGE_COLORS, CHART_COLORS

PLOTLY_TEMPLATE = dict(
    paper_bgcolor=FORGE_COLORS["bg"],
    plot_bgcolor=FORGE_COLORS["surface"],
    font=dict(family="JetBrains Mono, monospace", color=FORGE_COLORS["text_muted"], size=11),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(
        gridcolor=FORGE_COLORS["border"],
        linecolor=FORGE_COLORS["border"],
        zerolinecolor=FORGE_COLORS["border"],
    ),
    yaxis=dict(
        gridcolor=FORGE_COLORS["border"],
        linecolor=FORGE_COLORS["border"],
        zerolinecolor=FORGE_COLORS["border"],
    ),
)


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_TEMPLATE)
    return fig


def create_trend_chart(
    data: pd.DataFrame,
    view: str = "Daily",
) -> go.Figure:
    """Create sales vs expenses trend line chart."""
    fig = go.Figure()

    if view == "Daily" and "Date" in data.columns:
        fig.add_trace(go.Scatter(
            x=data["Date"], y=data["sales"],
            name="Sales", mode="lines",
            line=dict(color=FORGE_COLORS["accent"], width=2),
            fill="tozeroy",
            fillcolor="rgba(255,87,34,0.08)",
        ))
        if "tax" in data.columns:
            fig.add_trace(go.Scatter(
                x=data["Date"], y=data["tax"],
                name="Tax", mode="lines",
                line=dict(color=FORGE_COLORS["text_muted"], width=1, dash="dot"),
            ))
        fig.update_layout(title="Daily Sales Trend", xaxis_title="", yaxis_title="Amount ($)")
    else:
        fig.add_trace(go.Bar(
            x=data["Month"], y=data["net_sales"],
            name="Revenue", marker_color=FORGE_COLORS["accent"],
        ))
        fig.add_trace(go.Bar(
            x=data["Month"], y=data["total_expenses"],
            name="Expenses", marker_color=FORGE_COLORS["text_muted"],
        ))
        fig.add_trace(go.Scatter(
            x=data["Month"], y=data["net_profit"],
            name="Net Profit", mode="lines+markers",
            line=dict(color=FORGE_COLORS["green"], width=2),
            marker=dict(size=6),
        ))
        fig.update_layout(
            title="Monthly Sales vs Expenses",
            barmode="group", xaxis_title="", yaxis_title="Amount ($)",
        )

    return _apply_theme(fig)


def create_expense_pie(expense_df: pd.DataFrame) -> go.Figure:
    """Create expense breakdown donut chart."""
    if expense_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No expense data", showarrow=False,
                           font=dict(size=14, color=FORGE_COLORS["text_muted"]))
        return _apply_theme(fig)

    fig = go.Figure(go.Pie(
        labels=expense_df["category"],
        values=expense_df["amount"],
        hole=0.55,
        marker=dict(colors=CHART_COLORS[:len(expense_df)]),
        textinfo="label+percent",
        textfont=dict(size=10, color=FORGE_COLORS["text"]),
        hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(title="Expense Breakdown", showlegend=False)
    return _apply_theme(fig)


def create_expense_bar(expense_df: pd.DataFrame) -> go.Figure:
    """Create horizontal expense breakdown bar chart."""
    if expense_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No expense data", showarrow=False,
                           font=dict(size=14, color=FORGE_COLORS["text_muted"]))
        return _apply_theme(fig)

    sorted_df = expense_df.sort_values("amount", ascending=True)
    colors = [FORGE_COLORS["accent"] if i == len(sorted_df) - 1 else FORGE_COLORS["border"]
              for i in range(len(sorted_df))]

    fig = go.Figure(go.Bar(
        x=sorted_df["amount"],
        y=sorted_df["category"],
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(title="Expense Categories", xaxis_title="Amount ($)", yaxis_title="")
    return _apply_theme(fig)


def create_sales_distribution(payment_df: pd.DataFrame) -> go.Figure:
    """Create sales by payment mode chart."""
    if payment_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No payment data", showarrow=False,
                           font=dict(size=14, color=FORGE_COLORS["text_muted"]))
        return _apply_theme(fig)

    fig = go.Figure(go.Bar(
        x=payment_df["mode"],
        y=payment_df["amount"],
        marker=dict(
            color=[FORGE_COLORS["accent"], FORGE_COLORS["green"], "#60a5fa"][:len(payment_df)],
        ),
        hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(title="Sales by Payment Mode", xaxis_title="", yaxis_title="Amount ($)")
    return _apply_theme(fig)


def create_pl_waterfall(pl_df: pd.DataFrame) -> go.Figure:
    """Create a waterfall chart for P&L flow."""
    if pl_df.empty:
        return _apply_theme(go.Figure())

    totals = {
        "Revenue": pl_df["net_sales"].sum(),
        "COGS": -pl_df["cogs"].sum(),
        "Op. Expenses": -pl_df["operating_expenses"].sum(),
        "Tax": -pl_df["tax"].sum() if "tax" in pl_df.columns else 0,
        "Net Profit": pl_df["net_profit"].sum(),
    }

    fig = go.Figure(go.Waterfall(
        x=list(totals.keys()),
        y=list(totals.values()),
        connector=dict(line=dict(color=FORGE_COLORS["border"])),
        increasing=dict(marker=dict(color=FORGE_COLORS["green"])),
        decreasing=dict(marker=dict(color=FORGE_COLORS["red"])),
        totals=dict(marker=dict(color=FORGE_COLORS["accent"])),
    ))
    fig.update_layout(title="P&L Waterfall (YTD)", showlegend=False)
    return _apply_theme(fig)
