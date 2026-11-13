import csv
import os
import matplotlib.pyplot as plt

ANNUAL_FILE = "data/annual_climate_summary.csv"
MONTHLY_FILE = "data/monthly_climate_summary.csv"

OUTPUT_FOLDER = "outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def read_csv(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))

annual = read_csv(ANNUAL_FILE)
monthly = read_csv(MONTHLY_FILE)

years = [int(row["year"]) for row in annual]
annual_temp = [float(row["avg_tmean_c"]) for row in annual]
annual_rain = [float(row["annual_rainfall_mm"]) for row in annual]
hot_days = [
    int(row["days_tmax_35c_or_above"])
    for row in annual
]

months = [int(row["month"]) for row in monthly]
monthly_temp = [float(row["avg_tmean_c"]) for row in monthly]
monthly_rain = [
    float(row["avg_monthly_rainfall_mm"])
    for row in monthly
]

month_names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

def save_graph(filename):
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_FOLDER, filename),
        dpi=300
    )
    plt.close()
    print("Saved:", filename)

# 1. Annual average temperature
plt.figure(figsize=(10, 5))
plt.plot(years, annual_temp, marker="o")
plt.title("Annual Average Mean Temperature - Gujrat")
plt.xlabel("Year")
plt.ylabel("Temperature (°C)")
plt.grid(True)
save_graph("annual_temperature.png")

# 2. Annual rainfall
plt.figure(figsize=(10, 5))
plt.bar(years, annual_rain)
plt.title("Annual Rainfall - Gujrat")
plt.xlabel("Year")
plt.ylabel("Rainfall (mm)")
plt.grid(axis="y")
save_graph("annual_rainfall.png")

# 3. Annual hot days
plt.figure(figsize=(10, 5))
plt.plot(years, hot_days, marker="o")
plt.title("Annual Days with Maximum Temperature >= 35°C")
plt.xlabel("Year")
plt.ylabel("Number of Days")
plt.grid(True)
save_graph("annual_hot_days.png")

# 4. Monthly average temperature
plt.figure(figsize=(10, 5))
plt.plot(month_names, monthly_temp, marker="o")
plt.title("Monthly Average Mean Temperature - Gujrat")
plt.xlabel("Month")
plt.ylabel("Temperature (°C)")
plt.grid(True)
save_graph("monthly_temperature.png")

# 5. Monthly average rainfall
plt.figure(figsize=(10, 5))
plt.bar(month_names, monthly_rain)
plt.title("Average Monthly Rainfall - Gujrat")
plt.xlabel("Month")
plt.ylabel("Rainfall (mm)")
plt.grid(axis="y")
save_graph("monthly_rainfall.png")

print("\nALL CLIMATE GRAPHS GENERATED SUCCESSFULLY!")
