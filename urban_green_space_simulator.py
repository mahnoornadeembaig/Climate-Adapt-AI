import csv
import os
from statistics import mean

# ==========================================
# CLIMATEADAPTAI
# URBAN GREEN SPACES SIMULATOR
# ==========================================

INPUT_FILE = "data/rainwater_scenario_results.csv"
OUTPUT_FILE = "data/urban_green_space_results.csv"


def get_positive_number(prompt, default):
    """Get a positive numerical value from the user."""

    while True:
        value = input(f"{prompt} [{default}]: ").strip()

        if value == "":
            return default

        try:
            number = float(value)

            if number > 0:
                return number

            print("Please enter a value greater than zero.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def get_irrigation_days():
    """Get the number of irrigation days."""

    while True:
        value = input(
            "Enter annual irrigation days [180]: "
        ).strip()

        if value == "":
            return 180

        try:
            days = int(value)

            if 1 <= days <= 365:
                return days

            print("Please enter days between 1 and 365.")

        except ValueError:
            print("Please enter a whole number.")


def main():

    print("\n" + "=" * 50)
    print("CLIMATEADAPTAI")
    print("URBAN GREEN SPACES SIMULATOR")
    print("=" * 50)

    # Check whether rainwater results exist
    if not os.path.exists(INPUT_FILE):
        print("\nERROR: Rainwater scenario results not found.")
        print("Please run adaptation_simulator.py first.")
        return

    # User inputs
    green_area = get_positive_number(
        "Enter proposed green space area in m2",
        1000
    )

    daily_water_requirement = get_positive_number(
        "Enter assumed irrigation water requirement (litres/m2/day)",
        3
    )

    irrigation_days = get_irrigation_days()

    # Annual irrigation demand
    annual_water_demand = (
        green_area
        * daily_water_requirement
        * irrigation_days
    )

    # Read annual rainwater harvesting estimates
    results = []

    with open(INPUT_FILE, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            harvested_water = float(
                row["estimated_harvest_litres"]
            )

            covered_water = min(
                harvested_water,
                annual_water_demand
            )

            additional_water = max(
                0,
                annual_water_demand - harvested_water
            )

            coverage_percentage = (
                covered_water / annual_water_demand
            ) * 100

            results.append({
                "year": int(row["year"]),
                "green_space_area_m2": green_area,
                "daily_water_requirement_litres_m2": daily_water_requirement,
                "irrigation_days": irrigation_days,
                "annual_water_demand_litres": round(
                    annual_water_demand, 2
                ),
                "estimated_rainwater_available_litres": round(
                    harvested_water, 2
                ),
                "rainwater_used_for_irrigation_litres": round(
                    covered_water, 2
                ),
                "additional_water_required_litres": round(
                    additional_water, 2
                ),
                "irrigation_coverage_percentage": round(
                    coverage_percentage, 2
                )
            })

    # Save results
    os.makedirs("data", exist_ok=True)

    fieldnames = list(results[0].keys())

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    # Summary
    average_harvest = mean(
        row["estimated_rainwater_available_litres"]
        for row in results
    )

    average_coverage = mean(
        row["irrigation_coverage_percentage"]
        for row in results
    )

    average_additional_water = mean(
        row["additional_water_required_litres"]
        for row in results
    )

    print("\n" + "=" * 50)
    print("SIMULATION COMPLETED!")
    print("=" * 50)

    print(f"Years analyzed: {len(results)}")
    print(f"Green space area: {green_area:.2f} m2")
    print(
        f"Daily water requirement: "
        f"{daily_water_requirement:.2f} litres/m2/day"
    )
    print(f"Irrigation days: {irrigation_days}")

    print(
        f"\nAnnual irrigation demand: "
        f"{annual_water_demand:,.2f} litres"
    )

    print(
        f"Average estimated rainwater: "
        f"{average_harvest:,.2f} litres"
    )

    print(
        f"Average irrigation coverage: "
        f"{average_coverage:.2f}%"
    )

    print(
        f"Average additional water required: "
        f"{average_additional_water:,.2f} litres"
    )

    print(f"\nResults saved at: {OUTPUT_FILE}")

    print("\nIMPORTANT RESEARCH NOTE:")
    print(
        "Water requirements are user-defined assumptions, "
        "not measured local plant water consumption."
    )

    print(
        "This annual comparison does not account for "
        "storage capacity, rainfall timing, evaporation "
        "or actual irrigation system losses."
    )


if __name__ == "__main__":
    main()
