import csv
import os
from datetime import datetime

INPUT_FILE = "data/climate_data.csv"
REPORT_FILE = "data/data_quality_report.txt"

print("Starting Climate Data Quality Check...")

if not os.path.exists(INPUT_FILE):
    print("ERROR: Climate dataset not found!")
    raise SystemExit

total_records = 0
missing_values = 0
duplicate_dates = 0
invalid_dates = 0
invalid_temperatures = 0
invalid_precipitation = 0
non_ok_flags = 0

seen_dates = set()

with open(INPUT_FILE, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        total_records += 1

        date = row["date"]

        # Check duplicate dates
        if date in seen_dates:
            duplicate_dates += 1
        else:
            seen_dates.add(date)

        # Check date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            invalid_dates += 1

        # Check missing values
        fields = [
            "tmax_c",
            "tmin_c",
            "tmean_c",
            "precipitation_mm"
        ]

        for field in fields:
            if not row[field] or row[field].strip() == "":
                missing_values += 1

        try:
            tmax = float(row["tmax_c"])
            tmin = float(row["tmin_c"])
            tmean = float(row["tmean_c"])

            if (
                not (-90 <= tmax <= 60)
                or not (-90 <= tmin <= 60)
                or not (-90 <= tmean <= 60)
                or tmax < tmin
                or not (tmin <= tmean <= tmax)
            ):
                invalid_temperatures += 1

        except (ValueError, TypeError):
            invalid_temperatures += 1

        try:
            rainfall = float(row["precipitation_mm"])

            if rainfall < 0 or rainfall > 2000:
                invalid_precipitation += 1

        except (ValueError, TypeError):
            invalid_precipitation += 1

        if row["quality_flag"] != "OK":
            non_ok_flags += 1

# Generate quality report
os.makedirs("data", exist_ok=True)

report = f"""
CLIMATEADAPTAI - DATA QUALITY REPORT
====================================

Dataset: Gujrat, Punjab, Pakistan
Source: NASA POWER Daily API
Study Period: 2001-2024

Total Records: {total_records}

DATA QUALITY CHECKS
-------------------

Duplicate Dates: {duplicate_dates}
Missing Values: {missing_values}
Invalid Dates: {invalid_dates}
Invalid Temperature Records: {invalid_temperatures}
Invalid Precipitation Records: {invalid_precipitation}
Non-OK Quality Flags: {non_ok_flags}

Expected Records: 8766

Record Count Check: {
    "PASS" if total_records == 8766 else "CHECK REQUIRED"
}

Overall Status: {
    "CHECKS PASSED"
    if all(value == 0 for value in [
        duplicate_dates,
        missing_values,
        invalid_dates,
        invalid_temperatures,
        invalid_precipitation,
        non_ok_flags
    ]) and total_records == 8766
    else "REVIEW REQUIRED"
}

Note:
This report identifies potential data quality issues.
It does not modify the original dataset.
"""

with open(REPORT_FILE, "w", encoding="utf-8") as file:
    file.write(report)

print("\nDATA QUALITY CHECK COMPLETED!")
print(report)
print("Report saved at:", REPORT_FILE)
