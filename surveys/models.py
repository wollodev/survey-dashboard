from pathlib import Path

from django.conf import settings
from django.db import models


class SurveyUpload(models.Model):
    """An uploaded survey. The data itself is stored alongside as a Parquet file."""

    name = models.CharField(max_length=200)
    data_file = models.CharField(max_length=100, unique=True)
    row_count = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.row_count} Antworten)"

    @property
    def data_path(self) -> Path:
        return settings.SURVEY_FILES_DIR / self.data_file
