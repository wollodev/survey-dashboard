from django.urls import include, path

urlpatterns = [
    path("", include("surveys.urls")),
]
