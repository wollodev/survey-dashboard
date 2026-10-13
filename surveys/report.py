"""PDF report with ReportLab."""

import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .charts import brand_share_chart, weekly_chart
from .data.analysis import Summary

LINE = colors.HexColor("#e3e2dd")
HEADER_BG = colors.HexColor("#f6f6f4")


def _table(rows: list[list], col_widths: list[float]) -> Table:
    """Table with header row, rules and right-aligned number columns."""
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _chart(png: bytes, width: float) -> Image:
    """Image at a fixed width; the height follows from the aspect ratio."""
    pixel_width, pixel_height = ImageReader(io.BytesIO(png)).getSize()
    return Image(io.BytesIO(png), width=width, height=width * pixel_height / pixel_width)


def _num(value: float | None, digits: int = 0, suffix: str = "") -> str:
    """Formats a number with thousands separators; missing values become a dash."""
    if value is None:
        return "–"
    return f"{value:,.{digits}f}{suffix}"


def build_report(
    title: str, uploaded_at: datetime, summary: Summary, created_at: datetime | None = None
) -> bytes:
    """Builds the report and returns the finished PDF as bytes."""
    created_at = created_at or datetime.now().astimezone()
    styles = getSampleStyleSheet()
    k = summary["kpis"]

    story = [
        Paragraph(f"Survey report: {escape(title)}", styles["Title"]),
        Paragraph(
            f"Uploaded on {uploaded_at:%Y-%m-%d}, created on {created_at:%Y-%m-%d %H:%M}",
            styles["Normal"],
        ),
        Spacer(1, 0.6 * cm),
        Paragraph("Key figures", styles["Heading2"]),
        _table(
            [
                ["Metric", "Value"],
                ["Responses", _num(k["responses"])],
                ["Satisfaction (1–5)", _num(k["avg_satisfaction"], 2)],
                ["Net Promoter Score", _num(k["nps"], 1)],
                ["Monthly spend (avg.)", _num(k["avg_monthly_spend"], 2, " €")],
                ["Would subscribe", _num(k["subscribe_rate"], 1, " %")],
            ],
            col_widths=[7 * cm, 4 * cm],
        ),
        Spacer(1, 0.4 * cm),
        Paragraph("Brands", styles["Heading2"]),
        _chart(brand_share_chart(summary["brands"]), width=16 * cm),
        _table(
            [["Brand", "Responses", "Share", "Satisfaction", "NPS"]]
            + [
                [
                    b["brand"],
                    _num(b["responses"]),
                    _num(b["share"], 1, " %"),
                    _num(b["avg_satisfaction"], 2),
                    _num(b["nps"], 1),
                ]
                for b in summary["brands"]
            ],
            col_widths=[5 * cm, 2.8 * cm, 2.6 * cm, 2.8 * cm, 2.4 * cm],
        ),
        Spacer(1, 0.4 * cm),
        # KeepTogether: never split heading and chart across two pages
        KeepTogether(
            [
                Paragraph("Responses per week", styles["Heading2"]),
                _chart(weekly_chart(summary["weekly"]), width=16 * cm),
            ]
        ),
    ]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"Survey report: {title}",
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
    return buffer.getvalue()
