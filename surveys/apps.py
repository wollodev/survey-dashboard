from django.apps import AppConfig
from django.conf import settings


class SurveysConfig(AppConfig):
    name = "surveys"

    def ready(self) -> None:
        from . import signals  # noqa: F401 - registers the signal handlers

        # SQLite and the Parquet files need an existing data directory.
        settings.SURVEY_FILES_DIR.mkdir(parents=True, exist_ok=True)
