"""Survey analysis with pandas.

Each metric has its own small function; summarize() combines them.
Results are plain Python values (no NaN) so they can be serialized to JSON directly.
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
    """Loads a stored survey."""
    return pd.read_parquet(path)


def _round(value: Any, digits: int) -> float | None:
    """Rounds a number; missing values (None, NaN, pd.NA) become None."""
    if value is None or value is pd.NA or math.isnan(value):
        return None
    return round(float(value), digits)


def _records(df: pd.DataFrame) -> Rows:
    """DataFrame -> list of dicts, missing values as None (JSON: null)."""
    return cast(Rows, df.astype(object).where(df.notna(), None).to_dict("records"))


def net_promoter_score(scores: pd.Series) -> float | None:
    """NPS = share of promoters (9-10) minus share of detractors (0-6), in percentage points."""
    scores = scores.dropna()
    if scores.empty:
        return None
    promoters = (scores >= 9).mean()
    detractors = (scores <= 6).mean()
    return _round((promoters - detractors) * 100, 1)


def yes_rate(answers: pd.Series) -> float:
    """Share of "yes" answers in percent."""
    return float((answers == YES).mean() * 100)


def kpis(df: pd.DataFrame) -> Kpis:
    """The key metrics across all responses."""
    return {
        "responses": len(df),
        "avg_satisfaction": _round(df["satisfaction"].mean(), 2),
        "nps": net_promoter_score(df["nps_score"]),
        "avg_monthly_spend": _round(df["monthly_spend_eur"].mean(), 2),
        "subscribe_rate": _round(yes_rate(df["would_subscribe"]), 1),
    }


def brand_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Count, share, satisfaction and NPS per brand, largest brand first."""
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
    """Count, NPS and subscription willingness per age group."""
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
    """Median spend per income band, in natural order."""
    income_band = df["income_band"].cat.set_categories(INCOME_ORDER, ordered=True)
    income = (
        df.groupby(income_band, observed=True)
        .agg(responses=("response_id", "size"), median_spend=("monthly_spend_eur", "median"))
        .reset_index()
    )
    income["median_spend"] = income["median_spend"].round(2)
    return income


def channel_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Share of responses per purchase channel."""
    return (
        df["channel"]
        .value_counts(normalize=True)
        .mul(100)
        .round(1)
        .rename_axis("channel")
        .reset_index(name="share")
    )


def region_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Count and satisfaction per federal state, most responses first."""
    regions = (
        df.groupby("region", observed=True)
        .agg(responses=("response_id", "size"), avg_satisfaction=("satisfaction", "mean"))
        .sort_values("responses", ascending=False)
        .reset_index()
    )
    regions["avg_satisfaction"] = regions["avg_satisfaction"].round(2)
    return regions


def weekly_responses(df: pd.DataFrame) -> pd.DataFrame:
    """Responses per week (weeks start on Monday), week as "YYYY-MM-DD"."""
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
    """Computes all metrics for the dashboard, API and PDF report."""
    return {
        "kpis": kpis(df),
        "brands": _records(brand_stats(df)),
        "age_groups": _records(age_group_stats(df)),
        "channels": _records(channel_stats(df)),
        "regions": _records(region_stats(df)),
        "weekly": _records(weekly_responses(df)),
        "income": _records(income_stats(df)),
    }
