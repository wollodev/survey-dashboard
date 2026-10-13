"""Lokale Entwicklung und Tests (Standard für manage.py)."""

import os

from .base import *

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

# Statische Dateien direkt aus den Apps ausliefern, ohne collectstatic.
WHITENOISE_AUTOREFRESH = True
