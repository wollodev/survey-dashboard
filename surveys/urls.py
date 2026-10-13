from django.urls import path

from . import api, views

urlpatterns = [
    path("api/surveys/", api.SurveyListCreateView.as_view(), name="api_survey_list"),
    path("api/surveys/<int:pk>/summary/", api.SurveySummaryView.as_view(), name="api_survey_summary"),
    path("", views.survey_list, name="survey_list"),
    path("surveys/<int:pk>/", views.dashboard, name="dashboard"),
    path("surveys/<int:pk>/report.pdf", views.survey_report, name="survey_report"),
]
