import csv
import os

# ==========================================
# CLIMATEADAPTAI
# COOL ROOF ADAPTATION SIMULATOR
# ==========================================

OUTPUT_FILE = "data/cool_roof_scenario_results.csv"


def get_positive_number(prompt, default):

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


def get_percentage(prompt, default):

    while True:
        value = input(f"{prompt} [{default}]: ").strip()

        if value == "":
            return default

        try:
            number = float(value)

            if 0 <= number <= 100:
                return number

            print("Please enter a percentage between 0 and 100.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def main():

    print("\n" + "=" * 50)
    print("CLIMATEADAPTAI")
    print("COOL ROOF ADAPTATION SIMULATOR")
    print("=" * 50)

    # User inputs
    total_roof_area = get_positive_number(
        "Enter total roof area in m2",
        1000
    )

    coverage_percentages = [25, 50, 75, 100]

    # Save scenario results
    results = []

    for coverage in coverage_percentages:

        cool_roof_area = (
            total_roof_area * coverage / 100
        )

        conventional_roof_area = (
            total_roof_area - cool_roof_area
        )

        results.append({
            "total_roof_area_m2": round(
                total_roof_area, 2
            ),
            "cool_roof_coverage_percentage": coverage,
            "cool_roof_area_m2": round(
                cool_roof_area, 2
            ),
            "conventional_roof_area_m2": round(
                conventional_roof_area, 2
            )
        })

    # Save CSV report
    os.makedirs("data", exist_ok=True)

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        fieldnames = [
            "total_roof_area_m2",
            "cool_roof_coverage_percentage",
            "cool_roof_area_m2",
            "conventional_roof_area_m2"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    # Display results
    print("\n" + "=" * 50)
    print("COOL ROOF SCENARIO RESULTS")
    print("=" * 50)

    print(f"Total roof area: {total_roof_area:.2f} m2")

    for row in results:

        print(
            f"\nCool roof coverage: "
            f"{row['cool_roof_coverage_percentage']}%"
        )

        print(
            f"Cool roof area: "
            f"{row['cool_roof_area_m2']:.2f} m2"
        )

        print(
            f"Conventional roof area: "
            f"{row['conventional_roof_area_m2']:.2f} m2"
        )

    print("\nSIMULATION COMPLETED!")

    print(f"Scenarios generated: {len(results)}")

    print(f"Results saved at: {OUTPUT_FILE}")

    print("\nIMPORTANT RESEARCH NOTE:")
    print(
        "These are area-based planning scenarios only. "
        "They do not estimate actual temperature reduction, "
        "energy savings or financial benefits."
    )


if __name__ == "__main__":
    main()
