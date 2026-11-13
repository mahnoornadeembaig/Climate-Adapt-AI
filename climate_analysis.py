import csv
import os
from collections import defaultdict
from datetime import datetime

INPUT_FILE = "data/climate_data.csv"
ANNUAL_FILE = "data/annual_climate_summary.csv"
MONTHLY_FILE = "data/monthly_climate_summary.csv"

print("Starting Climate Analysis...")

annual = defaultdict(lambda: {
    "days": 0,
    "tmax": 0,
    "tmin": 0,
    "tmean": 0,
    "rainfall": 0,
    "hot_days": 0
})

monthly_yearly = defaultdict(lambda: {
    "days": 0,
    "tmax": 0,
    "tmin": 0,
    "tmean": 0,
    "rainfall": 0
})

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        date = datetime.strptime(row["date"], "%Y-%m-%d")
        year = date.year
        month = date.month

        tmax = float(row["tmax_c"])
        tmin = float(row["tmin_c"])
        tmean = float(row["tmean_c"])
        rainfall = float(row["precipitation_mm"])

        a = annual[year]
        a["days"] += 1
        a["tmax"] += tmax
        a["tmin"] += tmin
        a["tmean"] += tmean
        a["rainfall"] += rainfall

        if tmax >= 35:
            a["hot_days"] += 1

        m = monthly_yearly[(year, month)]
        m["days"] += 1
        m["tmax"] += tmax
        m["tmin"] += tmin
        m["tmean"] += tmean
        m["rainfall"] += rainfall

os.makedirs("data", exist_ok=True)

# Annual summary
with open(ANNUAL_FILE, "w", newline="", encoding="utf-8") as file:
    fields = [
        "year",
        "days",
        "avg_tmax_c",
        "avg_tmin_c",
        "avg_tmean_c",
        "annual_rainfall_mm",
        "days_tmax_35c_or_above"
    ]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for year in sorted(annual):
        a = annual[year]
        days = a["days"]

        writer.writerow({
            "year": year,
            "days": days,
            "avg_tmax_c": round(a["tmax"] / days, 2),
            "avg_tmin_c": round(a["tmin"] / days, 2),
            "avg_tmean_c": round(a["tmean"] / days, 2),
            "annual_rainfall_mm": round(a["rainfall"], 2),
            "days_tmax_35c_or_above": a["hot_days"]
        })

# Monthly climatology:
# Average each calendar month's results across all available years.
monthly_totals = defaultdict(lambda: {
    "years": 0,
    "avg_tmax": 0,
    "avg_tmin": 0,
    "avg_tmean": 0,
    "avg_rainfall": 0
})

for (year, month), m in monthly_yearly.items():
    days = m["days"]
    item = monthly_totals[month]

    item["years"] += 1
    item["avg_tmax"] += m["tmax"] / days
    item["avg_tmin"] += m["tmin"] / days
    item["avg_tmean"] += m["tmean"] / days
    item["avg_rainfall"] += m["rainfall"]

with open(MONTHLY_FILE, "w", newline="", encoding="utf-8") as file:
    fields = [
        "month",
        "years_available",
        "avg_tmax_c",
        "avg_tmin_c",
        "avg_tmean_c",
        "avg_monthly_rainfall_mm"
    ]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for month in range(1, 13):
        item = monthly_totals[month]
        years = item["years"]

        if years == 0:
            continue

        writer.writerow({
            "month": month,
            "years_available": years,
            "avg_tmax_c": round(item["avg_tmax"] / years, 2),
            "avg_tmin_c": round(item["avg_tmin"] / years, 2),
            "avg_tmean_c": round(item["avg_tmean"] / years, 2),
            "avg_monthly_rainfall_mm": round(
                item["avg_rainfall"] / years, 2
            )
        })

print("\nCLIMATE ANALYSIS COMPLETED!")
print("Annual summary:", ANNUAL_FILE)
print("Monthly summary:", MONTHLY_FILE)
print("Years analyzed:", len(annual))
print("Months analyzed:", len(monthly_totals))
