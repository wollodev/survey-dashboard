from django.apps import AppConfig
from django.conf import settings


class SurveysConfig(AppConfig):
    name = "surveys"

    def ready(self) -> None:
        from . import signals  # noqa: F401 – registriert die Signal-Handler

        # SQLite und die Parquet-Dateien brauchen einen existierenden Datenordner.
        settings.SURVEY_FILES_DIR.mkdir(parents=True, exist_ok=True)
