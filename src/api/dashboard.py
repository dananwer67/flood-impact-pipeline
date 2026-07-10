import streamlit as st

from src.modeling.dummy_scorer import score_district_weeks


st.title("Flood Impact Dashboard")

df = score_district_weeks()

for _, row in df.iterrows():
    st.subheader(row["district_name"])
    st.metric("Final Urgency Score", row["final_urgency_score"])
    st.metric("River Discharge", row["river_discharge"])
    st.caption(row["report_text"])
