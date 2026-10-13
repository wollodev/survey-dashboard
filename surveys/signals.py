from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import SurveyUpload


@receiver(post_delete, sender=SurveyUpload)
def delete_data_file(sender, instance: SurveyUpload, **kwargs) -> None:
    """Delete the Parquet file too, but only once the database deletion is committed."""
    path = instance.data_path
    transaction.on_commit(lambda: path.unlink(missing_ok=True))
