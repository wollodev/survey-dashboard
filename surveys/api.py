"""JSON-API mit Django REST Framework."""

from typing import Any, cast

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView, Response

from surveys.analysis import load_survey, summarize
from surveys.importer import SurveyImportError
from surveys.models import SurveyUpload
from surveys.serializers import SurveyUploadSerializer, UploadSerializer
from surveys.services import create_survey


class SurveyListCreateView(APIView):
    """GET /api/surveys/ listet alle Uploads, POST lädt eine neue CSV hoch."""

    parser_classes = [MultiPartParser]

    def get(self, request):
        uploads = SurveyUpload.objects.all()
        return Response(SurveyUploadSerializer(uploads, many=True).data)

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        csv_file = data["file"]
        try:
            upload, report = create_survey(csv_file, data.get("name"))
        except SurveyImportError as exc:
            raise ValidationError({"file": [str(exc)]}) from exc

        return Response(
            {"survey": SurveyUploadSerializer(upload).data, "report": report},
            status=status.HTTP_201_CREATED,
        )


class SurveySummaryView(APIView):
    """GET /api/surveys/<id>/summary/ liefert alle Kennzahlen als JSON."""

    def get(self, request, pk: int):
        upload = get_object_or_404(SurveyUpload, pk=pk)
        return Response(summarize(load_survey(upload.data_path)))
