import io
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings

from surveys.report import build_report

from .analysis import net_promoter_score, summarize
from .importer import SurveyImportError, read_and_clean
from .models import SurveyUpload

HEADER = (
    "response_id,submitted_at,age,gender,region,income_band,cups_per_day,"
    "preferred_brand,channel,monthly_spend_eur,satisfaction,nps_score,would_subscribe\n"
)
CSV = HEADER + (
    "1,2026-03-02 10:00:00,25,weiblich,Berlin,keine Angabe,2,Bohnenwerk,Abo,30.5,5,10,ja\n"
    "2,2026-03-03 11:00:00,40,männlich,Bayern,keine Angabe,3,Röstzeit,Supermarkt,12.0,3,6,nein\n"
    "2,2026-03-03 11:00:00,40,männlich,Bayern,keine Angabe,3,Röstzeit,Supermarkt,12.0,3,6,nein\n"
    "3,unbekannt,55,divers,Hessen,keine Angabe,1,Morgenrot,Café,20.0,4,8,vielleicht\n"
    "4,2026-03-10 09:30:00,70,weiblich,Hessen,keine Angabe,1,Bohnenwerk,Café,9999,4,99,nein\n"
)


class ImporterTests(SimpleTestCase):
    def test_cleaning_report(self):
        df, report = read_and_clean(io.StringIO(CSV))
        self.assertEqual(report["rows_read"], 5)
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(report["invalid_dates_removed"], 1)
        self.assertEqual(report["values_set_missing"]["monthly_spend_eur"], 1)
        self.assertEqual(report["values_set_missing"]["nps_score"], 1)
        self.assertEqual(report["rows_saved"], 3)
        self.assertEqual(len(df), 3)

    def test_rejects_missing_columns(self):
        with self.assertRaises(SurveyImportError):
            read_and_clean(io.StringIO("response_id,age\n1,30\n"))


class AnalysisTests(SimpleTestCase):
    def test_net_promoter_score(self):
        # 2 Promotoren (10, 9), 1 Kritiker (0) von 4 -> 50 % - 25 % = 25
        self.assertEqual(net_promoter_score(pd.Series([10, 9, 8, 0])), 25.0)

    def test_net_promoter_score_ignores_missing_values(self):
        self.assertEqual(net_promoter_score(pd.Series([10, None], dtype="Int8")), 100.0)

    def test_summary(self):
        df, _ = read_and_clean(io.StringIO(CSV))
        summary = summarize(df)
        self.assertEqual(summary["kpis"]["responses"], 3)
        self.assertEqual(summary["brands"][0]["brand"], "Bohnenwerk")
        self.assertEqual(summary["brands"][0]["responses"], 2)


class ReportTests(SimpleTestCase):
    def test_build_report_returns_pdf(self):
        df, _ = read_and_clean(io.StringIO(CSV))
        pdf = build_report("Test <b>Umfrage", datetime(2026, 3, 1, tzinfo=UTC), summarize(df))
        self.assertTrue(pdf.startswith(b"%PDF"))


class ApiTests(TestCase):
    def setUp(self):
        # Parquet-Dateien in einen temporären Ordner schreiben, nicht nach data/.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        override = override_settings(SURVEY_FILES_DIR=Path(tmp.name))
        override.enable()
        self.addCleanup(override.disable)

    def upload(self, filename="test.csv", content=CSV):
        file = SimpleUploadedFile(filename, content.encode(), content_type="text/csv")
        return self.client.post("/api/surveys/", {"file": file})

    def test_upload_creates_survey(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["report"]["rows_saved"], 3)
        upload = SurveyUpload.objects.get()
        self.assertTrue(upload.data_path.exists())

    def test_upload_rejects_other_file_types(self):
        response = self.upload(filename="test.txt")
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json())

    def test_upload_rejects_broken_csv(self):
        response = self.upload(content="foo,bar\n1,2\n")
        self.assertEqual(response.status_code, 400)

    def test_summary_endpoint(self):
        survey_id = self.upload().json()["survey"]["id"]
        response = self.client.get(f"/api/surveys/{survey_id}/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["kpis"]["responses"], 3)

    def test_dashboard_page(self):
        survey_id = self.upload().json()["survey"]["id"]
        response = self.client.get(f"/surveys/{survey_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bohnenwerk")

    def test_pdf_report(self):
        survey_id = self.upload().json()["survey"]["id"]
        response = self.client.get(f"/surveys/{survey_id}/report.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
