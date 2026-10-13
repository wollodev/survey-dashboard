"""CSV einlesen, bereinigen und als Parquet speichern."""

# Spalte -> Datentyp beim Einlesen.
# "Int8" (großes I) ist ein ganzzahliger Typ, der fehlende Werte (pd.NA) erlaubt.
import uuid
from pathlib import Path
from typing import IO, Any

import pandas as pd

COLUMN_TYPES = {
    "response_id": "int64",
    "submitted_at": "str",
    "age": "Int8",
    "gender": "str",
    "region": "str",
    "income_band": "str",
    "cups_per_day": "Int8",
    "preferred_brand": "str",
    "channel": "str",
    "monthly_spend_eur": "float64",
    "satisfaction": "Int8",
    "nps_score": "Int8",
    "would_subscribe": "str",
}

VALID_REGIONS = [
    "Baden-Württemberg",
    "Bayern",
    "Berlin",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thüringen",
]

# Abkürzungen und Schreibvarianten, jeweils kleingeschrieben
REGION_ALIASES = {
    "nrw": "Nordrhein-Westfalen",
    "bay": "Bayern",
    "bw": "Baden-Württemberg",
    "baden-wuerttemberg": "Baden-Württemberg",
    "nds": "Niedersachsen",
    "hes": "Hessen",
    "rlp": "Rheinland-Pfalz",
    "sac": "Sachsen",
    "ber": "Berlin",
    "sh": "Schleswig-Holstein",
    "bra": "Brandenburg",
    "saa": "Sachsen-Anhalt",
    "thü": "Thüringen",
    "hh": "Hamburg",
    "mv": "Mecklenburg-Vorpommern",
    "sl": "Saarland",
    "hb": "Bremen",
}

# Spalten mit wenigen, sich wiederholenden Werten -> Typ "category" spart viel Speicher.
CATEGORY_COLUMNS = ["gender", "region", "income_band", "preferred_brand", "channel", "would_subscribe"]

# Erlaubte Wertebereiche. Alles außerhalb wird zu einem fehlenden Wert.
VALID_RANGES = {
    "age": (18, 99),
    "cups_per_day": (0, 20),
    "monthly_spend_eur": (0, 1000),
    "satisfaction": (1, 5),
    "nps_score": (0, 10),
}


class SurveyImportError(Exception):
    """Die Datei ist keine gültige Umfrage-CSV."""


def normalize_region(regions: pd.Series) -> pd.Series:
    """Bildet jede Schreibweise auf den korrekten Namen ab; Unbekanntes wird zu NA."""
    lookup = {name.lower(): name for name in VALID_REGIONS} | REGION_ALIASES
    return regions.str.strip().str.lower().map(lookup)


def read_and_clean(source: str | Path | IO) -> tuple[pd.DataFrame, dict]:
    """Liest eine Umfrage-CSV und gibt (DateFrame, Bereinigungsbericht) zurück."""

    try:
        df = pd.read_csv(source, usecols=list(COLUMN_TYPES), dtype=COLUMN_TYPES)
    except ValueError as exc:  # fehlende Spalten, Text in Zahlenspalten, ...
        raise SurveyImportError(f"CSV konte nicht gelesen werden: {exc}") from exc

    report: dict[str, Any] = {"rows_read": len(df)}

    # 1. Dubletten: dieselbe Antwort wurde mehrfach abgeschickt.
    before = len(df)
    df = df.drop_duplicates(subset="response_id", keep="first")
    report["duplicates_removed"] = before - len(df)

    # 2. Zeitstempel umwandeln. Kaputte Werte werden zu NaT ("not a time") und fliegen raus.
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], errors="coerce")
    invalid_dates = df["submitted_at"].isna()
    df = df[~invalid_dates]
    report["invalid_dates_removed"] = int(invalid_dates.sum())

    # 3. Werte außerhalb des erlaubten Bereichs auf "fehlend" setzen.
    report["values_set_missing"] = {}
    for column, (low, high) in VALID_RANGES.items():
        out_of_range = df[column].notna() & ~df[column].between(low, high)
        df.loc[out_of_range, column] = pd.NA
        report["values_set_missing"][column] = int(out_of_range.sum())

    # 4. Bundesländer vereinheitlichen.
    df["region"] = normalize_region(df["region"])
    report["unknown_regions"] = int(df["region"].isna().sum())

    # 5. Textspalten mit wenigen Ausprägungen als Kategorie speichern
    df[CATEGORY_COLUMNS] = df[CATEGORY_COLUMNS].astype("category")

    if df.empty:
        raise SurveyImportError("Nach der Bereinigung ist keine Zeile übrig.")

    report["rows_saved"] = len(df)
    return df.reset_index(drop=True), report


def save_parquet(df: pd.DataFrame, directory: Path) -> str:
    """Speichert den DataFrame als Parquet-Datei und gibt den Dateinamen zurück."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.parquet"
    df.to_parquet(directory / filename, index=False)
    return filename
