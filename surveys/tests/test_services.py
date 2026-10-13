from unittest import mock

from ..models import SurveyUpload
from ..services import create_survey
from .base import SurveyTestCase


class CreateSurveyTests(SurveyTestCase):
    def test_removes_file_when_database_write_fails(self):
        with (
            mock.patch.object(SurveyUpload.objects, "create", side_effect=RuntimeError),
            self.assertRaises(RuntimeError),
        ):
            create_survey(self.csv_file(), None)
        self.assertEqual(list(self.files_dir.iterdir()), [])

    def test_name_defaults_to_file_name(self):
        upload, _ = create_survey(self.csv_file("maerz.csv"), "")
        self.assertEqual(upload.name, "maerz.csv")


class DeleteSurveyTests(SurveyTestCase):
    def test_deleting_upload_deletes_file(self):
        upload, _ = create_survey(self.csv_file(), None)
        with self.captureOnCommitCallbacks(execute=True):
            upload.delete()
        self.assertFalse(upload.data_path.exists())
