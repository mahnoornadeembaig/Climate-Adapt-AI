
import sqlite3
import pandas as pd
from pathlib import Path

# ==========================================
# CLIMATEADAPTAI - DATABASE MANAGER
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "climateadaptai.db"

# CSV files and their database table names
DATA_FILES = {

    # Original Gujrat Climate Data
    "climate_data.csv": "climate_records",
    "annual_climate_summary.csv": "annual_summary",
    "monthly_climate_summary.csv": "monthly_summary",

    # Adaptation Simulation Data
    "rainwater_scenario_results.csv": "rainwater_scenarios",
    "urban_green_space_results.csv": "urban_green_space_scenarios",
    "cool_roof_scenario_results.csv": "cool_roof_scenarios",

    # Multi-City Climate Data
    "multi_city_climate_data.csv": "multi_city_climate_records",
    "multi_city_annual_summary.csv": "multi_city_annual_summary",
    "multi_city_monthly_summary.csv": "multi_city_monthly_summary"
}


def create_database():

    print("\n" + "=" * 50)
    print("CLIMATEADAPTAI DATABASE SETUP")
    print("=" * 50)

    connection = sqlite3.connect(DB_PATH)

    try:

        for csv_file, table_name in DATA_FILES.items():

            file_path = DATA_DIR / csv_file

            if not file_path.exists():

                print(f"\nWARNING: File not found: {csv_file}")
                continue

            # Check whether database table already exists
            table_exists = connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
                """,
                (table_name,)
            ).fetchone()

            if table_exists:

                print(f"\nAlready exists: {table_name}")
                continue

            # Read CSV data
            dataframe = pd.read_csv(file_path)

            # Import CSV into SQLite
            dataframe.to_sql(
                table_name,
                connection,
                if_exists="fail",
                index=False
            )

            print(f"\nImported: {csv_file}")
            print(f"Database table: {table_name}")
            print(f"Records: {len(dataframe)}")

        connection.commit()

        print("\n" + "=" * 50)
        print("DATABASE SETUP COMPLETED!")
        print("=" * 50)

        print(f"Database location: {DB_PATH}")

    except Exception as error:

        connection.rollback()
        print("\nDATABASE ERROR:", error)

    finally:

        connection.close()


if __name__ == "__main__":

    create_database()
