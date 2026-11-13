import csv
import os
import requests

# =====================================
# CLIMATEADAPTAI - GUJRAT CLIMATE DATA
# Data Source: NASA POWER Daily API
# =====================================

LATITUDE = 32.5742
LONGITUDE = 74.0879

START_DATE = "20010101"
END_DATE = "20241231"

LOCATION = "Gujrat, Punjab, Pakistan"

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMETERS = "T2M_MAX,T2M_MIN,T2M,PRECTOTCORR"

params = {
    "parameters": PARAMETERS,
    "community": "RE",
    "longitude": LONGITUDE,
    "latitude": LATITUDE,
    "start": START_DATE,
    "end": END_DATE,
    "format": "JSON",
    "time-standard": "UTC"
}

print("Downloading Gujrat climate data...")

try:
    response = requests.get(
        API_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()
    data = response.json()

    climate = data["properties"]["parameter"]

    output_folder = "data"
    os.makedirs(output_folder, exist_ok=True)

    output_file = os.path.join(
        output_folder,
        "climate_data.csv"
    )

    parameter_names = [
        "T2M_MAX",
        "T2M_MIN",
        "T2M",
        "PRECTOTCORR"
    ]

    dates = sorted(climate["T2M"].keys())

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "date",
            "location",
            "tmax_c",
            "tmin_c",
            "tmean_c",
            "precipitation_mm",
            "source",
            "quality_flag"
        ])

        for date in dates:

            values = {}

            for name in parameter_names:

                value = climate[name].get(date, -999)

                if value is None or float(value) == -999:
                    values[name] = None
                else:
                    values[name] = round(float(value), 2)

            quality = (
                "OK"
                if all(v is not None for v in values.values())
                else "MISSING_VALUE"
            )

            formatted_date = (
                f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            )

            writer.writerow([
                formatted_date,
                LOCATION,
                values["T2M_MAX"],
                values["T2M_MIN"],
                values["T2M"],
                values["PRECTOTCORR"],
                "NASA POWER Daily API",
                quality
            ])

    print("\nSUCCESS!")
    print("Climate data downloaded successfully.")
    print("Saved file:", output_file)
    print("Total records:", len(dates))

except Exception as error:

    print("\nDATA DOWNLOAD FAILED!")
    print("Error:", error)
    print("Please check your internet connection and try again.")
