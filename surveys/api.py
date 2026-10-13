"""JSON API with Django REST Framework."""

from dataclasses import asdict

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, BaseThrottle, ScopedRateThrottle
from rest_framework.views import APIView

from .importer import SurveyImportError
from .models import SurveyUpload
from .serializers import SurveyUploadSerializer, UploadSerializer
from .services import create_survey, get_summary


class SurveyListCreateView(APIView):
    """GET /api/surveys/ lists all uploads, POST uploads a new CSV."""

    parser_classes = [MultiPartParser]
    throttle_scope = "uploads"

    def get_throttles(self) -> list[BaseThrottle]:
        # Uploads are expensive and get their own, stricter limit.
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return [AnonRateThrottle()]

    def get(self, request: Request) -> Response:
        uploads = SurveyUpload.objects.all()
        return Response(SurveyUploadSerializer(uploads, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            upload, report = create_survey(
                serializer.validated_data["file"], serializer.validated_data.get("name")
            )
        except SurveyImportError as exc:
            raise ValidationError({"file": [str(exc)]}) from exc

        return Response(
            {"survey": SurveyUploadSerializer(upload).data, "report": asdict(report)},
            status=status.HTTP_201_CREATED,
        )


class SurveySummaryView(APIView):
    """GET /api/surveys/<id>/summary/ returns all metrics as JSON."""

    def get(self, request: Request, pk: int) -> Response:
        upload = get_object_or_404(SurveyUpload, pk=pk)
        return Response(get_summary(upload))
