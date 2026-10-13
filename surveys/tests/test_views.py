from django.urls import reverse

from ..models import SurveyUpload
from .base import SurveyTestCase


class ViewTests(SurveyTestCase):
    def test_upload_form_redirects_to_dashboard(self):
        response = self.client.post(reverse("survey_list"), {"file": self.csv_file(), "name": "März"})
        upload = SurveyUpload.objects.get()
        self.assertRedirects(response, reverse("dashboard", args=[upload.pk]))
        self.assertEqual(upload.name, "März")

    def test_upload_form_shows_import_errors(self):
        response = self.client.post(reverse("survey_list"), {"file": self.csv_file(content="foo\n1\n")})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "konnte nicht gelesen werden")
        self.assertFalse(SurveyUpload.objects.exists())

    def test_dashboard_page(self):
        survey_id = self.upload().json()["survey"]["id"]
        response = self.client.get(reverse("dashboard", args=[survey_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bohnenwerk")
        self.assertContains(response, "Hessen")  # Bundesländer werden angezeigt

    def test_pdf_report(self):
        survey_id = self.upload().json()["survey"]["id"]
        response = self.client.get(reverse("survey_report", args=[survey_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
