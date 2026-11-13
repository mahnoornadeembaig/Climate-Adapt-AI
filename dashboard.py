import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from auth import authenticate_user, initialize_auth_db, register_user
from climate_model import train_city_forecasts
from recommendations import (
    climate_analysis_recommendations,
    cool_roof_recommendations,
    green_space_recommendations,
    rainwater_recommendations,
)
from reporting import (
    build_csv_report,
    build_pdf_report,
    report_filename,
    user_friendly_dataframe,
)


# =========================================================
# 1. PATHS AND PAGE CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
COMPARISON_DIR = OUTPUT_DIR / "source_comparison"
TREND_DIR = OUTPUT_DIR / "climate_trends"
DB_PATH = BASE_DIR / "climateadaptai.db"
DEVELOPER_MODE = os.getenv(
    "CLIMATEADAPTAI_DEVELOPER_MODE",
    "",
).strip().lower() in {"1", "true", "yes"}

st.set_page_config(
    page_title="Climate Adapt AI Simulator | Climate Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_auth_db(DB_PATH)


# =========================================================
# 2. CUSTOM DESIGN
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #f4f7f5;
}

.block-container {
    padding-top: 1.8rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #102c27 0%, #163d32 100%);
}

[data-testid="stSidebar"] * {
    color: #f1f8f4 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 9px 12px;
    border-radius: 9px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.12);
}

/* CITY SELECTBOX */

[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] {
    color-scheme: light;
    background-color: #ffffff !important;
    border: 1px solid #cbd8d0 !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] {
    background-color: transparent !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"]::placeholder {
    color: #555555 !important;
    -webkit-text-fill-color: #555555 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

[data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder {
    color: #555555 !important;
    -webkit-text-fill-color: #555555 !important;
    opacity: 1 !important;
}

[data-testid="stAlert"],
[data-testid="stAlert"] * {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] button[aria-label="Clear value"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] button[aria-label="Open"] {
    background-color: #eaf3ed !important;
    color: #173c31 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] button[aria-label="Clear value"] svg,
[data-testid="stSidebar"] [data-testid="stSelectbox"] button[aria-label="Open"] svg {
    color: #173c31 !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] button[aria-label="Clear value"] svg path:not([fill="none"]),
[data-testid="stSidebar"] [data-testid="stSelectbox"] button[aria-label="Open"] svg path:not([fill="none"]) {
    fill: #173c31 !important;
}

[role="listbox"] {
    background-color: #ffffff !important;
}

[role="option"] {
    background-color: #ffffff !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

[role="option"] * {
    background-color: transparent !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}

[role="option"]:hover,
[role="option"][data-focused="true"] {
    background-color: #eaf3ed !important;
}

[role="option"][aria-selected="true"],
[role="option"][aria-selected="true"] * {
    background-color: #dceee3 !important;
    color: #111111 !important;
}

/* HERO */

.hero {
    background: linear-gradient(120deg, #123b30 0%, #1c654c 60%, #2d8260 100%);
    padding: 34px 38px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 10px 28px rgba(18,59,48,0.15);
}

.hero h1 {
    color: white !important;
    font-size: 36px;
    font-weight: 800;
    margin: 0 0 8px 0;
}

.hero p {
    color: #e1f2e8;
    font-size: 15px;
    margin: 0;
}

.hero-tag {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    padding: 7px 13px;
    border-radius: 30px;
    font-size: 12px;
    margin-bottom: 15px;
}

/* SECTION TITLES */

.section-title {
    color: #173c31;
    font-size: 22px;
    font-weight: 800;
    margin: 24px 0 13px 0;
}

/* METRIC CARDS */

.metric-card {
    background: white;
    border: 1px solid #e4ece7;
    border-radius: 15px;
    padding: 17px 19px;
    min-height: 115px;
    box-shadow: 0 4px 14px rgba(20,55,42,0.045);
}

.metric-label {
    color: #718078;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 9px;
}

.metric-value {
    color: #173c31;
    font-size: 25px;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.metric-icon {
    font-size: 21px;
    margin-bottom: 7px;
}

/* INFORMATION CARDS */

.info-card {
    background: white;
    border: 1px solid #e4ece7;
    border-radius: 15px;
    padding: 19px;
    min-height: 145px;
    box-shadow: 0 4px 14px rgba(20,55,42,0.04);
}

.info-card h3 {
    color: #1b4939;
    font-size: 17px;
    margin-bottom: 8px;
}

.info-card p {
    color: #718078;
    font-size: 13px;
    line-height: 1.6;
}

/* NOTES */

.small-note {
    background: #eaf3ed;
    border-left: 4px solid #2d8260;
    border-radius: 8px;
    padding: 13px 16px;
    color: #315344;
    font-size: 13px;
    margin: 14px 0;
}

/* FOOTER */

.footer {
    text-align: center;
    color: #829087;
    font-size: 12px;
    padding: 20px 0 5px 0;
}

/* CHARTS */

div[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid #e4ece7;
    border-radius: 14px;
    padding: 10px;
    box-shadow: 0 4px 14px rgba(20,55,42,0.035);
}

/* BUTTONS */

.stButton button,
.stFormSubmitButton button {
    background: #1c654c;
    color: white;
    border-radius: 9px;
    border: none;
    font-weight: 600;
    padding: 8px 20px;
}

.stButton button:hover,
.stFormSubmitButton button:hover {
    background: #123b30;
    color: white;
}

h1, h2, h3 {
    color: #173c31;
}

.auth-logo {
    width: 64px;
    height: 64px;
    margin: 20px auto 14px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 20px;
    background: #e3efe7;
    font-size: 34px;
}

.auth-title {
    margin: 0;
    color: #173c31;
    font-size: 32px;
    font-weight: 800;
    line-height: 1.15;
    text-align: center;
}

.auth-description {
    margin: 0 0 18px 0;
    color: #52665b;
    text-align: center;
}

[data-testid="stForm"] {
    padding: 22px;
    border: 1px solid #dce8e0;
    border-radius: 16px;
    background: #ffffff;
    box-shadow: 0 10px 28px rgba(27, 62, 45, 0.08);
}

[data-testid="stForm"] input {
    color: #17241d !important;
    background: #ffffff !important;
}

[data-testid="stForm"] label,
[data-testid="stForm"] [data-testid="stCaptionContainer"] {
    color: #263d31 !important;
}

[data-testid="stTabs"] [role="tab"] {
    color: #40564a;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #176443 !important;
    border-bottom-color: #176443 !important;
}

[data-testid="stTabs"] .react-aria-SelectionIndicator {
    background: #176443 !important;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.get("dark_mode", False):
    st.markdown("""
    <style>
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: #111a16 !important;
        color: #e4eee8 !important;
    }

    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] .section-title,
    [data-testid="stMain"] .metric-value,
    [data-testid="stMain"] .info-card h3,
    [data-testid="stMain"] .auth-title {
        color: #e4eee8 !important;
    }

    [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] li {
        color: #c5d2ca !important;
    }

    [data-testid="stMain"] .hero h1,
    [data-testid="stMain"] .hero p,
    [data-testid="stMain"] .hero-tag {
        color: #ffffff !important;
    }

    [data-testid="stMain"] .metric-card,
    [data-testid="stMain"] .info-card,
    [data-testid="stMain"] [data-testid="stForm"],
    [data-testid="stMain"] div[data-testid="stPlotlyChart"] {
        background-color: #1b2821 !important;
        border-color: #33463b !important;
        color: #e4eee8 !important;
    }

    [data-testid="stMain"] .metric-label,
    [data-testid="stMain"] .info-card p,
    [data-testid="stMain"] .footer {
        color: #aab9af !important;
    }

    [data-testid="stMain"] .small-note {
        background-color: #20352a !important;
        border-left-color: #57a47b !important;
        color: #d7e6dc !important;
    }

    [data-testid="stMain"] [data-testid="stAlert"],
    [data-testid="stMain"] [data-testid="stAlert"] * {
        background-color: #26352d !important;
        border-color: #40564a !important;
        color: #e4eee8 !important;
        -webkit-text-fill-color: #e4eee8 !important;
    }

    [data-testid="stMain"] [data-testid="stForm"] input {
        background-color: #25332b !important;
        color: #e4eee8 !important;
        -webkit-text-fill-color: #e4eee8 !important;
    }

    [data-testid="stMain"] [data-testid="stForm"] label,
    [data-testid="stMain"] [data-testid="stForm"] [data-testid="stCaptionContainer"] {
        color: #d5e0d9 !important;
    }

    [data-testid="stMain"] [data-testid="stTabs"] [role="tab"] {
        color: #c5d2ca !important;
    }

    [data-testid="stMain"] [data-testid="stDataFrame"] {
        border: 1px solid #33463b;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


def render_auth_page():
    _, auth_column, _ = st.columns([1, 1.25, 1])

    with auth_column:
        st.markdown(
            '<div class="auth-logo">🌿</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h1 class="auth-title">Climate Adapt AI Simulator</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="auth-description">Sign in or create an account to '
            'explore climate insights and adaptation scenarios.</p>',
            unsafe_allow_html=True,
        )
        login_tab, register_tab = st.tabs(["Login", "Create account"])

        with login_tab:
            with st.form("login_form"):
                login_identifier = st.text_input(
                    "Username or email",
                    key="login_identifier",
                )
                login_password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                )
                login_submitted = st.form_submit_button(
                    "Log in",
                    width="stretch",
                )

            if login_submitted:
                authenticated_user = authenticate_user(
                    DB_PATH,
                    login_identifier,
                    login_password,
                )
                if authenticated_user:
                    st.session_state["authenticated_user_v2"] = (
                        authenticated_user
                    )
                    st.rerun()
                else:
                    st.error("Incorrect username/email or password.")

        with register_tab:
            with st.form("register_form"):
                register_username = st.text_input(
                    "Username",
                    key="register_username",
                )
                register_email = st.text_input(
                    "Email",
                    key="register_email",
                )
                register_password = st.text_input(
                    "Password",
                    type="password",
                    key="register_password",
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    key="register_password_confirm",
                )
                st.caption("Use a password between 8 and 128 characters.")
                register_submitted = st.form_submit_button(
                    "Create account",
                    width="stretch",
                )

            if register_submitted:
                if register_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        account_created = register_user(
                            DB_PATH,
                            register_username,
                            register_email,
                            register_password,
                        )
                    except ValueError as error:
                        st.error(str(error))
                    else:
                        if account_created:
                            st.session_state["authenticated_user_v2"] = (
                                register_username.strip().lower()
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Username or email is already registered."
                            )


authenticated_user = st.session_state.get("authenticated_user_v2")
if not authenticated_user:
    render_auth_page()
    st.stop()
else:
    for password_key in (
        "login_password",
        "register_password",
        "register_password_confirm",
    ):
        st.session_state.pop(password_key, None)


# =========================================================
# 3. DATA LOADING FUNCTIONS
# =========================================================

@st.cache_data
def load_csv(file_path):

    path = Path(file_path)

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)

    except Exception:
        return pd.DataFrame()


@st.cache_data
def load_db_table(table_name):

    allowed_tables = {
        "climate_records",
        "annual_summary",
        "monthly_summary",
        "rainwater_scenarios",
        "urban_green_space_scenarios",
        "cool_roof_scenarios",
        "multi_city_climate_records",
        "multi_city_annual_summary",
        "multi_city_monthly_summary"
    }

    if table_name not in allowed_tables:
        return pd.DataFrame()

    if not DB_PATH.exists():
        return pd.DataFrame()

    try:
        with closing(sqlite3.connect(DB_PATH)) as connection:
            return pd.read_sql_query(
                f"SELECT * FROM {table_name}",
                connection
            )

    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame()


def find_column(dataframe, possible_names):

    if dataframe.empty:
        return None

    normalized = {
        str(column).strip().lower(): column
        for column in dataframe.columns
    }

    for name in possible_names:

        key = name.strip().lower()

        if key in normalized:
            return normalized[key]

    return None


def standardize_annual(dataframe):

    if dataframe.empty:
        return pd.DataFrame()

    df = dataframe.copy()

    aliases = {
        "location": ["location", "city", "city_name"],
        "year": ["year"],
        "avg_tmax_c": [
            "avg_tmax_c",
            "mean_tmax_c",
            "average_tmax_c",
            "nasa_mean_tmax_c"
        ],
        "avg_tmin_c": [
            "avg_tmin_c",
            "mean_tmin_c",
            "average_tmin_c"
        ],
        "avg_tmean_c": [
            "avg_tmean_c",
            "mean_tmean_c",
            "average_temperature_c",
            "nasa_mean_temperature",
            "mean_temperature_c"
        ],
        "annual_rainfall_mm": [
            "annual_rainfall_mm",
            "total_rainfall_mm",
            "annual_precipitation_mm",
            "nasa_total_rainfall"
        ]
    }

    rename_map = {}

    for standard_name, candidates in aliases.items():

        actual = find_column(df, candidates)

        if actual and actual != standard_name:
            rename_map[actual] = standard_name

    df = df.rename(columns=rename_map)

    if "year" in df.columns:
        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

    for column in [
        "avg_tmax_c",
        "avg_tmin_c",
        "avg_tmean_c",
        "annual_rainfall_mm"
    ]:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def standardize_monthly(dataframe):

    if dataframe.empty:
        return pd.DataFrame()

    df = dataframe.copy()

    aliases = {
        "location": ["location", "city", "city_name"],
        "month": ["month"],
        "avg_tmax_c": ["avg_tmax_c", "mean_tmax_c"],
        "avg_tmin_c": ["avg_tmin_c", "mean_tmin_c"],
        "avg_tmean_c": ["avg_tmean_c", "mean_tmean_c"],
        "avg_monthly_rainfall_mm": [
            "avg_monthly_rainfall_mm",
            "monthly_rainfall_mm",
            "mean_rainfall_mm"
        ]
    }

    rename_map = {}

    for standard_name, candidates in aliases.items():

        actual = find_column(df, candidates)

        if actual and actual != standard_name:
            rename_map[actual] = standard_name

    df = df.rename(columns=rename_map)

    if "month" in df.columns:

        df["month"] = pd.to_numeric(
            df["month"],
            errors="coerce"
        )

    for column in [
        "avg_tmax_c",
        "avg_tmin_c",
        "avg_tmean_c",
        "avg_monthly_rainfall_mm"
    ]:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# =========================================================
# 4. LOAD PROJECT DATA
# =========================================================

multi_city_daily = load_csv(
    DATA_DIR / "multi_city_climate_data.csv"
)

multi_city_annual = load_csv(
    DATA_DIR / "multi_city_annual_summary.csv"
)

multi_city_monthly = load_csv(
    DATA_DIR / "multi_city_monthly_summary.csv"
)

era5_daily = load_csv(
    DATA_DIR / "open_meteo_climate_data.csv"
)

daily_comparison = load_csv(
    COMPARISON_DIR / "daily_source_comparison.csv"
)

city_comparison = load_csv(
    COMPARISON_DIR / "city_source_comparison.csv"
)

annual_comparison = load_csv(
    COMPARISON_DIR / "annual_source_comparison.csv"
)

monthly_comparison = load_csv(
    COMPARISON_DIR / "monthly_source_comparison.csv"
)

annual_trends = load_csv(
    TREND_DIR / "annual_climate_trends.csv"
)

monthly_climatology = load_csv(
    TREND_DIR / "monthly_climate_climatology.csv"
)

long_term_trends = load_csv(
    TREND_DIR / "city_long_term_trend_summary.csv"
)

extreme_summary = load_csv(
    TREND_DIR / "extreme_weather_summary.csv"
)

climate_db = load_db_table("climate_records")
annual_db = load_db_table("annual_summary")
monthly_db = load_db_table("monthly_summary")

rainwater_db = load_db_table("rainwater_scenarios")
green_db = load_db_table("urban_green_space_scenarios")
cool_roof_db = load_db_table("cool_roof_scenarios")


# =========================================================
# 5. PREPARE ANNUAL AND MONTHLY DATA
# =========================================================

if not multi_city_annual.empty:

    annual_data = standardize_annual(
        multi_city_annual
    )

else:

    annual_data = standardize_annual(
        annual_db
    )


if not multi_city_monthly.empty:

    monthly_data = standardize_monthly(
        multi_city_monthly
    )

else:

    monthly_data = standardize_monthly(
        monthly_db
    )


if annual_data.empty and not annual_db.empty:

    annual_data = standardize_annual(
        annual_db
    )


if monthly_data.empty and not monthly_db.empty:

    monthly_data = standardize_monthly(
        monthly_db
    )


# =========================================================
# 6. HELPER FUNCTIONS
# =========================================================

def metric_card(label, value, icon):

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def info_card(title, description, icon):

    st.markdown(f"""
    <div class="info-card">
        <div style="font-size:27px;margin-bottom:9px;">{icon}</div>
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


def section_title(title):

    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True
    )


def show_ai_recommendations(recommendations):

    section_title("Practical adaptation suggestions")
    st.caption(
        "Based on transparent local rules and historical data; use as "
        "planning guidance, not as a guaranteed outcome."
    )

    for recommendation in recommendations:
        st.markdown(f"- {recommendation}")


def style_chart(fig):
    dark_mode = st.session_state.get("dark_mode", False)
    text_color = "#dce8e0" if dark_mode else "#40564b"
    title_color = "#e4eee8" if dark_mode else "#173c31"
    chart_background = "#111a16" if dark_mode else "rgba(0,0,0,0)"
    grid_color = "#33463b" if dark_mode else "#e9efeb"

    fig.update_layout(
        template="plotly_dark" if dark_mode else "plotly_white",
        font=dict(
            family="DM Sans",
            color=text_color
        ),
        title_font=dict(
            size=18,
            color=title_color
        ),
        paper_bgcolor=chart_background,
        plot_bgcolor=chart_background,
        margin=dict(
            l=20,
            r=20,
            t=55,
            b=20
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=grid_color)

    return fig


def show_table(dataframe, technical=False):

    if dataframe.empty:

        st.info("No records available.")
        return

    st.dataframe(
        dataframe if technical else user_friendly_dataframe(dataframe),
        width="stretch",
        hide_index=True
    )


def render_download_controls(title, city, tables, notes=None):
    available_tables = [
        (section, dataframe)
        for section, dataframe in tables
        if not dataframe.empty
    ]
    if not available_tables:
        return

    csv_report = build_csv_report(title, city, available_tables)
    pdf_report = build_pdf_report(
        title,
        city,
        available_tables,
        notes,
    )
    report_key = report_filename(title, city, "file").replace(".", "_")
    st.markdown("#### Download this report")
    st.caption(
        "CSV is ready for spreadsheets; PDF is a printable summary."
    )
    csv_column, pdf_column = st.columns(2)
    with csv_column:
        st.download_button(
            "Download CSV",
            data=csv_report,
            file_name=report_filename(title, city, "csv"),
            mime="text/csv",
            key=f"{report_key}_csv",
            on_click="ignore",
            width="stretch",
        )
    with pdf_column:
        st.download_button(
            "Download PDF",
            data=pdf_report,
            file_name=report_filename(title, city, "pdf"),
            mime="application/pdf",
            key=f"{report_key}_pdf",
            on_click="ignore",
            width="stretch",
        )


def save_simulation_report(city, section, tables):
    reports = st.session_state.setdefault("simulation_reports", {})
    reports[f"{city}::{section}"] = {
        "city": city,
        "section": section,
        "tables": tables,
    }


@st.cache_resource(show_spinner="Training the climate prediction model...")
def cached_climate_forecasts(daily_data):
    return train_city_forecasts(daily_data)


def filter_city(dataframe, city):

    if dataframe.empty:
        return pd.DataFrame()

    location_column = find_column(
        dataframe,
        ["location", "city", "city_name"]
    )

    if location_column is None:
        return dataframe.copy()

    return dataframe[
        dataframe[location_column].astype(str) == city
    ].copy()


def get_year_options(dataframe):

    if dataframe.empty or "year" not in dataframe.columns:
        return []

    return sorted(
        dataframe["year"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )


def get_selected_rainfall(dataframe, city, year):

    if dataframe.empty:
        return None

    selected = filter_city(dataframe, city)

    if selected.empty:
        return None

    selected = selected[
        selected["year"] == year
    ]

    if selected.empty:
        return None

    if "annual_rainfall_mm" not in selected.columns:
        return None

    value = selected.iloc[0]["annual_rainfall_mm"]

    if pd.isna(value):
        return None

    return float(value)


# =========================================================
# 7. CITY SELECTION AND SIDEBAR
# =========================================================

if (
    not annual_data.empty
    and "location" in annual_data.columns
):

    city_options = sorted(
        annual_data["location"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

elif (
    not multi_city_daily.empty
    and "location" in multi_city_daily.columns
):

    city_options = sorted(
        multi_city_daily["location"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

else:

    city_options = [
        "Gujrat, Punjab, Pakistan"
    ]

if not city_options:
    city_options = ["Gujrat, Punjab, Pakistan"]

default_city = "Gujrat, Punjab, Pakistan"
if default_city not in city_options:
    default_city = city_options[0]

if "_research_city_selector_initialized" not in st.session_state:
    st.session_state["research_city_selector"] = None
    st.session_state["_research_city_selector_initialized"] = True

navigation_pages = [
    "Overview",
    "Compare Cities",
    "Compare Data Sources",
    "Climate Trends & Extreme Weather",
    "Climate Predictions",
    "Adaptation Simulations",
    "Saved Scenario Results",
    "Climate Insights & Data Coverage",
]
if DEVELOPER_MODE:
    navigation_pages.append("Developer: Database Information")


with st.sidebar:

    st.markdown("""
    <div style="padding:12px 5px 20px 5px;">
        <div style="font-size:34px;">🌿</div>
        <div style="font-size:19px;font-weight:800;line-height:1.2;">
            Climate Adapt AI Simulator
        </div>
        <div style="font-size:11px;color:#c0d8cb;">
            CLIMATE INTELLIGENCE
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ACCOUNT")
    st.caption(f"Signed in as {authenticated_user}")
    if st.button("Log out", key="logout_button", width="stretch"):
        del st.session_state["authenticated_user_v2"]
        st.rerun()
    st.toggle(
        "Dark mode",
        key="dark_mode",
        help="Switch between light and dark appearance.",
    )

    st.markdown("---")
    st.markdown("### CHOOSE A CITY")

    selected_city = st.selectbox(
        "Select City",
        city_options,
        index=None,
        placeholder="",
        key="research_city_selector"
    )

    st.markdown("---")
    st.markdown("### NAVIGATION")

    page = st.radio(
        "Explore Climate Tools",
        navigation_pages,
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("""
    <div style="font-size:12px;line-height:1.8;color:#d6e9dc;">
        <b>DATA PERIOD</b><br>
        2001 – 2024<br><br>
        <b>CLIMATE DATA SOURCES</b><br>
        NASA POWER<br>
        Open-Meteo ERA5<br><br>
        <b>STUDY AREA</b><br>
        Five cities in Pakistan
    </div>
    """, unsafe_allow_html=True)


if selected_city is None:
    selected_city = default_city
    st.info(
        "No city selected. Showing data for "
        f"{selected_city}; choose a city in the sidebar to switch locations."
    )


selected_annual = filter_city(
    annual_data,
    selected_city
)

selected_monthly = filter_city(
    monthly_data,
    selected_city
)

report_title = page
report_tables = []
report_notes = []


# =========================================================
# 8. MAIN HERO
# =========================================================

st.markdown(f"""
<div class="hero">
    <div class="hero-tag">
        🌍 CLIMATE INTELLIGENCE & ADAPTATION
    </div>
    <h1>Climate Adapt AI Simulator</h1>
    <p>Climate insights and adaptation decision support</p>
    <p style="margin-top:14px;font-size:13px;">
        Selected Research Location: {selected_city}
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# 9. OVERVIEW
# =========================================================

if page == "Overview":

    section_title("Climate Research at a Glance")
    report_title = "Climate summary"
    report_tables = [
        ("Annual climate history", selected_annual),
        ("Monthly climate averages", selected_monthly),
    ]
    report_notes = [
        "Historical gridded climate estimates are not direct local "
        "weather-station observations."
    ]

    total_daily_records = (
        len(multi_city_daily)
        if not multi_city_daily.empty
        else len(climate_db)
    )

    number_of_cities = len(city_options)

    years_available = get_year_options(
        selected_annual
    )

    first_year = (
        min(years_available)
        if years_available
        else 2001
    )

    last_year = (
        max(years_available)
        if years_available
        else 2024
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Daily Climate Records",
            f"{total_daily_records:,}",
            "📊"
        )

    with c2:
        metric_card(
            "Cities Analyzed",
            str(number_of_cities),
            "📍"
        )

    with c3:
        metric_card(
            "Study Period",
            f"{first_year}–{last_year}",
            "📅"
        )

    with c4:
        metric_card(
            "Climate Data Sources",
            "02",
            "🌐"
        )

    section_title("Explore Climate Adaptation Strategies")

    c1, c2, c3 = st.columns(3)

    with c1:
        info_card(
            "Rainwater Management",
            "Estimate rooftop rainwater harvesting using historical rainfall and selected collection assumptions.",
            "💧"
        )

    with c2:
        info_card(
            "Urban Green Spaces",
            "Compare estimated rainwater availability with green-space irrigation demand.",
            "🌳"
        )

    with c3:
        info_card(
            "Cool Roofs",
            "Explore cool-roof coverage scenarios for urban planning.",
            "🏠"
        )

    if not selected_annual.empty:

        latest = selected_annual.sort_values(
            "year"
        ).iloc[-1]

        section_title(
            f"Latest Available Climate Snapshot — {selected_city}"
        )

        a, b, c = st.columns(3)

        with a:
            metric_card(
                "Latest Data Year",
                str(int(latest["year"])),
                "📅"
            )

        with b:

            value = latest.get("avg_tmean_c")

            metric_card(
                "Mean Temperature",
                f"{value:.2f} °C"
                if pd.notna(value)
                else "N/A",
                "🌡️"
            )

        with c:

            value = latest.get("annual_rainfall_mm")

            metric_card(
                "Annual Rainfall",
                f"{value:,.1f} mm"
                if pd.notna(value)
                else "N/A",
                "🌧️"
            )

        if "avg_tmean_c" in selected_annual.columns:

            section_title("Annual Mean Temperature")

            fig = px.line(
                selected_annual.sort_values("year"),
                x="year",
                y="avg_tmean_c",
                markers=True,
                labels={
                    "year": "Year",
                    "avg_tmean_c": "Mean Temperature (°C)"
                }
            )

            fig.update_traces(
                line=dict(
                    color="#21845b",
                    width=3
                ),
                marker=dict(size=7)
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch",
                config={"displayModeBar": False}
            )

    else:

        st.warning(
            "Annual climate history is not available yet. Please try "
            "another city or contact the project administrator."
        )

    st.markdown("""
    <div class="small-note">
        <b>Research note:</b> NASA POWER and Open-Meteo ERA5 provide
        gridded climate estimates. They should not be interpreted as
        direct measurements from local weather stations.
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# 10. MULTI-CITY CLIMATE ANALYSIS
# =========================================================

elif page == "Compare Cities":

    report_title = "City climate history"
    report_tables = [
        ("Annual climate history", selected_annual),
        ("Monthly climate averages", selected_monthly),
    ]
    report_notes = [
        "Temperatures are in degrees Celsius and rainfall is in "
        "millimetres."
    ]
    section_title(
        f"Historical Climate Analysis — {selected_city}"
    )

    if selected_annual.empty:

        st.warning(
            f"Annual climate history is not available for {selected_city} "
            "yet. Please try another city."
        )

    else:

        years = get_year_options(selected_annual)

        c1, c2, c3 = st.columns(3)

        with c1:
            metric_card(
                "Years of Data",
                str(len(years)),
                "📅"
            )

        with c2:

            if "annual_rainfall_mm" in selected_annual.columns:

                metric_card(
                    "Highest Annual Rainfall",
                    f"{selected_annual['annual_rainfall_mm'].max():,.1f} mm",
                    "🌧️"
                )

            else:

                metric_card(
                    "Annual Rainfall",
                    "N/A",
                    "🌧️"
                )

        with c3:

            if "avg_tmax_c" in selected_annual.columns:

                metric_card(
                    "Highest Annual Mean Maximum Temperature",
                    f"{selected_annual['avg_tmax_c'].max():.1f} °C",
                    "🌡️"
                )

            else:

                metric_card(
                    "Maximum Temperature",
                    "N/A",
                    "🌡️"
                )

        temperature_columns = [
            col for col in [
                "avg_tmax_c",
                "avg_tmin_c",
                "avg_tmean_c"
            ]
            if col in selected_annual.columns
        ]

        if temperature_columns:

            section_title("Annual Temperature Trends")

            fig = px.line(
                selected_annual.sort_values("year"),
                x="year",
                y=temperature_columns,
                markers=True,
                labels={
                    "year": "Year",
                    "value": "Temperature (°C)",
                    "variable": "Temperature Type"
                },
                color_discrete_sequence=[
                    "#df8b3d",
                    "#4a91c5",
                    "#21845b"
                ]
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch"
            )

        if "annual_rainfall_mm" in selected_annual.columns:

            section_title("Annual Rainfall Patterns")

            fig = px.bar(
                selected_annual.sort_values("year"),
                x="year",
                y="annual_rainfall_mm",
                labels={
                    "year": "Year",
                    "annual_rainfall_mm": "Annual Rainfall (mm)"
                },
                color_discrete_sequence=["#3985b8"]
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch"
            )

        if not selected_monthly.empty:

            section_title("Monthly Climate Patterns")

            a, b = st.columns(2)

            with a:

                monthly_temp_cols = [
                    col for col in [
                        "avg_tmax_c",
                        "avg_tmin_c",
                        "avg_tmean_c"
                    ]
                    if col in selected_monthly.columns
                ]

                if monthly_temp_cols:

                    fig = px.line(
                        selected_monthly.sort_values("month"),
                        x="month",
                        y=monthly_temp_cols,
                        markers=True,
                        labels={
                            "month": "Month",
                            "value": "Temperature (°C)",
                            "variable": "Temperature Type"
                        }
                    )

                    st.plotly_chart(
                        style_chart(fig),
                        width="stretch"
                    )

            with b:

                if "avg_monthly_rainfall_mm" in selected_monthly.columns:

                    fig = px.bar(
                        selected_monthly.sort_values("month"),
                        x="month",
                        y="avg_monthly_rainfall_mm",
                        labels={
                            "month": "Month",
                            "avg_monthly_rainfall_mm":
                                "Average Monthly Rainfall (mm)"
                        },
                        color_discrete_sequence=["#3985b8"]
                    )

                    st.plotly_chart(
                        style_chart(fig),
                        width="stretch"
                    )

        section_title("Annual Climate Records")

        show_table(
            selected_annual.sort_values("year")
        )


# =========================================================
# 11. SOURCE COMPARISON
# =========================================================

elif page == "Compare Data Sources":

    report_title = "Climate data source comparison"
    report_tables = [
        (
            "City comparison summary",
            filter_city(city_comparison, selected_city),
        ),
        (
            "Annual comparison",
            filter_city(annual_comparison, selected_city),
        ),
        (
            "Monthly comparison",
            filter_city(monthly_comparison, selected_city),
        ),
    ]
    report_notes = [
        "Differences compare gridded climate datasets; they are not "
        "forecast errors or proof that one data source is correct."
    ]
    section_title("Compare NASA POWER and Open-Meteo ERA5")

    st.markdown("""
    <div class="small-note">
        Compare NASA POWER and Open-Meteo ERA5 estimates for matching dates
        and cities. NASA POWER and ERA5 are gridded climate products, not
        local station readings. Differences show where estimates disagree;
        they are not prediction errors or proof that one source is correct.
    </div>
    """, unsafe_allow_html=True)

    if city_comparison.empty and annual_comparison.empty:

        st.warning(
            "A comparison between the climate data sources is not "
            "available yet. Please try again later."
        )

    else:

        if not city_comparison.empty:

            section_title("City-wise Comparison Summary")

            city_row = filter_city(
                city_comparison,
                selected_city
            )

            if city_row.empty:

                st.info(
                    "No city-wise comparison record found for "
                    f"{selected_city}."
                )

            else:

                show_table(city_row)

                temperature_mae_col = find_column(
                    city_row,
                    [
                        "temperature_mae_c",
                        "temperature_mae",
                        "mean_absolute_temperature_difference_c"
                    ]
                )

                rainfall_mae_col = find_column(
                    city_row,
                    [
                        "rainfall_mae_mm",
                        "rainfall_mae",
                        "mean_absolute_rainfall_difference_mm"
                    ]
                )

                a, b = st.columns(2)

                with a:

                    if temperature_mae_col:

                        value = pd.to_numeric(
                            city_row.iloc[0][temperature_mae_col],
                            errors="coerce"
                        )

                        metric_card(
                            "Average Temperature Difference",
                            f"{value:.3f} °C"
                            if pd.notna(value)
                            else "N/A",
                            "🌡️"
                        )

                with b:

                    if rainfall_mae_col:

                        value = pd.to_numeric(
                            city_row.iloc[0][rainfall_mae_col],
                            errors="coerce"
                        )

                        metric_card(
                            "Average Rainfall Difference",
                            f"{value:.3f} mm"
                            if pd.notna(value)
                            else "N/A",
                            "🌧️"
                        )

        if not annual_comparison.empty:

            section_title("Annual Source Comparison")

            annual_city = filter_city(
                annual_comparison,
                selected_city
            )

            year_col = find_column(
                annual_city,
                ["year"]
            )

            nasa_temp_col = find_column(
                annual_city,
                [
                    "nasa_mean_temperature",
                    "nasa_mean_tmean_c",
                    "nasa_avg_temperature_c",
                    "nasa_mean_temp_c"
                ]
            )

            era5_temp_col = find_column(
                annual_city,
                [
                    "era5_mean_temperature",
                    "era5_mean_tmean_c",
                    "era5_avg_temperature_c",
                    "era5_mean_temp_c"
                ]
            )

            nasa_rain_col = find_column(
                annual_city,
                [
                    "nasa_total_rainfall",
                    "nasa_annual_rainfall_mm",
                    "nasa_rainfall_mm",
                    "nasa_total_rainfall_mm"
                ]
            )

            era5_rain_col = find_column(
                annual_city,
                [
                    "era5_total_rainfall",
                    "era5_annual_rainfall_mm",
                    "era5_rainfall_mm",
                    "era5_total_rainfall_mm"
                ]
            )

            if year_col and nasa_temp_col and era5_temp_col:

                plot_data = annual_city[
                    [year_col, nasa_temp_col, era5_temp_col]
                ].copy()

                plot_data = plot_data.rename(
                    columns={
                        nasa_temp_col: "NASA POWER",
                        era5_temp_col: "Open-Meteo ERA5"
                    }
                )

                plot_data = plot_data.melt(
                    id_vars=[year_col],
                    var_name="Data Source",
                    value_name="Mean Temperature (°C)"
                )

                fig = px.line(
                    plot_data,
                    x=year_col,
                    y="Mean Temperature (°C)",
                    color="Data Source",
                    markers=True
                )

                st.plotly_chart(
                    style_chart(fig),
                    width="stretch"
                )

            if year_col and nasa_rain_col and era5_rain_col:

                plot_data = annual_city[
                    [year_col, nasa_rain_col, era5_rain_col]
                ].copy()

                plot_data = plot_data.rename(
                    columns={
                        nasa_rain_col: "NASA POWER",
                        era5_rain_col: "Open-Meteo ERA5"
                    }
                )

                plot_data = plot_data.melt(
                    id_vars=[year_col],
                    var_name="Data Source",
                    value_name="Annual Rainfall (mm)"
                )

                fig = px.line(
                    plot_data,
                    x=year_col,
                    y="Annual Rainfall (mm)",
                    color="Data Source",
                    markers=True
                )

                st.plotly_chart(
                    style_chart(fig),
                    width="stretch"
                )

            section_title("Annual Comparison Records")

            show_table(annual_city)

        if not monthly_comparison.empty:

            with st.expander("View Monthly Comparison Records"):

                monthly_city = filter_city(
                    monthly_comparison,
                    selected_city
                )

                show_table(monthly_city)


# =========================================================
# 12. CLIMATE TRENDS AND EXTREME WEATHER
# =========================================================

elif page == "Climate Trends & Extreme Weather":

    report_title = "Climate trends and extreme weather"
    report_tables = [
        ("Annual climate trends", filter_city(annual_trends, selected_city)),
        (
            "Long-term trend summary",
            filter_city(long_term_trends, selected_city),
        ),
        (
            "Extreme weather summary",
            filter_city(extreme_summary, selected_city),
        ),
        (
            "Monthly climate averages",
            filter_city(monthly_climatology, selected_city),
        ),
    ]
    report_notes = [
        "Historical trends are descriptive and do not establish causation "
        "or predict future climate.",
        *climate_analysis_recommendations(selected_annual),
    ]
    section_title(
        f"Climate Trends & Extreme Weather — {selected_city}"
    )

    st.markdown("""
    <div class="small-note">
        Trend lines are descriptive statistical summaries of historical
        data. They do not establish causation or provide future climate
        predictions. Heat and heavy-rain thresholds are analytical
        screening assumptions used by this project.
    </div>
    """, unsafe_allow_html=True)

    trend_city = filter_city(
        annual_trends,
        selected_city
    )

    if trend_city.empty:

        st.warning(
            f"Climate trend information is not available for {selected_city} "
            "yet. Please try another city."
        )

    else:

        trend_year_col = find_column(
            trend_city,
            ["year"]
        )

        trend_temp_col = find_column(
            trend_city,
            [
                "avg_tmean_c",
                "mean_temperature_c",
                "annual_mean_temperature_c",
                "mean_temp_c"
            ]
        )

        trend_rain_col = find_column(
            trend_city,
            [
                "annual_rainfall_mm",
                "total_rainfall_mm",
                "annual_precipitation_mm"
            ]
        )

        if trend_year_col and trend_temp_col:

            section_title("Long-term Annual Temperature")

            fig = px.line(
                trend_city.sort_values(trend_year_col),
                x=trend_year_col,
                y=trend_temp_col,
                markers=True,
                labels={
                    trend_year_col: "Year",
                    trend_temp_col: "Mean Temperature (°C)"
                }
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch"
            )

        if trend_year_col and trend_rain_col:

            section_title("Long-term Annual Rainfall")

            fig = px.bar(
                trend_city.sort_values(trend_year_col),
                x=trend_year_col,
                y=trend_rain_col,
                labels={
                    trend_year_col: "Year",
                    trend_rain_col: "Annual Rainfall (mm)"
                },
                color_discrete_sequence=["#3985b8"]
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch"
            )

        section_title("Annual Trend Data")

        show_table(trend_city)

    if not long_term_trends.empty:

        section_title("City-wise Long-term Trend Summary")

        selected_long_term = filter_city(
            long_term_trends,
            selected_city
        )

        if not selected_long_term.empty:
            show_table(selected_long_term)
        else:
            show_table(long_term_trends)

    if not extreme_summary.empty:

        section_title("Extreme Weather Summary")

        selected_extreme = filter_city(
            extreme_summary,
            selected_city
        )

        if not selected_extreme.empty:
            show_table(selected_extreme)
        else:
            show_table(extreme_summary)

    if not monthly_climatology.empty:

        section_title("Monthly Climate Climatology")

        selected_climatology = filter_city(
            monthly_climatology,
            selected_city
        )

        if not selected_climatology.empty:
            show_table(selected_climatology)

    section_title("Suggestions based on this city's climate history")
    for suggestion in climate_analysis_recommendations(selected_annual):
        st.markdown(f"- {suggestion}")


# =========================================================
# 13. CLIMATE PREDICTIONS
# =========================================================

elif page == "Climate Predictions":

    report_title = "Next-day climate estimate and model evaluation"
    section_title(f"Next-day climate estimate — {selected_city}")
    st.markdown(
        "A city-specific machine-learning model estimates mean temperature "
        "and rainfall for the day after the latest available daily record."
    )

    forecast_data = (
        multi_city_daily
        if not multi_city_daily.empty
        else climate_db
    )
    try:
        forecast_run = cached_climate_forecasts(forecast_data)
    except ValueError as error:
        st.warning(f"Prediction is unavailable: {error}")
    else:
        forecast = forecast_run.forecasts.get(selected_city)
        if forecast is None:
            unavailable_reason = forecast_run.unavailable_cities.get(
                selected_city,
                "No forecast is available for this city.",
            )
            st.info(unavailable_reason)
        else:
            st.info(
                f"Estimate date: {forecast.forecast_date.isoformat()}. "
                f"Training data ends on "
                f"{forecast.trained_through_date.isoformat()}. This is a "
                "historical one-day-ahead model demonstration, not a "
                "current weather forecast or an emergency planning source."
            )

            prediction_columns = st.columns(2)
            with prediction_columns[0]:
                metric_card(
                    "Estimated Mean Temperature",
                    f"{forecast.mean_temperature_c:.1f} °C",
                    "🌡️",
                )
            with prediction_columns[1]:
                metric_card(
                    "Estimated Rainfall",
                    f"{forecast.rainfall_mm:.1f} mm",
                    "🌧️",
                )

            evaluation = pd.DataFrame([
                {
                    "Measure": "Mean temperature (°C)",
                    "Model MAE": forecast.temperature_metrics.mae,
                    "Previous-day MAE baseline":
                        forecast.temperature_baseline_metrics.mae,
                    "Model RMSE": forecast.temperature_metrics.rmse,
                    "Previous-day RMSE baseline":
                        forecast.temperature_baseline_metrics.rmse,
                },
                {
                    "Measure": "Rainfall (mm)",
                    "Model MAE": forecast.rainfall_metrics.mae,
                    "Previous-day MAE baseline":
                        forecast.rainfall_baseline_metrics.mae,
                    "Model RMSE": forecast.rainfall_metrics.rmse,
                    "Previous-day RMSE baseline":
                        forecast.rainfall_baseline_metrics.rmse,
                },
            ])
            section_title(
                f"Model check: {forecast_run.test_year} held-out year"
            )
            st.caption(
                f"MAE and RMSE are average prediction errors; lower is "
                f"better. Scores use {forecast.test_days} days not used "
                "to fit the evaluation model."
            )
            show_table(evaluation)

            temperature_improved = (
                forecast.temperature_metrics.mae
                < forecast.temperature_baseline_metrics.mae
            )
            rainfall_improved = (
                forecast.rainfall_metrics.mae
                < forecast.rainfall_baseline_metrics.mae
            )
            if temperature_improved and rainfall_improved:
                st.success(
                    "The model had lower MAE than the previous-day "
                    "baseline for both measures in the held-out year."
                )
            elif temperature_improved or rainfall_improved:
                st.warning(
                    "The model beat the previous-day baseline for only "
                    "one measure in the held-out year. Use the other "
                    "estimate with extra caution."
                )
            else:
                st.warning(
                    "The model did not beat the previous-day baseline in "
                    "the held-out year. Treat these estimates as a project "
                    "demonstration, not decision-grade forecasts."
                )

            with st.expander("How this prediction is produced"):
                st.markdown(
                    "- Separate HistGradientBoosting regressors are fit "
                    "for each city and climate measure.\n"
                    "- The model uses recent daily temperature, rainfall, "
                    "seven-day summaries, and the known calendar season.\n"
                    f"- It is evaluated chronologically: years before "
                    f"{forecast_run.test_year} for training and "
                    f"{forecast_run.test_year} for testing.\n"
                    "- After evaluation, the forecast model is refit on "
                    "all available history."
                )

            forecast_table = pd.DataFrame([{
                "City": forecast.city,
                "Estimate date": forecast.forecast_date.isoformat(),
                "Mean temperature estimate (°C)":
                    forecast.mean_temperature_c,
                "Rainfall estimate (mm)": forecast.rainfall_mm,
                "Latest observed date":
                    forecast.trained_through_date.isoformat(),
            }])
            report_tables = [
                ("Next-day estimate", forecast_table),
                ("Held-out-year model evaluation", evaluation),
            ]
            report_notes = [
                "This is a historical model demonstration, not a current "
                "weather forecast.",
                f"The chronological holdout year was {forecast_run.test_year}.",
                "Model errors are compared with a previous-day persistence "
                "baseline; lower MAE and RMSE are better.",
            ]


# =========================================================
# 14. LIVE SIMULATIONS
# =========================================================

elif page == "Adaptation Simulations":

    section_title("Interactive Climate Adaptation Simulations")
    report_title = "Adaptation simulation results"
    report_notes = [
        "Simulations use simplified planning assumptions and historical "
        "rainfall; they are estimates, not predictions of real-world savings."
    ]
    city_simulation_reports = [
        report
        for report in st.session_state.get("simulation_reports", {}).values()
        if report["city"] == selected_city
    ]
    report_tables = [
        table
        for report in city_simulation_reports
        for table in report["tables"]
    ]
    if not city_simulation_reports:
        st.info(
            "Run a simulation to create downloadable results for this city."
        )

    st.markdown("""
    <div class="small-note">
        Adjust the planning inputs and run a scenario. Calculations use
        historical rainfall and transparent mathematical assumptions.
        They are estimates, not operational forecasts.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "💧 Rainwater Harvesting",
        "🌳 Urban Green Spaces",
        "🏠 Cool Roofs"
    ])

    # RAINWATER HARVESTING

    with tab1:

        section_title("Rainwater Harvesting Calculator")

        years = get_year_options(selected_annual)

        if not years or "annual_rainfall_mm" not in selected_annual.columns:

            st.warning(
                "Annual rainfall data is not available for this city."
            )

        else:

            with st.form("rainwater_form"):

                col1, col2 = st.columns(2)

                with col1:

                    selected_year = st.selectbox(
                        "Select Historical Year",
                        years,
                        index=len(years) - 1
                    )

                    roof_area = st.number_input(
                        "Roof Area (m²)",
                        min_value=1.0,
                        max_value=1000000.0,
                        value=1000.0,
                        step=100.0
                    )

                with col2:

                    runoff = st.slider(
                        "Share of Rainfall Captured",
                        min_value=0.1,
                        max_value=1.0,
                        value=0.80,
                        step=0.05,
                        help=(
                            "Assumed fraction of rainfall that reaches the "
                            "collection system after roof runoff losses."
                        ),
                    )

                    efficiency = st.slider(
                        "Collection Efficiency",
                        min_value=0.1,
                        max_value=1.0,
                        value=0.80,
                        step=0.05,
                        help=(
                            "Assumed fraction of collected runoff that is "
                            "usable after system losses."
                        ),
                    )

                submitted = st.form_submit_button(
                    "Calculate Rainwater Harvest",
                    width="stretch"
                )

            if submitted:

                rainfall = get_selected_rainfall(
                    annual_data,
                    selected_city,
                    selected_year
                )

                if rainfall is None:

                    st.error("Rainfall data could not be retrieved.")

                else:

                    harvested_litres = (
                        rainfall *
                        roof_area *
                        runoff *
                        efficiency
                    )

                    harvested_m3 = harvested_litres / 1000

                    st.success("Rainwater calculation completed.")

                    a, b, c = st.columns(3)

                    with a:
                        metric_card(
                            "Annual Rainfall",
                            f"{rainfall:,.2f} mm",
                            "🌧️"
                        )

                    with b:
                        metric_card(
                            "Estimated Harvest",
                            f"{harvested_litres:,.0f} L",
                            "💧"
                        )

                    with c:
                        metric_card(
                            "Harvest Volume",
                            f"{harvested_m3:,.2f} m³",
                            "🛢️"
                        )

                    result = pd.DataFrame({
                        "Parameter": [
                            "City",
                            "Selected Year",
                            "Annual Rainfall",
                            "Roof Area",
                            "Runoff Coefficient",
                            "Collection Efficiency",
                            "Estimated Harvest"
                        ],
                        "Value": [
                            selected_city,
                            str(selected_year),
                            f"{rainfall:.2f} mm",
                            f"{roof_area:.2f} m²",
                            f"{runoff:.2f}",
                            f"{efficiency:.2f}",
                            f"{harvested_litres:,.2f} litres"
                        ]
                    })
                    save_simulation_report(
                        selected_city,
                        "Rainwater harvesting",
                        [("Rainwater harvesting results", result)],
                    )

                    section_title("Simulation Results")

                    show_table(result)

                    fig = px.bar(
                        x=["Estimated Rainwater"],
                        y=[harvested_litres],
                        labels={
                            "x": "Result",
                            "y": "Estimated Harvest (litres)"
                        },
                        color_discrete_sequence=["#26966b"]
                    )

                    st.plotly_chart(
                        style_chart(fig),
                        width="stretch"
                    )

                    st.caption(
                        "The estimate does not model storage capacity, "
                        "first-flush losses, rainfall timing or actual "
                        "roof conditions."
                    )

                    show_ai_recommendations(
                        rainwater_recommendations(harvested_litres)
                    )

    # URBAN GREEN SPACES

    with tab2:

        section_title("Urban Green Space Water Calculator")

        years = get_year_options(selected_annual)

        if not years or "annual_rainfall_mm" not in selected_annual.columns:

            st.warning(
                "Annual rainfall data is not available for this city."
            )

        else:

            with st.form("green_space_form"):

                col1, col2 = st.columns(2)

                with col1:

                    green_year = st.selectbox(
                        "Select Historical Year",
                        years,
                        index=len(years) - 1,
                        key="green_year"
                    )

                    green_area = st.number_input(
                        "Green Space Area (m²)",
                        min_value=1.0,
                        max_value=1000000.0,
                        value=1000.0,
                        step=100.0
                    )

                    daily_requirement = st.number_input(
                        "Daily Water Requirement (litres/m²)",
                        min_value=0.1,
                        max_value=100.0,
                        value=3.0,
                        step=0.5
                    )

                with col2:

                    irrigation_days = st.number_input(
                        "Annual Irrigation Days",
                        min_value=1,
                        max_value=365,
                        value=180
                    )

                    roof_area_green = st.number_input(
                        "Rainwater Collection Roof Area (m²)",
                        min_value=1.0,
                        max_value=1000000.0,
                        value=1000.0,
                        step=100.0
                    )

                    green_runoff = st.slider(
                        "Share of Rainfall Captured",
                        min_value=0.1,
                        max_value=1.0,
                        value=0.80,
                        step=0.05,
                        key="green_runoff",
                        help=(
                            "Assumed fraction of rainfall that reaches the "
                            "collection system after roof runoff losses."
                        ),
                    )

                    green_efficiency = st.slider(
                        "Collection Efficiency",
                        min_value=0.1,
                        max_value=1.0,
                        value=0.80,
                        step=0.05,
                        key="green_efficiency"
                    )

                submitted_green = st.form_submit_button(
                    "Run Green Space Simulation",
                    width="stretch"
                )

            if submitted_green:

                rainfall = get_selected_rainfall(
                    annual_data,
                    selected_city,
                    green_year
                )

                if rainfall is None:

                    st.error("Rainfall data could not be retrieved.")

                else:

                    water_demand = (
                        green_area *
                        daily_requirement *
                        irrigation_days
                    )

                    available_rainwater = (
                        rainfall *
                        roof_area_green *
                        green_runoff *
                        green_efficiency
                    )

                    water_used = min(
                        water_demand,
                        available_rainwater
                    )

                    additional_water = max(
                        0,
                        water_demand - available_rainwater
                    )

                    coverage = (
                        water_used / water_demand
                    ) * 100 if water_demand > 0 else 0

                    st.success("Green space simulation completed.")

                    a, b, c = st.columns(3)

                    with a:
                        metric_card(
                            "Annual Water Demand",
                            f"{water_demand:,.0f} L",
                            "🌳"
                        )

                    with b:
                        metric_card(
                            "Estimated Rainwater",
                            f"{available_rainwater:,.0f} L",
                            "💧"
                        )

                    with c:
                        metric_card(
                            "Irrigation Coverage",
                            f"{coverage:.2f}%",
                            "📊"
                        )

                    d, e = st.columns(2)

                    with d:
                        metric_card(
                            "Rainwater Used",
                            f"{water_used:,.0f} L",
                            "🚰"
                        )

                    with e:
                        metric_card(
                            "Additional Water Required",
                            f"{additional_water:,.0f} L",
                            "⚠️"
                        )

                    chart_data = pd.DataFrame({
                        "Water Category": [
                            "Annual Demand",
                            "Estimated Rainwater"
                        ],
                        "Litres": [
                            water_demand,
                            available_rainwater
                        ]
                    })

                    fig = px.bar(
                        chart_data,
                        x="Water Category",
                        y="Litres",
                        color="Water Category",
                        color_discrete_sequence=[
                            "#df9b45",
                            "#26966b"
                        ]
                    )

                    st.plotly_chart(
                        style_chart(fig),
                        width="stretch"
                    )

                    st.progress(
                        min(coverage / 100, 1.0)
                    )

                    if coverage >= 100:

                        st.success(
                            "Estimated annual rainwater is sufficient "
                            "for the selected annual demand under these "
                            "simplified assumptions."
                        )

                    else:

                        st.warning(
                            f"Estimated additional water required: "
                            f"{additional_water:,.0f} litres."
                        )

                    st.caption(
                        "This annual comparison does not account for "
                        "storage capacity, seasonal rainfall timing, "
                        "evaporation, leakage or irrigation losses."
                    )

                    green_result = pd.DataFrame({
                        "Parameter": [
                            "City",
                            "Selected Year",
                            "Annual Rainfall",
                            "Green Space Area",
                            "Daily Water Requirement",
                            "Irrigation Days",
                            "Annual Water Demand",
                            "Estimated Rainwater",
                            "Rainwater Used",
                            "Additional Water Required",
                            "Irrigation Coverage",
                        ],
                        "Value": [
                            selected_city,
                            str(green_year),
                            f"{rainfall:.2f} mm",
                            f"{green_area:.2f} m²",
                            f"{daily_requirement:.2f} L/m²/day",
                            str(irrigation_days),
                            f"{water_demand:,.2f} L",
                            f"{available_rainwater:,.2f} L",
                            f"{water_used:,.2f} L",
                            f"{additional_water:,.2f} L",
                            f"{coverage:.2f}%",
                        ],
                    })
                    save_simulation_report(
                        selected_city,
                        "Urban green space",
                        [("Green-space irrigation results", green_result)],
                    )
                    section_title("Simulation Results")
                    show_table(green_result)

                    show_ai_recommendations(
                        green_space_recommendations(coverage)
                    )

    # COOL ROOFS

    with tab3:

        section_title("Cool Roof Coverage Calculator")

        with st.form("cool_roof_form"):

            col1, col2 = st.columns(2)

            with col1:

                total_roof_area = st.number_input(
                    "Total Roof Area (m²)",
                    min_value=1.0,
                    max_value=1000000.0,
                    value=1000.0,
                    step=100.0
                )

            with col2:

                coverage_percentage = st.slider(
                    "Cool Roof Coverage (%)",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=5
                )

            submitted_roof = st.form_submit_button(
                "Calculate Cool Roof Scenario",
                width="stretch"
            )

        if submitted_roof:

            cool_area = (
                total_roof_area *
                coverage_percentage / 100
            )

            conventional_area = (
                total_roof_area - cool_area
            )

            st.success("Cool roof scenario completed.")

            a, b, c = st.columns(3)

            with a:
                metric_card(
                    "Total Roof Area",
                    f"{total_roof_area:,.0f} m²",
                    "🏠"
                )

            with b:
                metric_card(
                    "Cool Roof Area",
                    f"{cool_area:,.0f} m²",
                    "☀️"
                )

            with c:
                metric_card(
                    "Conventional Roof Area",
                    f"{conventional_area:,.0f} m²",
                    "🏢"
                )

            chart_data = pd.DataFrame({
                "Roof Type": [
                    "Cool Roof",
                    "Conventional Roof"
                ],
                "Area": [
                    cool_area,
                    conventional_area
                ]
            })

            fig = px.pie(
                chart_data,
                names="Roof Type",
                values="Area",
                hole=0.55,
                color_discrete_sequence=[
                    "#26966b",
                    "#9ba9a1"
                ]
            )

            st.plotly_chart(
                style_chart(fig),
                width="stretch"
            )

            section_title("Coverage Scenario Comparison")

            percentages = [25, 50, 75, 100]

            comparison = pd.DataFrame({
                "Coverage Percentage": percentages,
                "Cool Roof Area (m²)": [
                    total_roof_area * p / 100
                    for p in percentages
                ],
                "Conventional Roof Area (m²)": [
                    total_roof_area * (100 - p) / 100
                    for p in percentages
                ]
            })

            show_table(comparison)
            roof_result = pd.DataFrame({
                "Parameter": [
                    "City",
                    "Total Roof Area",
                    "Cool Roof Coverage",
                    "Cool Roof Area",
                    "Conventional Roof Area",
                ],
                "Value": [
                    selected_city,
                    f"{total_roof_area:.2f} m²",
                    f"{coverage_percentage}%",
                    f"{cool_area:.2f} m²",
                    f"{conventional_area:.2f} m²",
                ],
            })
            save_simulation_report(
                selected_city,
                "Cool roof",
                [("Cool-roof coverage results", roof_result)],
            )
            section_title("Simulation Results")
            show_table(roof_result)

            st.caption(
                "This calculator compares roof coverage areas only. "
                "It does not predict temperature reduction, energy "
                "savings or financial benefits."
            )

            show_ai_recommendations(
                cool_roof_recommendations(coverage_percentage)
            )


# =========================================================
# 14. ADAPTATION SCENARIOS
# =========================================================

elif page == "Saved Scenario Results":

    section_title("Stored Adaptation Scenario Results")
    report_title = "Saved adaptation scenario results"
    report_tables = [
        ("Rainwater scenarios", rainwater_db),
        ("Urban green-space scenarios", green_db),
        ("Cool-roof scenarios", cool_roof_db),
    ]

    tab1, tab2, tab3 = st.tabs([
        "💧 Rainwater Management",
        "🌳 Urban Green Spaces",
        "🏠 Cool Roofs"
    ])

    with tab1:

        if rainwater_db.empty:

            st.info("No saved rainwater scenario results are available yet.")

        else:

            if "estimated_harvest_litres" in rainwater_db.columns:

                a, b = st.columns(2)

                with a:

                    metric_card(
                        "Average Estimated Harvest",
                        f"{rainwater_db['estimated_harvest_litres'].mean():,.0f} L",
                        "💧"
                    )

                with b:

                    metric_card(
                        "Highest Estimated Harvest",
                        f"{rainwater_db['estimated_harvest_litres'].max():,.0f} L",
                        "📈"
                    )

            if (
                "year" in rainwater_db.columns
                and "estimated_harvest_litres" in rainwater_db.columns
            ):

                fig = px.bar(
                    rainwater_db.sort_values("year"),
                    x="year",
                    y="estimated_harvest_litres",
                    labels={
                        "year": "Year",
                        "estimated_harvest_litres":
                            "Estimated Harvest (litres)"
                    },
                    color_discrete_sequence=["#26966b"]
                )

                st.plotly_chart(
                    style_chart(fig),
                    width="stretch"
                )

            show_table(rainwater_db)

    with tab2:

        if green_db.empty:

            st.info(
                "No saved urban green-space scenario results are available yet."
            )

        else:

            if "irrigation_coverage_percentage" in green_db.columns:

                metric_card(
                    "Average Irrigation Coverage",
                    f"{green_db['irrigation_coverage_percentage'].mean():.2f}%",
                    "🌳"
                )

            if (
                "year" in green_db.columns
                and "irrigation_coverage_percentage" in green_db.columns
            ):

                fig = px.line(
                    green_db.sort_values("year"),
                    x="year",
                    y="irrigation_coverage_percentage",
                    markers=True,
                    labels={
                        "year": "Year",
                        "irrigation_coverage_percentage":
                            "Irrigation Coverage (%)"
                    },
                    color_discrete_sequence=["#21845b"]
                )

                fig.update_yaxes(range=[0, 100])

                st.plotly_chart(
                    style_chart(fig),
                    width="stretch"
                )

            show_table(green_db)

    with tab3:

        if cool_roof_db.empty:

            st.info("No saved cool-roof scenario results are available yet.")

        else:

            if "cool_roof_coverage_percentage" in cool_roof_db.columns:

                metric_card(
                    "Maximum Cool Roof Coverage",
                    f"{cool_roof_db['cool_roof_coverage_percentage'].max():.0f}%",
                    "🏠"
                )

            if (
                "cool_roof_coverage_percentage" in cool_roof_db.columns
                and "cool_roof_area_m2" in cool_roof_db.columns
            ):

                fig = px.bar(
                    cool_roof_db.sort_values(
                        "cool_roof_coverage_percentage"
                    ),
                    x="cool_roof_coverage_percentage",
                    y="cool_roof_area_m2",
                    labels={
                        "cool_roof_coverage_percentage": "Coverage (%)",
                        "cool_roof_area_m2": "Cool Roof Area (m²)"
                    },
                    color_discrete_sequence=["#26966b"]
                )

                st.plotly_chart(
                    style_chart(fig),
                    width="stretch"
                )

            show_table(cool_roof_db)


# =========================================================
# 15. CLIMATE INSIGHTS AND DATA COVERAGE
# =========================================================

elif page == "Climate Insights & Data Coverage":

    report_title = "Climate insights and data coverage"
    section_title("Climate Insights & Data Coverage")
    st.markdown(
        "Explore the historical climate records currently available for the "
        "study cities, along with the sources used for climate analysis."
    )

    daily_source = (
        multi_city_daily
        if not multi_city_daily.empty
        else climate_db
    )
    daily_count = len(daily_source)
    year_values = (
        pd.to_numeric(annual_data["year"], errors="coerce").dropna()
        if "year" in annual_data.columns
        else pd.Series(dtype="float64")
    )
    first_year = int(year_values.min()) if not year_values.empty else None
    last_year = int(year_values.max()) if not year_values.empty else None
    study_period = (
        f"{first_year}–{last_year}"
        if first_year is not None and last_year is not None
        else "Not available"
    )
    available_sources = sum(
        (
            not daily_source.empty,
            not era5_daily.empty,
        )
    )

    coverage_metrics = st.columns(4)
    with coverage_metrics[0]:
        metric_card("Cities Analyzed", str(len(city_options)), "📍")
    with coverage_metrics[1]:
        metric_card("Daily Climate Records", f"{daily_count:,}", "📊")
    with coverage_metrics[2]:
        metric_card("Study Period", study_period, "📅")
    with coverage_metrics[3]:
        metric_card("Available Data Sources", str(available_sources), "🌐")

    section_title("Coverage by City")
    location_column = (
        find_column(daily_source, ["location", "city", "city_name"])
        or find_column(annual_data, ["location", "city", "city_name"])
    )
    date_column = find_column(
        daily_source,
        ["date", "datetime", "time"],
    )
    coverage_rows = []

    for city in city_options:
        city_daily = filter_city(daily_source, city)
        city_annual = filter_city(annual_data, city)
        city_years = get_year_options(city_annual)

        if date_column and not city_daily.empty:
            dates = pd.to_datetime(
                city_daily[date_column],
                errors="coerce",
            ).dropna()
            observed_years = dates.dt.year
        else:
            observed_years = pd.Series(dtype="int64")

        coverage_years = (
            observed_years.tolist()
            if not observed_years.empty
            else city_years
        )
        coverage_rows.append({
            "City": city,
            "Daily Records": len(city_daily),
            "Annual Summary Years": len(city_years),
            "Coverage": (
                f"{min(coverage_years)}–{max(coverage_years)}"
                if coverage_years
                else "Not available"
            ),
        })

    coverage_table = pd.DataFrame(coverage_rows)
    if location_column and coverage_rows:
        show_table(coverage_table)
    else:
        st.info("City-level climate coverage is not available yet.")

    section_title("Climate Data Sources")
    source_coverage = pd.DataFrame([
        {
            "Source": "NASA POWER",
            "Coverage": (
                "Available"
                if not daily_source.empty
                else "Not available"
            ),
            "Used for": "Historical daily and annual climate analysis",
        },
        {
            "Source": "Open-Meteo ERA5",
            "Coverage": (
                "Available"
                if not era5_daily.empty
                else "Not available"
            ),
            "Used for": "Climate source comparison",
        },
    ])
    show_table(source_coverage)
    report_tables = [
        ("Coverage by city", coverage_table),
        ("Climate data sources", source_coverage),
    ]
    report_notes = [
        "Gridded climate products are estimates, not direct weather-station "
        "observations."
    ]
    st.caption(
        "Coverage reflects the climate data currently loaded for this "
        "project. Gridded climate products are estimates, not direct "
        "weather-station observations."
    )


# =========================================================
# 16. DEVELOPER-ONLY DATABASE INFORMATION
# =========================================================

elif page == "Developer: Database Information" and DEVELOPER_MODE:

    section_title("Project Database Overview")
    st.caption(
        "Developer-only technical details. This page is available when "
        "CLIMATEADAPTAI_DEVELOPER_MODE is enabled."
    )

    st.markdown(
        f'<div class="small-note"><b>Database Location:</b> {DB_PATH}</div>',
        unsafe_allow_html=True
    )

    database_tables = {
        "Original Climate Records": climate_db,
        "Original Annual Summary": annual_db,
        "Original Monthly Summary": monthly_db,

        "Multi-city Climate Records": load_db_table(
            "multi_city_climate_records"
        ),

        "Multi-city Annual Summary": load_db_table(
            "multi_city_annual_summary"
        ),

        "Multi-city Monthly Summary": load_db_table(
            "multi_city_monthly_summary"
        ),

        "Rainwater Scenarios": rainwater_db,
        "Urban Green Space Scenarios": green_db,
        "Cool Roof Scenarios": cool_roof_db
    }

    total_records = sum(
        len(dataframe)
        for dataframe in database_tables.values()
    )

    a, b, c = st.columns(3)

    with a:

        metric_card(
            "Database Tables",
            str(len(database_tables)),
            "🗄️"
        )

    with b:

        metric_card(
            "Total Stored Records",
            f"{total_records:,}",
            "📊"
        )

    with c:

        metric_card(
            "Database Status",
            "Connected" if DB_PATH.exists() else "Not Found",
            "✅" if DB_PATH.exists() else "⚠️"
        )

    section_title("Stored Database Tables")

    for table_name, dataframe in database_tables.items():

        with st.expander(
            f"{table_name} | {len(dataframe):,} records"
        ):

            if dataframe.empty:

                st.info("No records found in this table.")

            else:

                show_table(
                    dataframe.head(20),
                    technical=True,
                )

    section_title("Generated Research Files")

    file_status = {
        "Multi-city NASA POWER data":
            DATA_DIR / "multi_city_climate_data.csv",

        "Open-Meteo ERA5 data":
            DATA_DIR / "open_meteo_climate_data.csv",

        "Annual source comparison":
            COMPARISON_DIR / "annual_source_comparison.csv",

        "City source comparison":
            COMPARISON_DIR / "city_source_comparison.csv",

        "Annual climate trends":
            TREND_DIR / "annual_climate_trends.csv",

        "Extreme weather summary":
            TREND_DIR / "extreme_weather_summary.csv"
    }

    status_data = []

    for label, file_path in file_status.items():

        status_data.append({
            "Research File": label,
            "Status": (
                "Available"
                if file_path.exists()
                else "Not Generated"
            ),
            "File": str(
                file_path.relative_to(BASE_DIR)
            )
        })

    show_table(
        pd.DataFrame(status_data),
        technical=True,
    )

if page == "Adaptation Simulations":
    city_simulation_reports = [
        report
        for report in st.session_state.get("simulation_reports", {}).values()
        if report["city"] == selected_city
    ]
    report_tables = [
        table
        for report in city_simulation_reports
        for table in report["tables"]
    ]

if report_tables:
    render_download_controls(
        report_title,
        selected_city,
        report_tables,
        report_notes,
    )


# =========================================================
# 16. FOOTER
# =========================================================

st.markdown("---")

st.markdown("""
<div class="footer">
    <b>Climate Adapt AI Simulator</b> · Climate adaptation decision support<br>
    Historical Climate Study · 2001–2024 · Pakistan<br>
    Data Sources: NASA POWER and Open-Meteo ERA5
</div>
""", unsafe_allow_html=True)

st.caption(
    "Research limitation: NASA POWER and Open-Meteo ERA5 are gridded "
    "climate datasets, not direct local weather-station observations. "
    "Adaptation calculators provide simplified scenario estimates. "
    "Recommendations are transparent rules, not a trained AI prediction model."
)
