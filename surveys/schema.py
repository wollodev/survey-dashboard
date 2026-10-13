"""Structure of a survey CSV: columns, allowed values and fixed orderings.

The importer, the analysis and the tests all refer to these definitions.
"""

# Column -> dtype when reading. Integer answers are read as float64 first: this doesn't
# overflow on outliers like 9999 (Int8 would silently turn e.g. 300 into 44), and missing
# values become NaN. After validation the columns are converted to INTEGER_COLUMNS.
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

# Final dtype of integer columns. "Int8" (capital I) allows missing values (pd.NA).
INTEGER_COLUMNS = {
    "age": "Int8",
    "cups_per_day": "Int8",
    "satisfaction": "Int8",
    "nps_score": "Int8",
}

# Allowed value ranges (inclusive). Anything outside becomes a missing value.
VALID_RANGES = {
    "age": (18, 99),
    "cups_per_day": (0, 20),
    "monthly_spend_eur": (0, 1000),
    "satisfaction": (1, 5),
    "nps_score": (0, 10),
}

# Columns with few, repeating values -> dtype "category" saves a lot of memory.
CATEGORY_COLUMNS = ["gender", "region", "income_band", "preferred_brand", "channel", "would_subscribe"]

# Answer in "would_subscribe" that counts as yes.
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

# Abbreviations and spelling variants, all lowercase.
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

# Age bins: (17, 29] = 18-29, ..., (69, 99] = 70+. The upper bound matches VALID_RANGES.
AGE_BINS = [17, 29, 39, 49, 59, 69, VALID_RANGES["age"][1]]
AGE_LABELS = ["18–29", "30–39", "40–49", "50–59", "60–69", "70+"]
