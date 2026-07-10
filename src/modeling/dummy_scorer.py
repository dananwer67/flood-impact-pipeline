from src.ingestion.load_sample_data import load_sample_district_weeks
from src.extraction.dummy_extractor import dummy_extract_urgency


def score_district_weeks():
    df = load_sample_district_weeks()

    df["urgency_score"] = df["report_text"].apply(
        lambda text: dummy_extract_urgency(text)["urgency_score"]
    )

    max_discharge = df["river_discharge"].max()
    river_discharge_score = (df["river_discharge"] / max_discharge) * 100

    df["final_urgency_score"] = (df["urgency_score"] + river_discharge_score) / 2

    df = df.sort_values("final_urgency_score", ascending=False)

    return df
