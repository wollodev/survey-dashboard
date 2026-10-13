"""Small sample CSVs for the tests."""

HEADER = (
    "response_id,submitted_at,age,gender,region,income_band,cups_per_day,"
    "preferred_brand,channel,monthly_spend_eur,satisfaction,nps_score,would_subscribe\n"
)

# 5 rows: one duplicate, one broken date, two outliers (spend 9999, NPS 99).
CSV = HEADER + (
    "1,2026-03-02 10:00:00,25,weiblich,Berlin,keine Angabe,2,Bohnenwerk,Abo,30.5,5,10,ja\n"
    "2,2026-03-03 11:00:00,40,männlich,Bayern,keine Angabe,3,Röstzeit,Supermarkt,12.0,3,6,nein\n"
    "2,2026-03-03 11:00:00,40,männlich,Bayern,keine Angabe,3,Röstzeit,Supermarkt,12.0,3,6,nein\n"
    "3,unbekannt,55,divers,Hessen,keine Angabe,1,Morgenrot,Café,20.0,4,8,vielleicht\n"
    "4,2026-03-10 09:30:00,70,weiblich,Hessen,keine Angabe,1,Bohnenwerk,Café,9999,4,99,nein\n"
)


def row(response_id: int, **values: object) -> str:
    """A valid CSV row; individual values can be overridden."""
    defaults: dict[str, object] = {
        "submitted_at": "2026-03-02 10:00:00",
        "age": 30,
        "gender": "weiblich",
        "region": "Berlin",
        "income_band": "keine Angabe",
        "cups_per_day": 2,
        "preferred_brand": "Bohnenwerk",
        "channel": "Abo",
        "monthly_spend_eur": 20.0,
        "satisfaction": 4,
        "nps_score": 9,
        "would_subscribe": "ja",
    }
    fields = [response_id, *(defaults | values).values()]
    return ",".join("" if value is None else str(value) for value in fields) + "\n"
