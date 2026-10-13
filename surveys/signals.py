from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import SurveyUpload


@receiver(post_delete, sender=SurveyUpload)
def delete_data_file(sender, instance: SurveyUpload, **kwargs) -> None:
    """Parquet-Datei mitlöschen, aber erst wenn das Löschen in der Datenbank feststeht."""
    path = instance.data_path
    transaction.on_commit(lambda: path.unlink(missing_ok=True))
