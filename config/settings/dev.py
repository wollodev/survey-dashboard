"""Local development and tests (default for manage.py)."""

import os

from .base import *

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

# Serve static files straight from the apps, without collectstatic.
WHITENOISE_AUTOREFRESH = True
