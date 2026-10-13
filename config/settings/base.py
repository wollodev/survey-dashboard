"""Shared settings. dev.py and prod.py only add what differs."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_list(name: str, default: str) -> list[str]:
    """Comma-separated environment variable -> list without whitespace or empty entries."""
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

# Everything the application stores lives in one directory.
# In the container a Docker volume is mounted there. It is created in SurveysConfig.ready().
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))

# Upload metadata (name, date, row count) in SQLite ...
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
    }
}

# ... the actual survey data as Parquet files.
SURVEY_FILES_DIR = DATA_DIR / "surveys"

# Accept uploads up to 100 MB
MAX_UPLOAD_SIZE = 100 * 1024 * 1024

# Cache computed summaries (uploads never change).
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True  # 74967 is rendered as 74.967 in templates

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    # Protect the open API against abuse: limit requests per IP address.
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "120/minute", "uploads": "20/hour"},
}
