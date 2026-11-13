import csv
import time
import requests
from pathlib import Path

# ==========================================
# PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

EXISTING_FILE = BASE_DIR / "data" / "climate_data.csv"
OUTPUT_FILE = BASE_DIR / "data" / "multi_city_climate_data.csv"

START_DATE = "20010101"
END_DATE = "20241231"

API_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)

# New cities with their coordinates
CITIES = {
    "Lahore, Punjab, Pakistan": {
        "latitude": 31.5204,
        "longitude": 74.3587
    },
    "Gujranwala, Punjab, Pakistan": {
        "latitude": 32.1877,
        "longitude": 74.1945
    },
    "Rawalpindi, Punjab, Pakistan": {
        "latitude": 33.5651,
        "longitude": 73.0169
    },
    "Islamabad, Pakistan": {
        "latitude": 33.6844,
        "longitude": 73.0479
    }
}

FIELDS = [
    "date",
    "location",
    "tmax_c",
    "tmin_c",
    "tmean_c",
    "precipitation_mm",
    "source",
    "quality_flag"
]


def download_city_data(city_name, coordinates):

    print(f"\nDownloading data for {city_name}...")

    params = {
        "parameters": "T2M_MAX,T2M_MIN,T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": coordinates["longitude"],
        "latitude": coordinates["latitude"],
        "start": START_DATE,
        "end": END_DATE,
        "format": "JSON"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=180
    )

    response.raise_for_status()

    result = response.json()

    parameters = result["properties"]["parameter"]

    tmax_data = parameters["T2M_MAX"]
    tmin_data = parameters["T2M_MIN"]
    tmean_data = parameters["T2M"]
    rainfall_data = parameters["PRECTOTCORR"]

    city_rows = []
    missing_count = 0

    for date in sorted(tmean_data):

        tmax = tmax_data[date]
        tmin = tmin_data[date]
        tmean = tmean_data[date]
        rainfall = rainfall_data[date]

        # Skip unavailable NASA POWER values
        values = [tmax, tmin, tmean, rainfall]

        if any(value == -999 for value in values):
            missing_count += 1
            continue

        city_rows.append({
            "date": (
                f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            ),
            "location": city_name,
            "tmax_c": round(float(tmax), 2),
            "tmin_c": round(float(tmin), 2),
            "tmean_c": round(float(tmean), 2),
            "precipitation_mm": round(float(rainfall), 2),
            "source": "NASA POWER Daily API",
            "quality_flag": "OK"
        })

    print(f"Records collected: {len(city_rows)}")
    print(f"Missing records skipped: {missing_count}")

    return city_rows


def main():

    print("=" * 50)
    print("CLIMATEADAPTAI MULTI-CITY DATA COLLECTION")
    print("=" * 50)

    # Preserve existing Gujrat data
    if not EXISTING_FILE.exists():
        raise FileNotFoundError(
            "Existing Gujrat climate_data.csv was not found."
        )

    with open(
        EXISTING_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)
        all_rows = list(reader)

    print(f"\nExisting records: {len(all_rows)}")

    new_rows = []

    # Download the four additional cities
    for city_name, coordinates in CITIES.items():

        city_rows = download_city_data(
            city_name,
            coordinates
        )

        new_rows.extend(city_rows)

        # Small pause between API requests
        time.sleep(2)

    # Combine original Gujrat data with new city data
    all_rows.extend(new_rows)

    # Sort records by city and date
    all_rows.sort(
        key=lambda row: (
            row["location"],
            row["date"]
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Write a separate combined dataset
    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS
        )

        writer.writeheader()
        writer.writerows(all_rows)

    print("\n" + "=" * 50)
    print("DATA COLLECTION COMPLETED!")
    print("=" * 50)

    print(f"Total records: {len(all_rows)}")
    print(f"New records: {len(new_rows)}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
