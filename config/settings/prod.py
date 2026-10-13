"""Produktion (Standard für wsgi.py/asgi.py und den Docker-Container)."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

# Ohne eigenen Schlüssel lieber gar nicht starten als mit einem bekannten.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Die Umgebungsvariable DJANGO_SECRET_KEY muss gesetzt sein.")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
