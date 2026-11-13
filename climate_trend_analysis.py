from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# CLIMATEADAPTAI
# CLIMATE TREND & EXTREME WEATHER ANALYSIS
# NASA POWER | 2001-2024 | 5 CITIES
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "climate_trends"

INPUT_FILE = DATA_DIR / "multi_city_climate_data.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Transparent screening thresholds.
# These are project analysis thresholds, not official
# Pakistan Meteorological Department warning thresholds.
HEAT_THRESHOLD_C = 40.0
EXTREME_RAINFALL_THRESHOLD_MM = 50.0
WET_DAY_THRESHOLD_MM = 1.0


# ==========================================
# LOAD AND PREPARE DATA
# ==========================================

def load_data():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Climate dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "date",
        "location",
        "tmax_c",
        "tmin_c",
        "tmean_c",
        "precipitation_mm"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df = df[required_columns].copy()

    df["date"] = pd.to_datetime(
        df["date"], errors="coerce"
    )

    numeric_columns = [
        "tmax_c",
        "tmin_c",
        "tmean_c",
        "precipitation_mm"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df["location"] = (
        df["location"].astype(str).str.strip()
    )

    df = df.dropna(
        subset=["date", "location"] + numeric_columns
    )

    df = df.drop_duplicates(
        subset=["date", "location"]
    )

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    df = df.sort_values(
        ["location", "date"]
    ).reset_index(drop=True)

    print("Dataset loaded successfully!")
    print("Valid records:", len(df))
    print("Cities:", df["location"].nunique())
    print(
        "Date range:",
        df["date"].min().date(),
        "to",
        df["date"].max().date()
    )

    return df


# ==========================================
# CALCULATE LINEAR TREND
# ==========================================

def calculate_trend(years, values):

    valid = pd.DataFrame({
        "year": years,
        "value": values
    }).dropna()

    if len(valid) < 2:
        return np.nan

    slope = np.polyfit(
        valid["year"],
        valid["value"],
        1
    )[0]

    # Convert annual slope into per-decade trend
    return slope * 10


# ==========================================
# ANNUAL CLIMATE ANALYSIS
# ==========================================

def annual_analysis(df):

    annual = df.groupby(
        ["location", "year"]
    ).agg(

        mean_temperature_c=(
            "tmean_c", "mean"
        ),

        maximum_temperature_c=(
            "tmax_c", "max"
        ),

        minimum_temperature_c=(
            "tmin_c", "min"
        ),

        annual_rainfall_mm=(
            "precipitation_mm", "sum"
        ),

        average_daily_rainfall_mm=(
            "precipitation_mm", "mean"
        ),

        heat_days=(
            "heat_day", "sum"
        ),

        extreme_rainfall_days=(
            "extreme_rain_day", "sum"
        ),

        total_records=("date", "count")

    ).reset_index()

    annual.to_csv(
        OUTPUT_DIR / "annual_climate_trends.csv",
        index=False
    )

    return annual


# ==========================================
# MONTHLY CLIMATOLOGY
# ==========================================

def monthly_analysis(df):

    monthly = df.groupby(
        ["location", "month"]
    ).agg(

        mean_temperature_c=(
            "tmean_c", "mean"
        ),

        mean_maximum_temperature_c=(
            "tmax_c", "mean"
        ),

        mean_minimum_temperature_c=(
            "tmin_c", "mean"
        ),

        average_daily_rainfall_mm=(
            "precipitation_mm", "mean"
        ),

        total_rainfall_mm=(
            "precipitation_mm", "sum"
        )

    ).reset_index()

    monthly.to_csv(
        OUTPUT_DIR / "monthly_climate_climatology.csv",
        index=False
    )

    return monthly


# ==========================================
# EXTREME WEATHER INDICATORS
# ==========================================

def extreme_weather_analysis(df):

    results = []

    for city in sorted(df["location"].unique()):

        city_data = df[
            df["location"] == city
        ].copy()

        # City-specific percentile thresholds
        hot_threshold_90 = city_data[
            "tmax_c"
        ].quantile(0.90)

        wet_days = city_data[
            city_data["precipitation_mm"]
            >= WET_DAY_THRESHOLD_MM
        ]

        if len(wet_days) > 0:
            rainfall_threshold_95 = (
                wet_days["precipitation_mm"].quantile(0.95)
            )
        else:
            rainfall_threshold_95 = np.nan

        # Annual count of percentile-based events
        city_data["hot_percentile_day"] = (
            city_data["tmax_c"] > hot_threshold_90
        ).astype(int)

        city_data["heavy_rain_percentile_day"] = (
            city_data["precipitation_mm"]
            > rainfall_threshold_95
        ).astype(int)

        # Fixed project screening thresholds
        city_data["heat_day"] = (
            city_data["tmax_c"] >= HEAT_THRESHOLD_C
        ).astype(int)

        city_data["extreme_rain_day"] = (
            city_data["precipitation_mm"]
            >= EXTREME_RAINFALL_THRESHOLD_MM
        ).astype(int)

        annual_extremes = city_data.groupby(
            "year"
        ).agg(

            heat_days=("heat_day", "sum"),

            extreme_rainfall_days=(
                "extreme_rain_day", "sum"
            ),

            hot_percentile_days=(
                "hot_percentile_day", "sum"
            ),

            heavy_rain_percentile_days=(
                "heavy_rain_percentile_day", "sum"
            )

        ).reset_index()

        annual_extremes.insert(
            0, "location", city
        )

        annual_extremes.to_csv(
            OUTPUT_DIR / (
                city.split(",")[0].lower().replace(" ", "_")
                + "_extreme_weather.csv"
            ),
            index=False
        )

        results.append({
            "location": city,
            "hot_day_threshold_90_c": hot_threshold_90,
            "heavy_rain_threshold_95_mm": rainfall_threshold_95,
            "total_heat_days_40c_or_more": int(
                city_data["heat_day"].sum()
            ),
            "total_extreme_rain_days_50mm_or_more": int(
                city_data["extreme_rain_day"].sum()
            ),
            "total_hot_percentile_days": int(
                city_data["hot_percentile_day"].sum()
            ),
            "total_heavy_rain_percentile_days": int(
                city_data["heavy_rain_percentile_day"].sum()
            )
        })

    summary = pd.DataFrame(results)

    summary.to_csv(
        OUTPUT_DIR / "extreme_weather_summary.csv",
        index=False
    )

    return summary


# ==========================================
# CITY-WISE LONG-TERM TREND SUMMARY
# ==========================================

def city_trend_summary(annual):

    results = []

    for city in sorted(annual["location"].unique()):

        city_data = annual[
            annual["location"] == city
        ].sort_values("year")

        temp_trend = calculate_trend(
            city_data["year"],
            city_data["mean_temperature_c"]
        )

        rainfall_trend = calculate_trend(
            city_data["year"],
            city_data["annual_rainfall_mm"]
        )

        average_rainfall = (
            city_data["annual_rainfall_mm"].mean()
        )

        if average_rainfall > 0:
            rainfall_percent_trend = (
                rainfall_trend / average_rainfall
            ) * 100
        else:
            rainfall_percent_trend = np.nan

        results.append({

            "location": city,

            "average_temperature_c": (
                city_data["mean_temperature_c"].mean()
            ),

            "average_annual_rainfall_mm": (
                average_rainfall
            ),

            "temperature_trend_c_per_decade": (
                temp_trend
            ),

            "rainfall_trend_mm_per_decade": (
                rainfall_trend
            ),

            "rainfall_trend_percent_per_decade": (
                rainfall_percent_trend
            ),

            "highest_recorded_daily_max_c": (
                df_city_maximum(city)
            ),

            "highest_annual_rainfall_mm": (
                city_data["annual_rainfall_mm"].max()
            ),

            "lowest_annual_rainfall_mm": (
                city_data["annual_rainfall_mm"].min()
            )

        })

    summary = pd.DataFrame(results)

    summary.to_csv(
        OUTPUT_DIR / "city_long_term_trend_summary.csv",
        index=False
    )

    return summary


def df_city_maximum(city):
    # Read maximum from the original input dataset
    data = pd.read_csv(INPUT_FILE, usecols=[
        "location", "tmax_c"
    ])

    data = data[data["location"] == city]

    return pd.to_numeric(
        data["tmax_c"], errors="coerce"
    ).max()


# ==========================================
# GENERATE CITY-WISE GRAPHS
# ==========================================

def generate_graphs(df, annual):

    for city in sorted(df["location"].unique()):

        city_data = df[
            df["location"] == city
        ]

        annual_city = annual[
            annual["location"] == city
        ]

        slug = (
            city.split(",")[0]
            .lower()
            .replace(" ", "_")
        )

        # Annual mean temperature trend
        plt.figure(figsize=(12, 6))

        plt.plot(
            annual_city["year"],
            annual_city["mean_temperature_c"],
            marker="o",
            label="Annual Mean Temperature"
        )

        plt.title(
            f"Annual Temperature Trend - {city}"
        )

        plt.xlabel("Year")
        plt.ylabel("Temperature (°C)")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            OUTPUT_DIR / f"{slug}_temperature_trend.png",
            dpi=150
        )

        plt.close()

        # Annual rainfall trend
        plt.figure(figsize=(12, 6))

        plt.bar(
            annual_city["year"],
            annual_city["annual_rainfall_mm"]
        )

        plt.title(
            f"Annual Rainfall Trend - {city}"
        )

        plt.xlabel("Year")
        plt.ylabel("Rainfall (mm)")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        plt.savefig(
            OUTPUT_DIR / f"{slug}_rainfall_trend.png",
            dpi=150
        )

        plt.close()

        # Heat days and extreme rainfall days
        plt.figure(figsize=(12, 6))

        plt.plot(
            annual_city["year"],
            annual_city["heat_days"],
            marker="o",
            label="Days with Tmax >= 40°C"
        )

        plt.plot(
            annual_city["year"],
            annual_city["extreme_rainfall_days"],
            marker="o",
            label="Days with rainfall >= 50 mm"
        )

        plt.title(
            f"Extreme Weather Indicators - {city}"
        )

        plt.xlabel("Year")
        plt.ylabel("Number of Days")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()

        plt.savefig(
            OUTPUT_DIR / f"{slug}_extreme_weather.png",
            dpi=150
        )

        plt.close()


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():

    print("=" * 65)
    print("CLIMATEADAPTAI")
    print("CLIMATE TREND & EXTREME WEATHER ANALYSIS")
    print("=" * 65)

    global df

    df = load_data()

    # Add heat and rainfall screening indicators
    df["heat_day"] = (
        df["tmax_c"] >= HEAT_THRESHOLD_C
    ).astype(int)

    df["extreme_rain_day"] = (
        df["precipitation_mm"]
        >= EXTREME_RAINFALL_THRESHOLD_MM
    ).astype(int)

    print("\nRunning annual climate analysis...")
    annual = annual_analysis(df)

    print("Running monthly climatology...")
    monthly = monthly_analysis(df)

    print("Analyzing extreme weather events...")
    extremes = extreme_weather_analysis(df)

    print("Calculating long-term trends...")
    trends = city_trend_summary(annual)

    print("Generating graphs...")
    generate_graphs(df, annual)

    print("\n" + "=" * 65)
    print("CLIMATE ANALYSIS COMPLETED SUCCESSFULLY!")
    print("=" * 65)

    print("\nANNUAL RECORDS:", len(annual))
    print("MONTHLY RECORDS:", len(monthly))
    print("CITIES ANALYZED:", df["location"].nunique())

    print("\nCITY-WISE LONG-TERM TRENDS:")
    print(
        trends.round(3).to_string(index=False)
    )

    print("\nEXTREME WEATHER SUMMARY:")
    print(
        extremes.round(3).to_string(index=False)
    )

    print("\nOUTPUT DIRECTORY:")
    print(OUTPUT_DIR)

    print("\nGENERATED REPORTS:")
    print("- annual_climate_trends.csv")
    print("- monthly_climate_climatology.csv")
    print("- city_long_term_trend_summary.csv")
    print("- extreme_weather_summary.csv")
    print("- Five city-wise extreme weather CSV files")
    print("- 15 city-wise climate graphs")

    print("\nAll analysis files generated successfully!")


if __name__ == "__main__":
    main()
