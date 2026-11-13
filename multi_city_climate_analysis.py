import pandas as pd
from pathlib import Path

# ==========================================
# CLIMATEADAPTAI MULTI-CITY ANALYSIS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "data" / "multi_city_climate_data.csv"

ANNUAL_FILE = BASE_DIR / "data" / "multi_city_annual_summary.csv"
MONTHLY_FILE = BASE_DIR / "data" / "multi_city_monthly_summary.csv"

print("=" * 55)
print("CLIMATEADAPTAI MULTI-CITY CLIMATE ANALYSIS")
print("=" * 55)

# Load dataset
df = pd.read_csv(INPUT_FILE)

# Validate required columns
required_columns = [
    "date",
    "location",
    "tmax_c",
    "tmin_c",
    "tmean_c",
    "precipitation_mm"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Prepare dates and numeric values
df["date"] = pd.to_datetime(df["date"], errors="coerce")

numeric_columns = [
    "tmax_c",
    "tmin_c",
    "tmean_c",
    "precipitation_mm"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required_columns)

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# Screening indicator, not an official heatwave definition
df["hot_day"] = df["tmax_c"] >= 35

# ==========================================
# ANNUAL CLIMATE SUMMARY
# ==========================================

annual = (
    df.groupby(["location", "year"])
    .agg(
        days=("date", "count"),
        avg_tmax_c=("tmax_c", "mean"),
        avg_tmin_c=("tmin_c", "mean"),
        avg_tmean_c=("tmean_c", "mean"),
        annual_rainfall_mm=("precipitation_mm", "sum"),
        days_tmax_35c_or_above=("hot_day", "sum")
    )
    .reset_index()
)

round_columns = [
    "avg_tmax_c",
    "avg_tmin_c",
    "avg_tmean_c",
    "annual_rainfall_mm"
]

annual[round_columns] = annual[round_columns].round(2)

annual = annual.sort_values(["location", "year"])

annual.to_csv(ANNUAL_FILE, index=False)

# ==========================================
# MONTHLY CLIMATE SUMMARY
# ==========================================

# First calculate each city's monthly values
# separately for every year.

monthly_yearly = (
    df.groupby(["location", "year", "month"])
    .agg(
        avg_tmax_c=("tmax_c", "mean"),
        avg_tmin_c=("tmin_c", "mean"),
        avg_tmean_c=("tmean_c", "mean"),
        monthly_rainfall_mm=("precipitation_mm", "sum")
    )
    .reset_index()
)

# Then calculate average monthly climate
# across all available years.

monthly = (
    monthly_yearly.groupby(["location", "month"])
    .agg(
        years_available=("year", "nunique"),
        avg_tmax_c=("avg_tmax_c", "mean"),
        avg_tmin_c=("avg_tmin_c", "mean"),
        avg_tmean_c=("avg_tmean_c", "mean"),
        avg_monthly_rainfall_mm=("monthly_rainfall_mm", "mean")
    )
    .reset_index()
)

monthly[[
    "avg_tmax_c",
    "avg_tmin_c",
    "avg_tmean_c",
    "avg_monthly_rainfall_mm"
]] = monthly[[
    "avg_tmax_c",
    "avg_tmin_c",
    "avg_tmean_c",
    "avg_monthly_rainfall_mm"
]].round(2)

monthly = monthly.sort_values(["location", "month"])

monthly.to_csv(MONTHLY_FILE, index=False)

# ==========================================
# COMPLETION REPORT
# ==========================================

print("\nANALYSIS COMPLETED SUCCESSFULLY!")

print("\nCities analyzed:")
for city in sorted(df["location"].unique()):
    print("-", city)

print("\nTotal valid records:", len(df))

print("\nAnnual summary records:", len(annual))
print("Monthly summary records:", len(monthly))

print("\nAnnual summary saved:", ANNUAL_FILE)
print("Monthly summary saved:", MONTHLY_FILE)

print("\nAnnual summary preview:")
print(annual.head(10).to_string(index=False))

print("\n" + "=" * 55)
