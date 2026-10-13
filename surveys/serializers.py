from rest_framework import serializers

from .models import SurveyUpload
from .validators import validate_csv_upload


class SurveyUploadSerializer(serializers.ModelSerializer):
    """Output: the metadata of an upload."""

    class Meta:
        model = SurveyUpload
        fields = ["id", "name", "row_count", "uploaded_at"]


class UploadSerializer(serializers.Serializer):
    """Input: the uploaded CSV file and an optional name."""

    file = serializers.FileField(validators=[validate_csv_upload])
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
