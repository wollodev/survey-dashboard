"""Checks for uploaded files, shared by the form and the API."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.template.defaultfilters import filesizeformat


def validate_csv_upload(file: File) -> None:
    """Only accept .csv files up to MAX_UPLOAD_SIZE."""
    if not (file.name or "").lower().endswith(".csv"):
        raise ValidationError("Bitte eine .csv-Datei hochladen.")
    if file.size is not None and file.size > settings.MAX_UPLOAD_SIZE:
        limit = filesizeformat(settings.MAX_UPLOAD_SIZE)
        raise ValidationError(f"Die Datei ist größer als {limit}.")
