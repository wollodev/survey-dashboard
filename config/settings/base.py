"""Gemeinsame Einstellungen. dev.py und prod.py ergänzen nur, was sich unterscheidet."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_list(name: str, default: str) -> list[str]:
    """Kommagetrennte Umgebungsvariable -> Liste ohne Leerzeichen und leere Einträge."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "rest_framework",
    "surveys",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {},
    },
]

# Alles, was die Anwendung speichert, liegt in einem Ordner.
# Im Container wird dort ein Docker-Volume eingehängt. Angelegt wird er in SurveysConfig.ready().
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))

# Metadaten der Uploads (Name, Datum, Zeilenzahl) in SQLite ...
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
    }
}

# ... die eigentlichen Umfragedaten als Parquet-Dateien.
SURVEY_FILES_DIR = DATA_DIR / "surveys"

# Uploads bis 100 MB annehmen
MAX_UPLOAD_SIZE = 100 * 1024 * 1024

# Berechnete Auswertungen zwischenspeichern (Uploads ändern sich nie).
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True  # 74967 wird in Templates zu 74.967

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    # Schutz vor Missbrauch der offenen API: Anfragen pro IP-Adresse begrenzen.
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "120/minute", "uploads": "20/hour"},
}
