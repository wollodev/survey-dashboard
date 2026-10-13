"""Application logic between the views/API and the pandas modules."""

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile

from .analysis import Summary, load_survey, summarize
from .importer import CleaningReport, read_and_clean, save_parquet
from .models import SurveyUpload


def create_survey(csv_file: UploadedFile, name: str | None) -> tuple[SurveyUpload, CleaningReport]:
    """Reads, cleans and stores a CSV. Raises SurveyImportError for invalid files."""
    df, report = read_and_clean(csv_file)
    filename = save_parquet(df, settings.SURVEY_FILES_DIR)
    try:
        upload = SurveyUpload.objects.create(
            name=name or csv_file.name or "Umfrage", data_file=filename, row_count=len(df)
        )
    except Exception:
        # Without a database row the file would never be found again: clean up.
        (settings.SURVEY_FILES_DIR / filename).unlink(missing_ok=True)
        raise
    return upload, report


def get_summary(upload: SurveyUpload) -> Summary:
    """Metrics of a survey. Uploads never change, so the result is cached."""
    key = f"survey-summary:{upload.data_file}"
    summary: Summary | None = cache.get(key)
    if summary is None:
        summary = summarize(load_survey(upload.data_path))
        cache.set(key, summary, timeout=None)
    return summary
