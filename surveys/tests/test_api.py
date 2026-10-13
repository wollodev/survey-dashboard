from django.test import override_settings

from ..models import SurveyUpload
from .base import SurveyTestCase


class SurveyApiTests(SurveyTestCase):
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

    @override_settings(MAX_UPLOAD_SIZE=10)
    def test_upload_rejects_large_files(self):
        response = self.upload()
        self.assertEqual(response.status_code, 400)
        self.assertIn("larger", response.json()["file"][0])

    def test_upload_rejects_broken_csv(self):
        response = self.upload(content="foo,bar\n1,2\n")
        self.assertEqual(response.status_code, 400)

    def test_list(self):
        self.upload()
        response = self.client.get("/api/surveys/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["row_count"], 3)

    def test_summary_endpoint(self):
        survey_id = self.upload().json()["survey"]["id"]
        response = self.client.get(f"/api/surveys/{survey_id}/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["kpis"]["responses"], 3)

    def test_summary_not_found(self):
        self.assertEqual(self.client.get("/api/surveys/999/summary/").status_code, 404)
