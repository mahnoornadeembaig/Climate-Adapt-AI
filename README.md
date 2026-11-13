# Climate Adapt AI Simulator

Climate Adapt AI Simulator is a Streamlit research and decision-support app
for historical climate analysis and simplified urban adaptation scenarios in
five Pakistani cities.

## What it does

- Shows city-level temperature and rainfall summaries for 2001–2024.
- Compares NASA POWER and Open-Meteo ERA5 historical datasets.
- Trains separate next-day mean-temperature and rainfall regressors by city,
  evaluates them against a previous-day baseline, and displays the limitation
  that the resulting estimate is historical rather than current.
- Generates practical, rule-based guidance from historical climate trends and
  simulation results.
- Simulates rooftop rainwater collection, green-space irrigation coverage,
  and cool-roof coverage using visible assumptions.
- Exports the current page's results as CSV or PDF.
- Requires registration and login; the account database is stored locally.

The app is a project prototype, not an operational forecasting service.
Adaptation suggestions are planning prompts, not engineering or emergency
advice.

## Run locally

Python 3.10 or later is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run dashboard.py
```

Create an account in the app, then sign in. The application stores account
records in the local `climateadaptai.db` SQLite file. Do not publish that file
or share account credentials.

## Data

The included daily datasets contain 43,830 records each: five cities with
complete daily records from 2001-01-01 through 2024-12-31.

- `data/multi_city_climate_data.csv` — NASA POWER daily data; used by the
  next-day model.
- `data/open_meteo_climate_data.csv` — Open-Meteo ERA5 daily data; used for
  source comparisons.

Both sources are gridded estimates, not direct observations from local weather
stations. NASA POWER records for Islamabad and Rawalpindi are identical in the
included file; see the data limitation in the [project report](docs/PROJECT_REPORT.md).

## Tests

```powershell
python -m unittest discover -s tests -v
```

See the [testing record](docs/TESTING.md) for the application-level checks and
measured model results.

## Project documentation

- [Project report](docs/PROJECT_REPORT.md)
- [Methodology](docs/METHODOLOGY.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Testing and results](docs/TESTING.md)
