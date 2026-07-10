import pandas as pd


def load_sample_district_weeks():
    data = [
        {
            "district_id": "PK-SD-DADU",
            "district_name": "Dadu",
            "week_number": 34,
            "river_discharge": 1250.5,
            "rainfall_72h": 180.2,
            "report_text": "Heavy flooding reported along the Indus near Dadu; WASH and NFI interventions requested.",
        },
        {
            "district_id": "PK-SD-SANGHAR",
            "district_name": "Sanghar",
            "week_number": 34,
            "river_discharge": 980.3,
            "rainfall_72h": 145.7,
            "report_text": "Localized flooding in low-lying areas of Sanghar; several villages report crop damage.",
        },
        {
            "district_id": "PK-PB-MULTAN",
            "district_name": "Multan",
            "week_number": 35,
            "river_discharge": 610.8,
            "rainfall_72h": 60.4,
            "report_text": "River levels near Multan remain within normal range; no major impact reported this week.",
        },
    ]

    return pd.DataFrame(data)
