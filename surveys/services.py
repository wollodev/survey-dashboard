"""Anwendungslogik zwischen Views/API und den pandas-Modulen."""

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile

from .analysis import Summary, load_survey, summarize
from .importer import CleaningReport, read_and_clean, save_parquet
from .models import SurveyUpload


def create_survey(csv_file: UploadedFile, name: str | None) -> tuple[SurveyUpload, CleaningReport]:
    """Liest, bereinigt und speichert eine CSV. Wirft SurveyImportError bei ungültigen Dateien."""
    df, report = read_and_clean(csv_file)
    filename = save_parquet(df, settings.SURVEY_FILES_DIR)
    try:
        upload = SurveyUpload.objects.create(
            name=name or csv_file.name or "Umfrage", data_file=filename, row_count=len(df)
        )
    except Exception:
        # Ohne Datenbankeintrag würde die Datei nie wieder gefunden: aufräumen.
        (settings.SURVEY_FILES_DIR / filename).unlink(missing_ok=True)
        raise
    return upload, report


def get_summary(upload: SurveyUpload) -> Summary:
    """Kennzahlen einer Umfrage. Uploads ändern sich nie, daher wird das Ergebnis zwischengespeichert."""
    key = f"survey-summary:{upload.data_file}"
    summary: Summary | None = cache.get(key)
    if summary is None:
        summary = summarize(load_survey(upload.data_path))
        cache.set(key, summary, timeout=None)
    return summary
