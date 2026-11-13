import csv
import os
from statistics import mean

INPUT_FILE = "data/annual_climate_summary.csv"
OUTPUT_FILE = "data/rainwater_scenario_results.csv"

print("=" * 50)
print("CLIMATEADAPTAI - RAINWATER MANAGEMENT SIMULATOR")
print("=" * 50)

# Demonstration inputs; replace with actual site measurements
try:
    area_input = input(
        "\nEnter rooftop catchment area in m2 [1000]: "
    ).strip()
    roof_area = float(area_input) if area_input else 1000

    runoff_input = input(
        "Enter runoff coefficient [0.80]: "
    ).strip()
    runoff_coefficient = float(runoff_input) if runoff_input else 0.80

    efficiency_input = input(
        "Enter collection efficiency [0.80]: "
    ).strip()
    collection_efficiency = (
        float(efficiency_input) if efficiency_input else 0.80
    )

    if roof_area <= 0:
        raise ValueError("Roof area must be greater than zero.")

    if not 0 <= runoff_coefficient <= 1:
        raise ValueError("Runoff coefficient must be between 0 and 1.")

    if not 0 <= collection_efficiency <= 1:
        raise ValueError("Collection efficiency must be between 0 and 1.")

except ValueError as error:
    print("\nInvalid input:", error)
    raise SystemExit

if not os.path.exists(INPUT_FILE):
    print("\nAnnual climate summary not found!")
    raise SystemExit

results = []

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        year = int(row["year"])
        rainfall_mm = float(row["annual_rainfall_mm"])

        # 1 mm rainfall on 1 m2 = 1 litre
        harvested_litres = (
            rainfall_mm
            * roof_area
            * runoff_coefficient
            * collection_efficiency
        )

        results.append({
            "year": year,
            "annual_rainfall_mm": rainfall_mm,
            "roof_area_m2": roof_area,
            "runoff_coefficient": runoff_coefficient,
            "collection_efficiency": collection_efficiency,
            "estimated_harvest_litres": round(harvested_litres, 2),
            "estimated_harvest_m3": round(
                harvested_litres / 1000, 2
            )
        })

os.makedirs("data", exist_ok=True)

fields = [
    "year",
    "annual_rainfall_mm",
    "roof_area_m2",
    "runoff_coefficient",
    "collection_efficiency",
    "estimated_harvest_litres",
    "estimated_harvest_m3"
]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

if results:
    average_water = mean(
        row["estimated_harvest_litres"] for row in results
    )

    highest = max(
        results, key=lambda row: row["estimated_harvest_litres"]
    )

    lowest = min(
        results, key=lambda row: row["estimated_harvest_litres"]
    )

    print("\nSIMULATION COMPLETED!")
    print("-" * 40)
    print("Years analyzed:", len(results))
    print("Roof area:", roof_area, "m2")
    print("Runoff coefficient:", runoff_coefficient)
    print("Collection efficiency:", collection_efficiency)

    print(
        "\nAverage annual harvest:",
        round(average_water, 2), "litres"
    )

    print(
        "Average annual harvest:",
        round(average_water / 1000, 2), "m3"
    )

    print(
        "\nHighest estimated harvest:",
        highest["year"],
        round(highest["estimated_harvest_litres"], 2),
        "litres"
    )

    print(
        "Lowest estimated harvest:",
        lowest["year"],
        round(lowest["estimated_harvest_litres"], 2),
        "litres"
    )

    print("\nResults saved at:", OUTPUT_FILE)

    print(
        "\nNOTE: These are theoretical estimates based on "
        "historical rainfall and user-entered assumptions. "
        "Actual collection depends on roof condition, storage "
        "capacity, first-flush losses and system design."
    )
