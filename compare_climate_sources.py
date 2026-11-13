
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# CLIMATEADAPTAI
# NASA POWER vs OPEN-METEO ERA5
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "source_comparison"

NASA_FILE = DATA_DIR / "multi_city_climate_data.csv"
ERA5_FILE = DATA_DIR / "open_meteo_climate_data.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# LOAD AND PREPARE DATA
# ==========================================

def load_and_prepare(file_path, source_name):

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    required_columns = [
        "date",
        "location",
        "tmax_c",
        "tmin_c",
        "tmean_c",
        "precipitation_mm"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{source_name} missing columns: {missing_columns}"
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

    # Extract date components
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Remove duplicate city/date records
    df = df.drop_duplicates(
        subset=["date", "location"]
    )

    print(
        f"{source_name}: {len(df)} valid records"
    )

    return df


# ==========================================
# MAIN FUNCTION
# ==========================================

def main():

    print("=" * 65)
    print("CLIMATEADAPTAI - CLIMATE SOURCE COMPARISON")
    print("NASA POWER vs OPEN-METEO ERA5")
    print("=" * 65)

    # Load datasets
    nasa = load_and_prepare(
        NASA_FILE, "NASA POWER"
    )

    era5 = load_and_prepare(
        ERA5_FILE, "Open-Meteo ERA5"
    )

    # ======================================
    # MATCH DATA BY CITY AND DATE
    # ======================================

    merged = pd.merge(
        nasa,
        era5,
        on=["date", "location"],
        how="inner",
        suffixes=("_nasa", "_era5")
    )

    if merged.empty:
        raise ValueError(
            "No matching city/date records found."
        )

    # IMPORTANT FIX:
    # Extract year and month AFTER merging
    merged["year"] = merged["date"].dt.year
    merged["month"] = merged["date"].dt.month

    print("\nMatched records:", len(merged))
    print(
        "Matched cities:",
        merged["location"].nunique()
    )

    print("\nCity-wise matched records:")
    print(
        merged.groupby("location").size().to_string()
    )

    # ======================================
    # DAILY SOURCE DIFFERENCES
    # ======================================

    variables = [
        "tmax_c",
        "tmin_c",
        "tmean_c",
        "precipitation_mm"
    ]

    for variable in variables:

        merged[f"{variable}_difference"] = (
            merged[f"{variable}_era5"]
            - merged[f"{variable}_nasa"]
        )

    merged.to_csv(
        OUTPUT_DIR / "daily_source_comparison.csv",
        index=False
    )

    # ======================================
    # CITY-WISE COMPARISON
    # ======================================

    city_summary = merged.groupby(
        "location"
    ).agg(

        matched_records=("date", "count"),

        nasa_mean_temperature=(
            "tmean_c_nasa", "mean"
        ),

        era5_mean_temperature=(
            "tmean_c_era5", "mean"
        ),

        nasa_mean_rainfall=(
            "precipitation_mm_nasa", "mean"
        ),

        era5_mean_rainfall=(
            "precipitation_mm_era5", "mean"
        ),

        temperature_mae=(
            "tmean_c_difference",
            lambda x: x.abs().mean()
        ),

        rainfall_mae=(
            "precipitation_mm_difference",
            lambda x: x.abs().mean()
        )

    ).reset_index()

    city_summary.to_csv(
        OUTPUT_DIR / "city_source_comparison.csv",
        index=False
    )

    # ======================================
    # ANNUAL COMPARISON
    # ======================================

    annual = merged.groupby(
        ["location", "year"]
    ).agg(

        nasa_mean_temperature=(
            "tmean_c_nasa", "mean"
        ),

        era5_mean_temperature=(
            "tmean_c_era5", "mean"
        ),

        nasa_total_rainfall=(
            "precipitation_mm_nasa", "sum"
        ),

        era5_total_rainfall=(
            "precipitation_mm_era5", "sum"
        ),

        matched_records=("date", "count")

    ).reset_index()

    annual["temperature_difference_c"] = (
        annual["era5_mean_temperature"]
        - annual["nasa_mean_temperature"]
    )

    annual["rainfall_difference_mm"] = (
        annual["era5_total_rainfall"]
        - annual["nasa_total_rainfall"]
    )

    annual.to_csv(
        OUTPUT_DIR / "annual_source_comparison.csv",
        index=False
    )

    # ======================================
    # MONTHLY CLIMATOLOGY COMPARISON
    # ======================================

    monthly = merged.groupby(
        ["location", "month"]
    ).agg(

        nasa_mean_temperature=(
            "tmean_c_nasa", "mean"
        ),

        era5_mean_temperature=(
            "tmean_c_era5", "mean"
        ),

        nasa_mean_daily_rainfall=(
            "precipitation_mm_nasa", "mean"
        ),

        era5_mean_daily_rainfall=(
            "precipitation_mm_era5", "mean"
        )

    ).reset_index()

    monthly["temperature_difference_c"] = (
        monthly["era5_mean_temperature"]
        - monthly["nasa_mean_temperature"]
    )

    monthly["rainfall_difference_mm"] = (
        monthly["era5_mean_daily_rainfall"]
        - monthly["nasa_mean_daily_rainfall"]
    )

    monthly.to_csv(
        OUTPUT_DIR / "monthly_source_comparison.csv",
        index=False
    )

    # ======================================
    # VISUALIZATIONS
    # ======================================

    for city in sorted(
        merged["location"].unique()
    ):

        city_data = merged[
            merged["location"] == city
        ].sort_values("date")

        city_annual = annual[
            annual["location"] == city
        ]

        city_slug = (
            city.split(",")[0]
            .lower()
            .replace(" ", "_")
        )

        # ----------------------------------
        # DAILY TEMPERATURE COMPARISON
        # ----------------------------------

        plt.figure(figsize=(14, 6))

        plt.plot(
            city_data["date"],
            city_data["tmean_c_nasa"],
            label="NASA POWER",
            alpha=0.75
        )

        plt.plot(
            city_data["date"],
            city_data["tmean_c_era5"],
            label="Open-Meteo ERA5",
            alpha=0.75
        )

        plt.title(
            f"Daily Mean Temperature Comparison - {city}"
        )

        plt.xlabel("Date")
        plt.ylabel("Temperature (°C)")
        plt.legend()
        plt.grid(alpha=0.25)
        plt.tight_layout()

        plt.savefig(
            OUTPUT_DIR / f"{city_slug}_temperature.png",
            dpi=150
        )

        plt.close()

        # ----------------------------------
        # ANNUAL RAINFALL COMPARISON
        # ----------------------------------

        plt.figure(figsize=(12, 6))

        plt.plot(
            city_annual["year"],
            city_annual["nasa_total_rainfall"],
            marker="o",
            label="NASA POWER"
        )

        plt.plot(
            city_annual["year"],
            city_annual["era5_total_rainfall"],
            marker="o",
            label="Open-Meteo ERA5"
        )

        plt.title(
            f"Annual Rainfall Comparison - {city}"
        )

        plt.xlabel("Year")
        plt.ylabel("Annual Rainfall (mm)")
        plt.legend()
        plt.grid(alpha=0.25)
        plt.tight_layout()

        plt.savefig(
            OUTPUT_DIR / f"{city_slug}_rainfall.png",
            dpi=150
        )

        plt.close()

    # ======================================
    # FINAL SUMMARY
    # ======================================

    print("\n" + "=" * 65)
    print("COMPARISON COMPLETED SUCCESSFULLY!")
    print("=" * 65)

    print("\nMatched records:", len(merged))
    print(
        "Cities analyzed:",
        merged["location"].nunique()
    )

    print("\nCITY-WISE COMPARISON:")
    print(
        city_summary.round(3).to_string(index=False)
    )

    print("\nANNUAL COMPARISON SAMPLE:")
    print(
        annual.head(10).round(3).to_string(index=False)
    )

    print("\nOUTPUT DIRECTORY:")
    print(OUTPUT_DIR)

    print("\nGENERATED FILES:")
    print("1. daily_source_comparison.csv")
    print("2. city_source_comparison.csv")
    print("3. annual_source_comparison.csv")
    print("4. monthly_source_comparison.csv")
    print("5. Five city-wise temperature graphs")
    print("6. Five city-wise rainfall graphs")

    print("\nAll comparison files saved successfully!")


if __name__ == "__main__":
    main()
