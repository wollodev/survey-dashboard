"""Auswertung einer Umfrage mit pandas."""

from pathlib import Path

import pandas as pd

AGE_BINS = [17, 29, 39, 49, 59, 69, 99]
AGE_LABELS = ["18–29", "30–39", "40–49", "50–59", "60–69", "70+"]

INCOME_ORDER = ["unter 1.500 €", "1.500–2.999 €", "3.000–4.499 €", "4.500 € und mehr", "keine Angabe"]


def load_survey(path: Path) -> pd.DataFrame:
    """Lädt eine gespeicherte Umfrage."""
    return pd.read_parquet(path)


def net_promoter_score(scores: pd.Series) -> float | None:
    """NPS = Anteil Promotoren (9-10) minus Anteil Kritiker (0-6), in Prozentpunkten."""
    scores = scores.dropna()
    if scores.empty:
        return None
    promoters = (scores >= 9).mean()
    detractors = (scores <= 6).mean()
    return round(float(promoters - detractors) * 100, 1)


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> Liste von dicts, fehlende Werte als None (JSON: null)."""
    return df.astype(object).where(df.notna(), None).to_dict("records")


def summarize(df: pd.DataFrame) -> dict:
    """Berechnet alle Kennzahlen für Dashboard und API."""
    total = len(df)

    kpis = {
        "responses": total,
        "avg_satisfaction": round(float(df["satisfaction"].mean()), 2),
        "nps": net_promoter_score(df["nps_score"]),
        "avg_monthly_spend": round(float(df["monthly_spend_eur"].mean()), 2),
        "subscribe_rate": round(float((df["would_subscribe"] == "ja").mean()) * 100, 1),
    }

    # Marken: Anzahl, Anteil, Zufriedenheit und NPS je Marke.
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
    brands["share"] = (brands["responses"] / total * 100).round(1)
    brands["avg_satisfaction"] = brands["avg_satisfaction"].round(2)

    # Altersgruppe: Alter in Klassen einteilen, dann gruppieren
    age_group = pd.cut(df["age"], bins=AGE_BINS, labels=AGE_LABELS)
    age_groups = (
        df.groupby(age_group, observed=True)
        .agg(
            responses=("response_id", "size"),
            nps=("nps_score", "mean"),
            subscribe_rate=("would_subscribe", lambda s: (s == "ja").mean() * 100),
        )
        .reset_index()
        .rename(columns={"age": "age_group"})
    )
    age_groups["subscribe_rate"] = age_groups["subscribe_rate"].round(1)

    # Einkommen: Median der Ausgaben je Einkommensgruppe, in natürlicher Reihenfolge.
    income = (
        df.assign(income_band=df["income_band"].cat.set_categories(INCOME_ORDER, ordered=True))
        .groupby("income_band", observed=True)
        .agg(responses=("response_id", "size"), median_spend=("monthly_spend_eur", "median"))
        .reset_index()
    )
    income["median_spend"] = income["median_spend"].round(2)

    # Kanäle: Anteil der Antworten je Einkaufskanal.
    channels = (
        df["channel"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .rename_axis("channel")
        .reset_index(name="share")
    )

    # Regionen: Anzahl und Zufriedenheit je Bundesland.
    regions = (
        df.groupby("region", observed=True)
        .agg(responses=("response_id", "size"), avg_satisfaction=("satisfaction", "mean"))
        .sort_values("responses", ascending=False)
        .reset_index()
    )
    regions["avg_satisfaction"] = regions["avg_satisfaction"].round(2)

    # Zeitverlauf: Antworten pro Woche (Wochen beginnen montags).
    weekly = (
        df.resample("W-MON", on="submitted_at", label="left", closed="left")
        .size()
        .rename("responses")
        .reset_index()
        .rename(columns={"submitted_at": "week"})
    )
    weekly["week"] = weekly["week"].dt.strftime("%Y-%m-%d")

    return {
        "kpis": kpis,
        "brands": _records(brands),
        "age_groups": _records(age_groups),
        "channels": _records(channels),
        "regions": _records(regions),
        "weekly": _records(weekly),
        "income": _records(income),
    }
