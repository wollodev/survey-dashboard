# Umfrage-Dashboard

Django-Anwendung zum Hochladen, Bereinigen und Auswerten von Umfrage-CSVs (Kaffeekonsum).
Die Daten werden mit pandas bereinigt, als Parquet gespeichert und als Dashboard, JSON-API
und PDF-Bericht ausgegeben.

## Aufbau

| Modul | Aufgabe |
|---|---|
| `surveys/schema.py` | Spalten, Datentypen, erlaubte Werte |
| `surveys/importer.py` | CSV einlesen und bereinigen → `CleaningReport` |
| `surveys/analysis.py` | Kennzahlen mit pandas → `Summary` |
| `surveys/services.py` | Upload speichern, Auswertung zwischenspeichern |
| `surveys/views.py`, `api.py` | HTML-Seiten und JSON-API |
| `surveys/charts.py`, `report.py` | Diagramme (matplotlib) und PDF (ReportLab) |

Metadaten liegen in SQLite, die Umfragedaten als Parquet-Dateien – beides unter `DATA_DIR` (Standard: `data/`).

## Lokal entwickeln

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py generate_survey          # erzeugt survey.csv mit 75.000 Testantworten
python manage.py runserver
```

`manage.py` nutzt `config.settings.dev`, `wsgi.py`/`asgi.py` nutzen `config.settings.prod`.

### Prüfen

```bash
python manage.py test
ruff check . && ruff format --check .
mypy .
```

## Mit Docker

```bash
cp .env.example .env    # DJANGO_SECRET_KEY eintragen
docker compose up --build
```

## API

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/api/surveys/` | alle Uploads |
| `POST` | `/api/surveys/` | CSV hochladen (`file`, optional `name`), max. 20 pro Stunde und IP |
| `GET` | `/api/surveys/<id>/summary/` | alle Kennzahlen als JSON |

```bash
curl -F "file=@survey.csv" http://localhost:8000/api/surveys/
```

Weitere Seiten: `/surveys/<id>/` (Dashboard) und `/surveys/<id>/report.pdf` (PDF-Bericht).
