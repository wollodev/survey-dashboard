from django.conf import settings

from surveys.importer import read_and_clean, save_parquet
from surveys.models import SurveyUpload


def create_survey(csv_file, name: str | None) -> tuple[SurveyUpload, dict]:
    """Liest, bereinigt und speichert eine CSV. Wirft SurveyImportError bei ungültigen Dateien."""

    df, report = read_and_clean(csv_file)
    filename = save_parquet(df, settings.SURVEY_FILES_DIR)
    upload = SurveyUpload.objects.create(name=name or csv_file.name, data_file=filename, row_count=len(df))

    return upload, report
