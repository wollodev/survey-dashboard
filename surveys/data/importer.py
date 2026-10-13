"""Read a CSV, clean it and store it as Parquet."""

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
    """The file is not a valid survey CSV."""


@dataclass
class CleaningReport:
    """What happened during cleaning; returned after the upload."""

    rows_read: int = 0
    duplicates_removed: int = 0
    invalid_dates_removed: int = 0
    values_set_missing: dict[str, int] = field(default_factory=dict)
    unknown_regions: int = 0
    rows_saved: int = 0


def normalize_region(regions: pd.Series) -> pd.Series:
    """Maps every spelling to the correct name; unknown values become NA."""
    lookup = {name.lower(): name for name in REGIONS} | REGION_ALIASES
    return regions.str.strip().str.lower().map(lookup)


def read_and_clean(source: str | Path | IO) -> tuple[pd.DataFrame, CleaningReport]:
    """Reads a survey CSV and returns (DataFrame, cleaning report)."""
    try:
        df = pd.read_csv(source, usecols=list(COLUMN_TYPES), dtype=COLUMN_TYPES)
    except ValueError as exc:  # missing columns, text in numeric columns, ...
        raise SurveyImportError(f"The CSV could not be read: {exc}") from exc

    report = CleaningReport(rows_read=len(df))

    # 1. Duplicates: the same response was submitted more than once.
    before = len(df)
    df = df.drop_duplicates(subset="response_id", keep="first")
    report.duplicates_removed = before - len(df)

    # 2. Parse timestamps. Broken values become NaT ("not a time") and are dropped.
    submitted_at = pd.to_datetime(df["submitted_at"], errors="coerce")
    invalid_dates = submitted_at.isna()
    df = df.assign(submitted_at=submitted_at)[~invalid_dates]
    report.invalid_dates_removed = int(invalid_dates.sum())

    # 3. Set out-of-range values (and fractions in integer columns) to missing.
    for column, (low, high) in VALID_RANGES.items():
        values = df[column]
        invalid = values.notna() & ~values.between(low, high)
        if column in INTEGER_COLUMNS:
            invalid |= values.notna() & (values % 1 != 0)
        df[column] = values.mask(invalid)
        report.values_set_missing[column] = int(invalid.sum())

    # Now all values safely fit into the small integer type.
    df = df.astype(INTEGER_COLUMNS)

    # 4. Normalize federal state names.
    df["region"] = normalize_region(df["region"])
    report.unknown_regions = int(df["region"].isna().sum())

    # 5. Store low-cardinality text columns as categories.
    df[CATEGORY_COLUMNS] = df[CATEGORY_COLUMNS].astype("category")

    if df.empty:
        raise SurveyImportError("No rows left after cleaning.")

    report.rows_saved = len(df)
    return df.reset_index(drop=True), report


def save_parquet(df: pd.DataFrame, directory: Path) -> str:
    """Saves the DataFrame as a Parquet file and returns the file name."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.parquet"
    df.to_parquet(directory / filename, index=False)
    return filename
