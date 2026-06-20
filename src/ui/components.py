"""Reusable Streamlit UI components."""

from __future__ import annotations

import streamlit as st

from src.calculations.financials import format_currency


def render_header(company_name: str = "ARCUS"):
    """Render the FORGE-style dashboard header."""
    st.markdown(f"""
    <div class="forge-header">
        <div>
            <span class="forge-logo">⚙ {company_name}</span>
            <span class="forge-live"><span class="forge-live-dot"></span> LIVE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, sub: str = "", accent: bool = False):
    """Render a single metric card."""
    value_color = "var(--accent)" if accent else "var(--text)"
    st.markdown(f"""
    <div class="forge-metric-card">
        <div class="forge-metric-label">{label}</div>
        <div class="forge-metric-value" style="color:{value_color}">{value}</div>
        {f'<div class="forge-metric-sub">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)


def render_summary_cards(ytd: dict):
    """Render the top financial summary cards row."""
    cols = st.columns(4)
    metrics = [
        ("YTD Revenue", format_currency(ytd["ytd_revenue"]), "Net sales after discounts"),
        ("Total Expenses", format_currency(ytd["ytd_total_expenses"]), "COGS + operating + tax"),
        ("Net Profit", format_currency(ytd["ytd_net_profit"]), "Gross profit − expenses", True),
        ("Operating Margin", f"{ytd['ytd_operating_margin']:.1f}%", "Net profit / revenue"),
    ]
    for col, (label, value, sub, *rest) in zip(cols, metrics):
        with col:
            render_metric_card(label, value, sub, accent=bool(rest))


def render_section(title: str, label: str = ""):
    """Render a section header."""
    label_html = f'<div class="forge-section-label">{label}</div>' if label else ""
    st.markdown(f"""
    {label_html}
    <div class="forge-section-title">{title}</div>
    """, unsafe_allow_html=True)


def render_alert(alert: dict):
    """Render a single alert card."""
    severity = alert.get("severity", "INFO").lower()
    css_class = f"forge-alert forge-alert-{severity}" if severity in ("critical", "warning") else "forge-alert forge-alert-info"
    st.markdown(f"""
    <div class="{css_class}">
        <div class="forge-alert-severity">{alert.get('severity', 'INFO')}</div>
        <div class="forge-alert-message">{alert.get('message', '')}</div>
    </div>
    """, unsafe_allow_html=True)


def render_alerts_panel(alerts: list[dict]):
    """Render the alerts sidebar panel."""
    render_section("Live Alert Feed", "ANOMALY DETECTION")
    if not alerts:
        st.markdown("""
        <div class="forge-alert forge-alert-info">
            <div class="forge-alert-severity">INFO</div>
            <div class="forge-alert-message">No anomalies detected. All expenses within normal range.</div>
        </div>
        """, unsafe_allow_html=True)
        return
    for alert in alerts[:8]:
        render_alert(alert)


def render_pl_table(display_rows: list[dict], months: list[str]):
    """Render the P&L statement table matching Excel format."""
    header_cols = st.columns([3] + [1] * (len(months) + 1))
    with header_cols[0]:
        st.markdown("**Line Item**")
    with header_cols[1]:
        st.markdown("**YTD**")
    for i, m in enumerate(months):
        with header_cols[i + 2]:
            st.markdown(f"**{m}**")

    for row in display_rows:
        if row.get("type") == "section":
            st.markdown(f"---\n**{row['label']}**")
            continue

        cols = st.columns([3] + [1] * (len(months) + 1))
        label = row.get("label", "")
        is_total = any(k in label.lower() for k in ("total", "net profit", "gross profit"))
        weight = "bold" if is_total else "normal"

        with cols[0]:
            st.markdown(f"**{label}**" if is_total else label)
        with cols[1]:
            val = row.get("ytd", 0)
            st.markdown(f"**${val:,.0f}**" if is_total else f"${val:,.0f}")
        for i, m in enumerate(months):
            with cols[i + 2]:
                val = row.get(m, 0)
                st.markdown(f"**${val:,.0f}**" if is_total else f"${val:,.0f}")


def render_balance_sheet(bs_totals: dict):
    """Render balance sheet in two-column layout."""
    col_assets, col_liab = st.columns(2)

    with col_assets:
        render_section("Assets", "BALANCE SHEET")
        for item in bs_totals.get("assets", []):
            amount = item.get("amount")
            amt_str = f"${amount:,.0f}" if amount is not None else "—"
            st.markdown(f"**{item['item']}** — {amt_str}")
        st.markdown(f"---\n**Total Assets: ${bs_totals['total_assets']:,.0f}**")

    with col_liab:
        render_section("Liabilities & Equity")
        for item in bs_totals.get("liabilities", []):
            amount = item.get("amount")
            amt_str = f"${amount:,.0f}" if amount is not None else "—"
            st.markdown(f"**{item['item']}** — {amt_str}")
        st.markdown(f"**Retained Earnings** — ${bs_totals['retained_earnings']:,.0f}")
        st.markdown(f"---\n**Total Equity: ${bs_totals['total_equity']:,.0f}**")


def render_categorizer_ui():
    """Render the AI categorizer input interface."""
    render_section("AI Expense Categorizer", "AUTO-CLASSIFY")
    description = st.text_input(
        "Receipt / expense description",
        placeholder='e.g. "DEWA electricity bill" or "ANWAR FLOUR MILL"',
        key="categorizer_input",
    )
    if description:
        from src.services.categorizer import categorize_expense
        result = categorize_expense(description)
        badge_class = "forge-badge-green" if result["confidence"] > 0.5 else "forge-badge-amber"
        st.markdown(f"""
        <div class="forge-metric-card">
            <div class="forge-metric-label">Suggested Category</div>
            <div class="forge-metric-value" style="font-size:1.25rem">{result['category']}</div>
            <div class="forge-metric-sub">
                Confidence: {result['confidence']*100:.0f}%
                <span class="forge-badge {badge_class}" style="margin-left:0.5rem">{result['method']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
