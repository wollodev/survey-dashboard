FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    DATA_DIR=/app/data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CSS & Co. einsammeln; WhiteNoise liefert sie aus. Der Schlüssel wird nur für diesen Schritt gebraucht.
RUN DJANGO_SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput

# Nicht als root laufen; der Datenordner muss dem App-Benutzer gehören.
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown appuser /app/data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/', timeout=4)"

# Erst die Datenbank auf den neuesten Stand bringen, dann Gunicorn starten.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile -"]
