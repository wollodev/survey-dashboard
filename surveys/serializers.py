from rest_framework import serializers

from config import settings
from surveys.models import SurveyUpload


class SurveyUploadSerializer(serializers.ModelSerializer):
    """Ausgabe: die Metadaten eines Uploads."""

    class Meta:
        model = SurveyUpload
        fields = ["id", "name", "row_count", "uploaded_at"]


class UploadSerializer(serializers.Serializer):
    """Eingabe: die hochgeladene CSV-Datei und ein optionaler Name."""

    file = serializers.FileField()
    name = serializers.CharField(max_length=200, required=False)

    def validate_file(self, value):
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Bitte eine .csv-Datei hochladen.")
        if value.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError("Die Datei is größer als 100 MB.")
        return value
