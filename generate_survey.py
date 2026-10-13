"""
Erzeugt eine fiktive Marktforschungsumfrage zum Kaffeekonsum als CSV.

Alle Marken, Personen und Antworten sind erfunden. Die Daten enthalten
absichtlich typische Fehler aus echten Umfragen (Dubletten, fehlende Werte,
Tippfehler, Ausreißer), damit es beim Bereinigen mit pandas etwas zu tun gibt.

Aufruf:
    python generate_survey.py                 # 75.000 Zeilen nach survey.csv
    python generate_survey.py --rows 120000 --out gross.csv
"""

import argparse
import csv
import random
from datetime import datetime, timedelta

BRANDS = {
    # Marke: (Anteil, durchschnittliche Zufriedenheit 1–5)
    "Bohnenwerk": (0.24, 4.1),
    "Röstzeit": (0.22, 3.7),
    "Morgenrot": (0.18, 3.4),
    "Hafenkaffee": (0.14, 3.9),
    "Eigenmarke": (0.22, 3.1),
}

REGIONS = {
    # Bundesland: ungefährer Anteil an der Bevölkerung
    "Nordrhein-Westfalen": 0.215,
    "Bayern": 0.158,
    "Baden-Württemberg": 0.134,
    "Niedersachsen": 0.097,
    "Hessen": 0.076,
    "Rheinland-Pfalz": 0.049,
    "Sachsen": 0.048,
    "Berlin": 0.045,
    "Schleswig-Holstein": 0.035,
    "Brandenburg": 0.030,
    "Sachsen-Anhalt": 0.026,
    "Thüringen": 0.025,
    "Hamburg": 0.022,
    "Mecklenburg-Vorpommern": 0.019,
    "Saarland": 0.012,
    "Bremen": 0.008,
}

# So tauchen manche Bundesländer in schlecht gepflegten Daten auf.
REGION_TYPOS = {
    "Nordrhein-Westfalen": ["NRW", "nordrhein-westfalen", "Nordrhein-Westfalen "],
    "Bayern": ["bayern", " Bayern"],
    "Baden-Württemberg": ["BW", "Baden-Wuerttemberg"],
    "Berlin": ["berlin", "Berlin "],
}

GENDERS = {"weiblich": 0.49, "männlich": 0.48, "divers": 0.01, "keine Angabe": 0.02}
INCOME_BANDS = {
    "unter 1.500 €": 0.17,
    "1.500–2.999 €": 0.33,
    "3.000–4.499 €": 0.27,
    "4.500 € und mehr": 0.15,
    "keine Angabe": 0.08,
}

COLUMNS = [
    "response_id",
    "submitted_at",
    "age",
    "gender",
    "region",
    "income_band",
    "cups_per_day",
    "preferred_brand",
    "channel",
    "monthly_spend_eur",
    "satisfaction",
    "nps_score",
    "would_subscribe",
]


def pick(rng: random.Random, weights: dict) -> str:
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def week_weights(weeks: int) -> list[float]:
    """Wie viele Antworten pro Woche eingehen: Anlauf, Newsletter-Spitze, langsames Abflauen."""
    weights = []
    for week in range(weeks):
        weight = 1.0 - 0.02 * week
        if week < 3:
            weight *= (0.4, 0.7, 0.9)[week]
        if week == 11:
            weight *= 2.2  # Newsletter mit Umfrage-Link
        weights.append(weight)
    return weights


def make_row(rng: random.Random, response_id: int, start: datetime, weights: list[float]) -> dict:
    age = min(79, max(18, int(rng.gauss(45, 15))))
    young = age < 35

    channel_weights = {
        "Supermarkt": 0.40 if young else 0.52,
        "Online-Shop": 0.26 if young else 0.16,
        "Abo": 0.16 if young else 0.10,
        "Café": 0.18 if young else 0.22,
    }
    channel = pick(rng, channel_weights)

    brand = rng.choices(list(BRANDS), weights=[share for share, _ in BRANDS.values()])[0]
    base = BRANDS[brand][1] + (age - 45) * 0.008  # Ältere sind etwas zufriedener
    satisfaction = min(5, max(1, round(rng.gauss(base, 0.9))))

    # Wer zufrieden ist, empfiehlt eher weiter (0–10).
    nps = min(10, max(0, round(satisfaction * 2 - 0.5 + rng.gauss(0, 1.4))))

    cups = min(8, max(0, round(rng.gauss(2.6 if age > 30 else 1.9, 1.3))))
    income_band = pick(rng, INCOME_BANDS)
    income_factor = {
        "unter 1.500 €": 0.7,
        "1.500–2.999 €": 0.9,
        "3.000–4.499 €": 1.1,
        "4.500 € und mehr": 1.4,
    }
    price_per_cup = {"Supermarkt": 0.22, "Online-Shop": 0.30, "Abo": 0.38, "Café": 2.90}[channel]
    spend = cups * 30 * price_per_cup * income_factor.get(income_band, 1.0) * rng.uniform(0.6, 1.3)
    spend = round(max(0.0, spend), 2)

    subscribe_p = 0.12 + (0.18 if young else 0.0) + (0.35 if channel == "Abo" else 0.0)
    roll = rng.random()
    would_subscribe = "ja" if roll < subscribe_p else ("vielleicht" if roll < subscribe_p + 0.25 else "nein")

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
    """Baut typische Datenfehler ein."""
    if rng.random() < 0.02:
        row["cups_per_day"] = ""  # nicht beantwortet
    if rng.random() < 0.03:
        row["monthly_spend_eur"] = ""  # nicht beantwortet
    if rng.random() < 0.001:
        row["monthly_spend_eur"] = 9999.0  # Tippfehler bei der Eingabe
    if rng.random() < 0.001:
        row["nps_score"] = 99  # ungültiger Wert
    if rng.random() < 0.0005:
        row["submitted_at"] = "unbekannt"  # kaputtes Datum
    if row["region"] in REGION_TYPOS and rng.random() < 0.04:
        row["region"] = rng.choice(REGION_TYPOS[row["region"]])
    return row


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--rows", type=int, default=75_000, help="Anzahl Antworten (Standard: 75000)")
    parser.add_argument("--out", default="survey.csv", help="Zieldatei (Standard: survey.csv)")
    parser.add_argument("--seed", type=int, default=42, help="Startwert für den Zufall")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    start = datetime(2026, 3, 2)  # noqa: DTZ001 – ein Montag; die Umfrage speichert Ortszeit ohne Zeitzone
    weights = week_weights(26)  # 26 Wochen, März bis August

    written = 0
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for i in range(args.rows):
            row = add_noise(rng, make_row(rng, 100_001 + i, start, weights))
            writer.writerow(row)
            written += 1
            if rng.random() < 0.005:  # doppelt abgeschickt
                writer.writerow(row)
                written += 1

    print(f"{written} Zeilen nach {args.out} geschrieben.")


if __name__ == "__main__":
    main()
