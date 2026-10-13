"""HTML-Seiten mit Django-Templates."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .analysis import Rows
from .forms import UploadForm
from .importer import SurveyImportError
from .models import SurveyUpload
from .report import build_report
from .services import create_survey, get_summary


def _largest(rows: Rows, key: str) -> float:
    """Größter Wert einer Spalte, damit der längste Balken die volle Breite bekommt."""
    return max((row[key] for row in rows if row[key] is not None), default=1) or 1


def survey_list(request: HttpRequest) -> HttpResponse:
    """Startseite: alle Umfragen und das Upload-Formular."""
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            upload, _ = create_survey(form.cleaned_data["file"], form.cleaned_data["name"])
        except SurveyImportError as exc:
            form.add_error("file", str(exc))
        else:
            return redirect("dashboard", pk=upload.pk)
    return render(request, "surveys/survey_list.html", {"uploads": SurveyUpload.objects.all(), "form": form})


def dashboard(request: HttpRequest, pk: int) -> HttpResponse:
    """Dashboard einer Umfrage."""
    upload = get_object_or_404(SurveyUpload, pk=pk)
    summary = get_summary(upload)
    context = {
        "upload": upload,
        "summary": summary,
        "brand_max": _largest(summary["brands"], "share"),
        "channel_max": _largest(summary["channels"], "share"),
        "region_max": _largest(summary["regions"], "responses"),
        "weekly_max": _largest(summary["weekly"], "responses"),
    }
    return render(request, "surveys/dashboard.html", context)


def survey_report(request: HttpRequest, pk: int) -> HttpResponse:
    """PDF-Bericht einer Umfrage zum Herunterladen."""
    upload = get_object_or_404(SurveyUpload, pk=pk)
    pdf = build_report(
        title=upload.name,
        uploaded_at=upload.uploaded_at,
        summary=get_summary(upload),
        created_at=timezone.localtime(),
    )
    return HttpResponse(
        pdf,
        content_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="umfrage-{upload.pk}.pdf"'},
    )
