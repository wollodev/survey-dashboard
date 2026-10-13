import io
from datetime import UTC, datetime

from django.test import SimpleTestCase

from ..charts import brand_share_chart
from ..data.analysis import summarize
from ..data.importer import read_and_clean
from ..report import build_report
from .samples import CSV, HEADER, row


class ReportTests(SimpleTestCase):
    def test_build_report_returns_pdf(self):
        df, _ = read_and_clean(io.StringIO(CSV))
        pdf = build_report("Test <b>survey", datetime(2026, 3, 1, tzinfo=UTC), summarize(df))
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_build_report_with_missing_values(self):
        df, _ = read_and_clean(io.StringIO(HEADER + row(1, satisfaction=None, monthly_spend_eur=None)))
        pdf = build_report("Sparse", datetime(2026, 3, 1, tzinfo=UTC), summarize(df))
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_brand_chart_without_brands(self):
        self.assertTrue(brand_share_chart([]).startswith(b"\x89PNG"))
