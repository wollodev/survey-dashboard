"""PDF-Bericht mit ReportLab."""

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

LINE = colors.HexColor("#e3e2dd")
HEADER_BG = colors.HexColor("#f6f6f4")


def _table(rows: list[list], col_widths: list[float]) -> Table:
    """Tabelle mit Kopfzeile, Linien und rechtsbündigen Zahlenspalten."""
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
    """Bild in fester Breite, die Höhe ergibt sich aus dem Seitenverhältnis."""
    pixel_width, pixel_height = ImageReader(io.BytesIO(png)).getSize()
    return Image(io.BytesIO(png), width=width, height=width * pixel_height / pixel_width)


def build_report(
    title: str, uploaded_at: datetime, summary: dict, created_at: datetime | None = None
) -> bytes:
    """Baut den Bericht und gibt das fertige PDF als Bytes zurück."""
    created_at = created_at or datetime.now().astimezone()
    styles = getSampleStyleSheet()
    k = summary["kpis"]

    story = [
        Paragraph(f"Umfrage-Auswertung: {escape(title)}", styles["Title"]),
        Paragraph(
            f"Hochgeladen am {uploaded_at:%d.%m.%Y}, erstellt am {created_at:%d.%m.%Y %H:%M}",
            styles["Normal"],
        ),
        Spacer(1, 0.6 * cm),
        Paragraph("Kennzahlen", styles["Heading2"]),
        _table(
            [
                ["Kennzahl", "Wert"],
                ["Antworten", f"{k['responses']}"],
                ["Zufriedenheit (1–5)", f"{k['avg_satisfaction']:.2f}"],
                ["Net Promoter Score", "–" if k["nps"] is None else f"{k['nps']:.1f}"],
                ["Ausgaben pro Monat (Ø)", f"{k['avg_monthly_spend']:.2f} €"],
                ["Würde ein Abo abschließen", f"{k['subscribe_rate']:.1f} %"],
            ],
            col_widths=[7 * cm, 4 * cm],
        ),
        Spacer(1, 0.4 * cm),
        Paragraph("Marken", styles["Heading2"]),
        _chart(brand_share_chart(summary["brands"]), width=16 * cm),
        _table(
            [["Marke", "Antworten", "Anteil", "Zufriedenheit", "NPS"]]
            + [
                [
                    b["brand"],
                    f"{b['responses']}",
                    f"{b['share']:.1f} %",
                    f"{b['avg_satisfaction']:.2f}",
                    "–" if b["nps"] is None else f"{b['nps']:.1f}",
                ]
                for b in summary["brands"]
            ],
            col_widths=[5 * cm, 2.8 * cm, 2.6 * cm, 2.8 * cm, 2.4 * cm],
        ),
        Spacer(1, 0.4 * cm),
        # KeepTogether: Überschrift und Diagramm nie auf zwei Seiten verteilen
        KeepTogether(
            [
                Paragraph("Antworten pro Woche", styles["Heading2"]),
                _chart(weekly_chart(summary["weekly"]), width=16 * cm),
            ]
        ),
    ]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f"Umfrage-Auswertung: {title}",
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)
    return buffer.getvalue()
