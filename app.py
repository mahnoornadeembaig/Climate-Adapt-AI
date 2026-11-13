import streamlit as st

st.set_page_config(
    page_title="ClimateAdaptAI",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 ClimateAdaptAI")
st.subheader("AI-Based Climate Adaptation Decision Simulator")

st.markdown(
    "An interdisciplinary research project combining "
    "Artificial Intelligence, climate science and data analysis."
)

st.divider()

st.header("📍 Research Case Study: Gujrat, Punjab, Pakistan")

st.write(
    "This project explores climate adaptation strategies "
    "for Gujrat using climate data, environmental indicators "
    "and evidence-based simulations."
)

col1, col2, col3 = st.columns(3)

col1.metric("Research Location", "Gujrat")
col2.metric("Research Domain", "Climate Adaptation")
col3.metric("Technical Approach", "AI & Data Science")

st.divider()

st.header("🌱 Explore Adaptation Strategies")

strategy = st.selectbox(
    "Select a climate adaptation strategy:",
    [
        "Urban Green Spaces",
        "Cool Roofs",
        "Rainwater Management"
    ]
)

st.write("Selected Strategy:", strategy)

st.info(
    "Evidence-based climate analysis and adaptation "
    "simulations will be developed in the next stages."
)

st.caption("ClimateAdaptAI | Research Case Study: Gujrat")
