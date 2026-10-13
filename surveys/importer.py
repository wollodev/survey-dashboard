"""CSV einlesen, bereinigen und als Parquet speichern."""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

import pandas as pd

from .schema import (
    CATEGORY_COLUMNS,
    COLUMN_TYPES,
    INTEGER_COLUMNS,
    REGION_ALIASES,
    REGIONS,
    VALID_RANGES,
)


class SurveyImportError(Exception):
    """Die Datei ist keine gültige Umfrage-CSV."""


@dataclass
class CleaningReport:
    """Was beim Bereinigen passiert ist; wird nach dem Upload angezeigt."""

    rows_read: int = 0
    duplicates_removed: int = 0
    invalid_dates_removed: int = 0
    values_set_missing: dict[str, int] = field(default_factory=dict)
    unknown_regions: int = 0
    rows_saved: int = 0


def normalize_region(regions: pd.Series) -> pd.Series:
    """Bildet jede Schreibweise auf den korrekten Namen ab; Unbekanntes wird zu NA."""
    lookup = {name.lower(): name for name in REGIONS} | REGION_ALIASES
    return regions.str.strip().str.lower().map(lookup)


def read_and_clean(source: str | Path | IO) -> tuple[pd.DataFrame, CleaningReport]:
    """Liest eine Umfrage-CSV und gibt (DataFrame, Bereinigungsbericht) zurück."""
    try:
        df = pd.read_csv(source, usecols=list(COLUMN_TYPES), dtype=COLUMN_TYPES)
    except ValueError as exc:  # fehlende Spalten, Text in Zahlenspalten, ...
        raise SurveyImportError(f"CSV konnte nicht gelesen werden: {exc}") from exc

    report = CleaningReport(rows_read=len(df))

    # 1. Dubletten: dieselbe Antwort wurde mehrfach abgeschickt.
    before = len(df)
    df = df.drop_duplicates(subset="response_id", keep="first")
    report.duplicates_removed = before - len(df)

    # 2. Zeitstempel umwandeln. Kaputte Werte werden zu NaT ("not a time") und fliegen raus.
    submitted_at = pd.to_datetime(df["submitted_at"], errors="coerce")
    invalid_dates = submitted_at.isna()
    df = df.assign(submitted_at=submitted_at)[~invalid_dates]
    report.invalid_dates_removed = int(invalid_dates.sum())

    # 3. Werte außerhalb des erlaubten Bereichs (und Kommazahlen in Ganzzahl-Spalten) auf "fehlend" setzen.
    for column, (low, high) in VALID_RANGES.items():
        values = df[column]
        invalid = values.notna() & ~values.between(low, high)
        if column in INTEGER_COLUMNS:
            invalid |= values.notna() & (values % 1 != 0)
        df[column] = values.mask(invalid)
        report.values_set_missing[column] = int(invalid.sum())

    # Jetzt passen alle Werte sicher in den kleinen Ganzzahl-Typ.
    df = df.astype(INTEGER_COLUMNS)

    # 4. Bundesländer vereinheitlichen.
    df["region"] = normalize_region(df["region"])
    report.unknown_regions = int(df["region"].isna().sum())

    # 5. Textspalten mit wenigen Ausprägungen als Kategorie speichern.
    df[CATEGORY_COLUMNS] = df[CATEGORY_COLUMNS].astype("category")

    if df.empty:
        raise SurveyImportError("Nach der Bereinigung ist keine Zeile übrig.")

    report.rows_saved = len(df)
    return df.reset_index(drop=True), report


def save_parquet(df: pd.DataFrame, directory: Path) -> str:
    """Speichert den DataFrame als Parquet-Datei und gibt den Dateinamen zurück."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.parquet"
    df.to_parquet(directory / filename, index=False)
    return filename
