"""HTML-Seiten mit Django-Templates."""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from surveys.forms import UploadForm
from surveys.importer import SurveyImportError
from surveys.report import build_report
from surveys.services import create_survey

from .analysis import load_survey, summarize
from .models import SurveyUpload


def survey_list(request):
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


def dashboard(request, pk: int):
    """Dashboard einer Umfrage."""
    upload = get_object_or_404(SurveyUpload, pk=pk)
    summary = summarize(load_survey(upload.data_path))

    # Höchstwerte, damit der längste Balken die volle Breite bekommt.
    context = {
        "upload": upload,
        "summary": summary,
        "brand_max": max((b["share"] for b in summary["brands"]), default=1),
        "region_max": max((r["responses"] for r in summary["regions"]), default=1),
        "weekly_max": max((w["responses"] for w in summary["weekly"]), default=1),
    }
    return render(request, "surveys/dashboard.html", context)


def survey_report(request, pk: int):
    """PDF-Bericht einer Umfrage zum Herunterladen."""
    upload = get_object_or_404(SurveyUpload, pk=pk)
    summary = summarize(load_survey(upload.data_path))
    pdf = build_report(
        title=upload.name,
        uploaded_at=upload.uploaded_at,
        summary=summary,
        created_at=timezone.localtime(),
    )

    return HttpResponse(
        pdf,
        content_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="umfrage-{upload.pk}.pdf"'},
    )
