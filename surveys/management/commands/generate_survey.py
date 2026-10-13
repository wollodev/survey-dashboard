"""
Generates a fictional market research survey on coffee consumption in Germany as CSV.

All brands, people and answers are made up. The data intentionally contains
typical errors from real surveys (duplicates, missing values, typos, outliers)
so there is something to clean up with pandas.

Usage:
    python manage.py generate_survey                 # 75,000 rows to survey.csv
    python manage.py generate_survey --rows 120000 --out gross.csv
"""

import csv
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandParser

from ...data.schema import COLUMN_TYPES

BRANDS = {
    # brand: (share, average satisfaction 1-5)
    "Bohnenwerk": (0.24, 4.1),
    "Röstzeit": (0.22, 3.7),
    "Morgenrot": (0.18, 3.4),
    "Hafenkaffee": (0.14, 3.9),
    "Private Label": (0.22, 3.1),
}

REGIONS = {
    # federal state: approximate share of the population
    "North Rhine-Westphalia": 0.215,
    "Bavaria": 0.158,
    "Baden-Württemberg": 0.134,
    "Lower Saxony": 0.097,
    "Hesse": 0.076,
    "Rhineland-Palatinate": 0.049,
    "Saxony": 0.048,
    "Berlin": 0.045,
    "Schleswig-Holstein": 0.035,
    "Brandenburg": 0.030,
    "Saxony-Anhalt": 0.026,
    "Thuringia": 0.025,
    "Hamburg": 0.022,
    "Mecklenburg-Western Pomerania": 0.019,
    "Saarland": 0.012,
    "Bremen": 0.008,
}

# How some federal states show up in poorly maintained data.
REGION_TYPOS = {
    "North Rhine-Westphalia": [
        "NRW",
        "Nordrhein-Westfalen",
        "north rhine-westphalia",
        "North Rhine-Westphalia ",
    ],
    "Bavaria": ["Bayern", "bavaria", " Bavaria"],
    "Baden-Württemberg": ["BW", "Baden-Wuerttemberg"],
    "Berlin": ["berlin", "Berlin "],
}

GENDERS = {"female": 0.49, "male": 0.48, "diverse": 0.01, "not specified": 0.02}
INCOME_BANDS = {
    "under €1,500": 0.17,
    "€1,500–2,999": 0.33,
    "€3,000–4,499": 0.27,
    "€4,500 and more": 0.15,
    "not specified": 0.08,
}

COLUMNS = list(COLUMN_TYPES)


def pick(rng: random.Random, weights: dict) -> str:
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def week_weights(weeks: int) -> list[float]:
    """How many responses arrive per week: ramp-up, newsletter spike, slow decline."""
    weights = []
    for week in range(weeks):
        weight = 1.0 - 0.02 * week
        if week < 3:
            weight *= (0.4, 0.7, 0.9)[week]
        if week == 11:
            weight *= 2.2  # newsletter with survey link
        weights.append(weight)
    return weights


def make_row(rng: random.Random, response_id: int, start: datetime, weights: list[float]) -> dict:
    age = min(79, max(18, int(rng.gauss(45, 15))))
    young = age < 35

    channel_weights = {
        "Supermarket": 0.40 if young else 0.52,
        "Online shop": 0.26 if young else 0.16,
        "Subscription": 0.16 if young else 0.10,
        "Café": 0.18 if young else 0.22,
    }
    channel = pick(rng, channel_weights)

    brand = rng.choices(list(BRANDS), weights=[share for share, _ in BRANDS.values()])[0]
    base = BRANDS[brand][1] + (age - 45) * 0.008  # older people are slightly more satisfied
    satisfaction = min(5, max(1, round(rng.gauss(base, 0.9))))

    # Satisfied customers are more likely to recommend (0-10).
    nps = min(10, max(0, round(satisfaction * 2 - 0.5 + rng.gauss(0, 1.4))))

    cups = min(8, max(0, round(rng.gauss(2.6 if age > 30 else 1.9, 1.3))))
    income_band = pick(rng, INCOME_BANDS)
    income_factor = {
        "under €1,500": 0.7,
        "€1,500–2,999": 0.9,
        "€3,000–4,499": 1.1,
        "€4,500 and more": 1.4,
    }
    price_per_cup = {"Supermarket": 0.22, "Online shop": 0.30, "Subscription": 0.38, "Café": 2.90}[channel]
    spend = cups * 30 * price_per_cup * income_factor.get(income_band, 1.0) * rng.uniform(0.6, 1.3)
    spend = round(max(0.0, spend), 2)

    subscribe_p = 0.12 + (0.18 if young else 0.0) + (0.35 if channel == "Subscription" else 0.0)
    roll = rng.random()
    would_subscribe = "yes" if roll < subscribe_p else ("maybe" if roll < subscribe_p + 0.25 else "no")

    week = rng.choices(range(len(weights)), weights=weights)[0]
    submitted_at = start + timedelta(weeks=week, seconds=rng.randrange(7 * 24 * 3600))

    return {
        "response_id": response_id,
        "submitted_at": submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
        "age": age,
        "gender": pick(rng, GENDERS),
        "region": pick(rng, REGIONS),
        "income_band": income_band,
        "cups_per_day": cups,
        "preferred_brand": brand,
        "channel": channel,
        "monthly_spend_eur": spend,
        "satisfaction": satisfaction,
        "nps_score": nps,
        "would_subscribe": would_subscribe,
    }


def add_noise(rng: random.Random, row: dict) -> dict:
    """Injects typical data errors."""
    if rng.random() < 0.02:
        row["cups_per_day"] = ""  # not answered
    if rng.random() < 0.03:
        row["monthly_spend_eur"] = ""  # not answered
    if rng.random() < 0.001:
        row["monthly_spend_eur"] = 9999.0  # typo during data entry
    if rng.random() < 0.001:
        row["nps_score"] = 99  # invalid value
    if rng.random() < 0.0005:
        row["submitted_at"] = "unknown"  # broken date
    if row["region"] in REGION_TYPOS and rng.random() < 0.04:
        row["region"] = rng.choice(REGION_TYPOS[row["region"]])
    return row


def write_survey(path: str, rows: int, seed: int) -> int:
    """Writes the survey as CSV and returns the number of rows written."""
    rng = random.Random(seed)
    start = datetime(2026, 3, 2)  # noqa: DTZ001 - a Monday; the survey stores local time without a time zone
    weights = week_weights(26)  # 26 weeks, March to August

    written = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for i in range(rows):
            row = add_noise(rng, make_row(rng, 100_001 + i, start, weights))
            writer.writerow(row)
            written += 1
            if rng.random() < 0.005:  # submitted twice
                writer.writerow(row)
                written += 1
    return written


class Command(BaseCommand):
    help = "Generates a fictional coffee survey as CSV (with intentional data errors)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--rows", type=int, default=75_000, help="number of responses (default: 75000)")
        parser.add_argument("--out", default="survey.csv", help="output file (default: survey.csv)")
        parser.add_argument("--seed", type=int, default=42, help="random seed (default: 42)")

    def handle(self, *args, rows: int, out: str, seed: int, **options) -> None:
        written = write_survey(out, rows, seed)
        self.stdout.write(self.style.SUCCESS(f"Wrote {written} rows to {out}."))
