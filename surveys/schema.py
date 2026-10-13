"""Aufbau einer Umfrage-CSV: Spalten, erlaubte Werte und feste Reihenfolgen.

Importer, Auswertung und Tests beziehen sich alle auf diese Definitionen.
"""

# Spalte -> Datentyp beim Einlesen. Ganzzahlige Antworten werden zunächst als float64
# gelesen: Das läuft bei Ausreißern wie 9999 nicht über (Int8 würde z. B. 300 still zu 44
# machen) und fehlende Werte werden zu NaN. Nach der Prüfung folgt INTEGER_COLUMNS.
COLUMN_TYPES = {
    "response_id": "int64",
    "submitted_at": "str",
    "age": "float64",
    "gender": "str",
    "region": "str",
    "income_band": "str",
    "cups_per_day": "float64",
    "preferred_brand": "str",
    "channel": "str",
    "monthly_spend_eur": "float64",
    "satisfaction": "float64",
    "nps_score": "float64",
    "would_subscribe": "str",
}

# Endgültiger Typ ganzzahliger Spalten. "Int8" (großes I) erlaubt fehlende Werte (pd.NA).
INTEGER_COLUMNS = {
    "age": "Int8",
    "cups_per_day": "Int8",
    "satisfaction": "Int8",
    "nps_score": "Int8",
}

# Erlaubte Wertebereiche (einschließlich). Alles außerhalb wird zu einem fehlenden Wert.
VALID_RANGES = {
    "age": (18, 99),
    "cups_per_day": (0, 20),
    "monthly_spend_eur": (0, 1000),
    "satisfaction": (1, 5),
    "nps_score": (0, 10),
}

# Spalten mit wenigen, sich wiederholenden Werten -> Typ "category" spart viel Speicher.
CATEGORY_COLUMNS = ["gender", "region", "income_band", "preferred_brand", "channel", "would_subscribe"]

# Antwort in "would_subscribe", die als Zustimmung zählt.
YES = "ja"

REGIONS = [
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

# Abkürzungen und Schreibvarianten, jeweils kleingeschrieben.
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

INCOME_ORDER = ["unter 1.500 €", "1.500–2.999 €", "3.000–4.499 €", "4.500 € und mehr", "keine Angabe"]

# Altersklassen: (17, 29] = 18–29, ..., (69, 99] = 70+. Die Obergrenze passt zu VALID_RANGES.
AGE_BINS = [17, 29, 39, 49, 59, 69, VALID_RANGES["age"][1]]
AGE_LABELS = ["18–29", "30–39", "40–49", "50–59", "60–69", "70+"]
