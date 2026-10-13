"""Auswertung einer Umfrage mit pandas.

Jede Kennzahl hat eine eigene kleine Funktion; summarize() setzt sie zusammen.
Die Ergebnisse sind reine Python-Werte (keine NaN), damit sie direkt als JSON taugen.
"""

import math
from pathlib import Path
from typing import Any, TypedDict, cast

import pandas as pd

from .schema import AGE_BINS, AGE_LABELS, INCOME_ORDER, YES

Rows = list[dict[str, Any]]


class Kpis(TypedDict):
    responses: int
    avg_satisfaction: float | None
    nps: float | None
    avg_monthly_spend: float | None
    subscribe_rate: float | None


class Summary(TypedDict):
    kpis: Kpis
    brands: Rows
    age_groups: Rows
    channels: Rows
    regions: Rows
    weekly: Rows
    income: Rows


def load_survey(path: Path) -> pd.DataFrame:
    """Lädt eine gespeicherte Umfrage."""
    return pd.read_parquet(path)


def _round(value: Any, digits: int) -> float | None:
    """Rundet eine Zahl; fehlende Werte (None, NaN, pd.NA) werden zu None."""
    if value is None or value is pd.NA or math.isnan(value):
        return None
    return round(float(value), digits)


def _records(df: pd.DataFrame) -> Rows:
    """DataFrame -> Liste von dicts, fehlende Werte als None (JSON: null)."""
    return cast(Rows, df.astype(object).where(df.notna(), None).to_dict("records"))


def net_promoter_score(scores: pd.Series) -> float | None:
    """NPS = Anteil Promotoren (9-10) minus Anteil Kritiker (0-6), in Prozentpunkten."""
    scores = scores.dropna()
    if scores.empty:
        return None
    promoters = (scores >= 9).mean()
    detractors = (scores <= 6).mean()
    return _round((promoters - detractors) * 100, 1)


def yes_rate(answers: pd.Series) -> float:
    """Anteil der Antworten "ja" in Prozent."""
    return float((answers == YES).mean() * 100)


def kpis(df: pd.DataFrame) -> Kpis:
    """Die wichtigsten Kennzahlen über alle Antworten."""
    return {
        "responses": len(df),
        "avg_satisfaction": _round(df["satisfaction"].mean(), 2),
        "nps": net_promoter_score(df["nps_score"]),
        "avg_monthly_spend": _round(df["monthly_spend_eur"].mean(), 2),
        "subscribe_rate": _round(yes_rate(df["would_subscribe"]), 1),
    }


def brand_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Anzahl, Anteil, Zufriedenheit und NPS je Marke, größte Marke zuerst."""
    brands = (
        df.groupby("preferred_brand", observed=True)
        .agg(
            responses=("response_id", "size"),
            avg_satisfaction=("satisfaction", "mean"),
            nps=("nps_score", net_promoter_score),
        )
        .sort_values("responses", ascending=False)
        .reset_index()
        .rename(columns={"preferred_brand": "brand"})
    )
    brands["share"] = (brands["responses"] / len(df) * 100).round(1)
    brands["avg_satisfaction"] = brands["avg_satisfaction"].round(2)
    return brands


def age_group_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Anzahl, NPS und Abo-Bereitschaft je Altersgruppe."""
    age_group = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS).rename("age_group")
    age_groups = (
        df.groupby(age_group, observed=True)
        .agg(
            responses=("response_id", "size"),
            nps=("nps_score", net_promoter_score),
            subscribe_rate=("would_subscribe", yes_rate),
        )
        .reset_index()
    )
    age_groups["subscribe_rate"] = age_groups["subscribe_rate"].round(1)
    return age_groups


def income_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Median der Ausgaben je Einkommensgruppe, in natürlicher Reihenfolge."""
    income_band = df["income_band"].cat.set_categories(INCOME_ORDER, ordered=True)
    income = (
        df.groupby(income_band, observed=True)
        .agg(responses=("response_id", "size"), median_spend=("monthly_spend_eur", "median"))
        .reset_index()
    )
    income["median_spend"] = income["median_spend"].round(2)
    return income


def channel_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Anteil der Antworten je Einkaufskanal."""
    return (
        df["channel"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .rename_axis("channel")
        .reset_index(name="share")
    )


def region_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Anzahl und Zufriedenheit je Bundesland, meiste Antworten zuerst."""
    regions = (
        df.groupby("region", observed=True)
        .agg(responses=("response_id", "size"), avg_satisfaction=("satisfaction", "mean"))
        .sort_values("responses", ascending=False)
        .reset_index()
    )
    regions["avg_satisfaction"] = regions["avg_satisfaction"].round(2)
    return regions


def weekly_responses(df: pd.DataFrame) -> pd.DataFrame:
    """Antworten pro Woche (Wochen beginnen montags), Woche als "JJJJ-MM-TT"."""
    weekly = (
        df.resample("W-MON", on="submitted_at", label="left", closed="left")
        .size()
        .rename("responses")
        .reset_index()
        .rename(columns={"submitted_at": "week"})
    )
    weekly["week"] = weekly["week"].dt.strftime("%Y-%m-%d")
    return weekly


def summarize(df: pd.DataFrame) -> Summary:
    """Berechnet alle Kennzahlen für Dashboard, API und PDF-Bericht."""
    return {
        "kpis": kpis(df),
        "brands": _records(brand_stats(df)),
        "age_groups": _records(age_group_stats(df)),
        "channels": _records(channel_stats(df)),
        "regions": _records(region_stats(df)),
        "weekly": _records(weekly_responses(df)),
        "income": _records(income_stats(df)),
    }
