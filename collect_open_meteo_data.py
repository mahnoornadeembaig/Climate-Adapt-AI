import requests
import pandas as pd
import time
from pathlib import Path

# ==========================================
# CLIMATEADAPTAI - OPEN-METEO DATA COLLECTION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CACHE_DIR = DATA_DIR / "open_meteo_city_cache"
OUTPUT_FILE = DATA_DIR / "open_meteo_climate_data.csv"

START_DATE = "2001-01-01"
END_DATE = "2024-12-31"

API_URL = "https://archive-api.open-meteo.com/v1/archive"

CITIES = {
    "Gujrat, Punjab, Pakistan": {
        "latitude": 32.5742,
        "longitude": 74.0879
    },
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


def collect_city_data(city_name, coordinates, cache_file):

    # Reuse previously downloaded city data
    if cache_file.exists():

        cached_data = pd.read_csv(cache_file)

        if len(cached_data) == 8766:
            print(f"Already downloaded. Using saved data: {city_name}")
            return cached_data

        print(f"Cache incomplete. Downloading again: {city_name}")

    params = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": [
            "temperature_2m_mean",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum"
        ],
        "timezone": "Asia/Karachi",
        "models": "era5"
    }

    for attempt in range(1, 6):

        try:

            print(f"\nDownloading: {city_name}")
            print(f"Attempt: {attempt}/5")

            response = requests.get(
                API_URL,
                params=params,
                timeout=180
            )

            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                try:
                    wait_time = int(retry_after)
                except (TypeError, ValueError):
                    wait_time = 60 * attempt

                print(
                    f"API rate limit reached. "
                    f"Waiting {wait_time} seconds..."
                )

                if attempt < 5:
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

            response.raise_for_status()

            data = response.json()
            daily = data["daily"]

            dataframe = pd.DataFrame({
                "date": daily["time"],
                "location": city_name,
                "tmax_c": daily["temperature_2m_max"],
                "tmin_c": daily["temperature_2m_min"],
                "tmean_c": daily["temperature_2m_mean"],
                "precipitation_mm": daily["precipitation_sum"]
            })

            dataframe["source"] = "Open-Meteo ERA5"
            dataframe["quality_flag"] = "OK"

            if len(dataframe) != 8766:
                raise ValueError(
                    f"Expected 8766 records, received {len(dataframe)}"
                )

            # Save each city immediately
            dataframe.to_csv(cache_file, index=False)

            print(f"Successfully saved: {len(dataframe)} records")

            return dataframe

        except requests.exceptions.RequestException as error:

            print(f"Request error: {error}")

            if attempt == 5:
                raise

            wait_time = 30 * attempt
            print(f"Retrying after {wait_time} seconds...")
            time.sleep(wait_time)


def main():

    print("=" * 60)
    print("CLIMATEADAPTAI - OPEN-METEO ERA5 DATA COLLECTION")
    print("=" * 60)

    DATA_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

    all_data = []

    try:

        for index, (city_name, coordinates) in enumerate(CITIES.items()):

            city_slug = city_name.split(",")[0].lower().replace(" ", "_")
            cache_file = CACHE_DIR / f"{city_slug}.csv"

            city_data = collect_city_data(
                city_name,
                coordinates,
                cache_file
            )

            all_data.append(city_data)

            # Pause between API requests
            if index < len(CITIES) - 1:
                print("\nWaiting 15 seconds before next city...")
                time.sleep(15)

        final_data = pd.concat(
            all_data,
            ignore_index=True
        )

        final_data["date"] = pd.to_datetime(final_data["date"])

        final_data = final_data.sort_values(
            ["location", "date"]
        )

        print("\n" + "=" * 60)
        print("DATA VALIDATION")
        print("=" * 60)

        print("Total records:", len(final_data))
        print("Total cities:", final_data["location"].nunique())
        print("Missing values:", final_data.isnull().sum().sum())

        print("\nCity-wise records:")
        print(final_data.groupby("location").size())

        final_data.to_csv(
            OUTPUT_FILE,
            index=False,
            date_format="%Y-%m-%d"
        )

        print("\n" + "=" * 60)
        print("DATA COLLECTION COMPLETED!")
        print("=" * 60)

        print("\nSaved file:", OUTPUT_FILE)

    except Exception as error:

        print("\nDATA COLLECTION PAUSED OR FAILED!")
        print("Error:", error)
        print("Successfully downloaded city files are preserved in:")
        print(CACHE_DIR)


if __name__ == "__main__":
    main()