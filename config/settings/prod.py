"""Production (default for wsgi.py/asgi.py and the Docker container)."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

# Better not to start at all than to start with a publicly known key.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("The DJANGO_SECRET_KEY environment variable must be set.")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
