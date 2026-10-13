import tempfile
from pathlib import Path

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .samples import CSV


class SurveyTestCase(TestCase):
    """Parquet files go to a temporary directory, not to data/."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.files_dir = Path(tmp.name)
        override = override_settings(SURVEY_FILES_DIR=self.files_dir)
        override.enable()
        self.addCleanup(override.disable)
        # Don't share cached summaries and upload rate limits between tests.
        cache.clear()

    def csv_file(self, filename="test.csv", content=CSV):
        return SimpleUploadedFile(filename, content.encode(), content_type="text/csv")

    def upload(self, filename="test.csv", content=CSV):
        return self.client.post("/api/surveys/", {"file": self.csv_file(filename, content)})
