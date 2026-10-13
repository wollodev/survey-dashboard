"""Small sample CSVs for the tests."""

HEADER = (
    "response_id,submitted_at,age,gender,region,income_band,cups_per_day,"
    "preferred_brand,channel,monthly_spend_eur,satisfaction,nps_score,would_subscribe\n"
)

# 5 rows: one duplicate, one broken date, two outliers (spend 9999, NPS 99).
CSV = HEADER + (
    "1,2026-03-02 10:00:00,25,female,Berlin,not specified,2,Bohnenwerk,Subscription,30.5,5,10,yes\n"
    "2,2026-03-03 11:00:00,40,male,Bavaria,not specified,3,Röstzeit,Supermarket,12.0,3,6,no\n"
    "2,2026-03-03 11:00:00,40,male,Bavaria,not specified,3,Röstzeit,Supermarket,12.0,3,6,no\n"
    "3,unknown,55,diverse,Hesse,not specified,1,Morgenrot,Café,20.0,4,8,maybe\n"
    "4,2026-03-10 09:30:00,70,female,Hesse,not specified,1,Bohnenwerk,Café,9999,4,99,no\n"
)


def row(response_id: int, **values: object) -> str:
    """A valid CSV row; individual values can be overridden."""
    defaults: dict[str, object] = {
        "submitted_at": "2026-03-02 10:00:00",
        "age": 30,
        "gender": "female",
        "region": "Berlin",
        "income_band": "not specified",
        "cups_per_day": 2,
        "preferred_brand": "Bohnenwerk",
        "channel": "Subscription",
        "monthly_spend_eur": 20.0,
        "satisfaction": 4,
        "nps_score": 9,
        "would_subscribe": "yes",
    }
    fields = [response_id, *(defaults | values).values()]
    return ",".join("" if value is None else str(value) for value in fields) + "\n"
