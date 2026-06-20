"""Export clean financial data to Excel and PDF."""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd


def export_to_excel(
    pl_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    expense_breakdown: pd.DataFrame,
    ytd_summary: dict,
    pl_display_rows: list[dict] | None = None,
) -> bytes:
    """Export financial data to an Excel workbook."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        summary_df = pd.DataFrame([{
            "Metric": k.replace("ytd_", "").replace("_", " ").title(),
            "Value": v,
        } for k, v in ytd_summary.items()])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        if pl_display_rows:
            pl_export = pd.DataFrame(pl_display_rows)
            pl_export.to_excel(writer, sheet_name="P&L Statement", index=False)
        else:
            pl_df.to_excel(writer, sheet_name="P&L Monthly", index=False)

        sales_export = sales_df.copy()
        if "Date" in sales_export.columns:
            sales_export["Date"] = sales_export["Date"].dt.strftime("%Y-%m-%d")
        sales_export.to_excel(writer, sheet_name="Daily Sales", index=False)

        if not expense_breakdown.empty:
            expense_breakdown.to_excel(writer, sheet_name="Expense Breakdown", index=False)

    output.seek(0)
    return output.getvalue()


def export_to_pdf(
    ytd_summary: dict,
    pl_df: pd.DataFrame,
    company_name: str = "Sai Dham",
) -> bytes:
    """Export a summary P&L report to PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, topMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"],
        fontSize=18, textColor=colors.HexColor("#ff5722"),
    )
    elements = []

    elements.append(Paragraph(f"{company_name} — Financial Report", title_style))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y')}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 0.3 * inch))

    summary_data = [["Metric", "Value"]]
    for key, val in ytd_summary.items():
        label = key.replace("ytd_", "").replace("_", " ").title()
        if "margin" in key:
            formatted = f"{val:.1f}%"
        else:
            formatted = f"AED {val:,.2f}"
        summary_data.append([label, formatted])

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff5722")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4 * inch))

    if not pl_df.empty:
        elements.append(Paragraph("Monthly P&L", styles["Heading2"]))
        pl_cols = ["Month", "net_sales", "cogs", "gross_profit", "operating_expenses", "net_profit"]
        available = [c for c in pl_cols if c in pl_df.columns]
        pl_data = [["Month", "Revenue", "COGS", "Gross Profit", "Op. Expenses", "Net Profit"][:len(available)]]
        for _, row in pl_df.iterrows():
            pl_data.append([
                str(row[c]) if c == "Month" else f"AED {row[c]:,.0f}"
                for c in available
            ])
        pl_table = Table(pl_data)
        pl_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(pl_table)

    doc.build(elements)
    output.seek(0)
    return output.getvalue()
