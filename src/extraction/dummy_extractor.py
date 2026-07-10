def dummy_extract_urgency(report_text):
    keywords = ["flooding", "damage", "wash", "nfi", "critical"]

    text_lower = report_text.lower()
    match_count = sum(1 for keyword in keywords if keyword in text_lower)

    urgency_score = (match_count / len(keywords)) * 100

    return {"urgency_score": urgency_score}
