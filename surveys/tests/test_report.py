import io
from datetime import UTC, datetime

from django.test import SimpleTestCase

from ..charts import brand_share_chart
from ..data.analysis import summarize
from ..data.importer import read_and_clean
from ..report import build_report
from .samples import CSV


class ReportTests(SimpleTestCase):
    def test_build_report_returns_pdf(self):
        df, _ = read_and_clean(io.StringIO(CSV))
        pdf = build_report("Test <b>Umfrage", datetime(2026, 3, 1, tzinfo=UTC), summarize(df))
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_brand_chart_without_brands(self):
        self.assertTrue(brand_share_chart([]).startswith(b"\x89PNG"))
