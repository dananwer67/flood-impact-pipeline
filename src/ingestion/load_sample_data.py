from src.ingestion.load_districts import load_pakistan_districts


def load_sample_district_weeks():
    districts = load_pakistan_districts()

    # FAKE PLACEHOLDER DATA below this point. district_id, district_name, and
    # geometry above are real (from GADM, via load_pakistan_districts). We haven't
    # built real hazard (GloFAS/CHIRPS) or text (ReliefWeb/GDELT) ingestion yet, so
    # every district gets the same placeholder values for now. river_discharge is
    # a non-zero constant so downstream max-based scaling doesn't divide by zero.
    districts["week_number"] = 1
    districts["river_discharge"] = 1.0
    districts["rainfall_72h"] = 0.0
    districts["report_text"] = "PLACEHOLDER - no real report text ingested yet."

    return districts