# Testing and Results

## Automated unit tests

Run from the project root:

```powershell
python -m unittest discover -s tests -v
```

Latest run: **16 tests passed**. Coverage includes:

- Chronological city-model training for the default and an earlier holdout
  year, holdout date/count, required columns, nonnegative rainfall estimates,
  and calendar-gap handling.
- Trend recommendations for warming/drying histories, short histories,
  unavailable histories, and all-null annual values.
- Readable report labels, CSV section/city context, safe filenames, and valid
  PDF output.
- Dashboard navigation, report controls, developer-page gating, all five
  city predictions, and persistence of downloadable simulation results.

## Application checks

Streamlit `AppTest` was used against the actual dashboard:

- All eight public navigation pages rendered without app exceptions.
- CSV and PDF download controls rendered on each page with reportable data.
- Climate estimates and model-evaluation sections rendered for all five
  cities, with estimate date 2025-01-01.
- Rainwater simulation was exercised for 2001 with a 600 m² roof.
- Green-space simulation was exercised for 2010 with a 500 m² area.
- Cool-roof simulation was exercised with a 500 m² roof and 100% coverage.
- Simulation reports persisted in session state and the CSV/PDF controls
  rendered after the simulations.
- Simulation result tables rendered without the earlier mixed-type Arrow
  serialization warning.
- Dark mode rendered, and the developer-only database page stayed hidden by
  default and rendered when explicitly enabled.

These checks use the bundled data and selected scenarios; they do not
constitute field validation of real adaptation projects.

## Data audit

| File | Rows | Coverage | Missing cells | Duplicate city/date rows | Quality flags |
|---|---:|---|---:|---:|---|
| `multi_city_climate_data.csv` | 43,830 | 2001-01-01–2024-12-31 | 0 | 0 | 43,830 `OK` |
| `open_meteo_climate_data.csv` | 43,830 | 2001-01-01–2024-12-31 | 0 | 0 | 43,830 `OK` |

Each city has 8,766 daily rows in each file. The NASA POWER temperature and
rainfall series for Islamabad and Rawalpindi are identical; the Open-Meteo
series are not. This source-level discrepancy is documented as a limitation
and should be investigated before making independent city claims.

## Model evaluation summary

The chronological holdouts cover 2022, 2023, and 2024 (365, 365, and 366 days
per city). All five city models beat the previous-day baseline on MAE and RMSE
for both measures in each holdout. The report contains the 2024 city-level
scores and the three-year mean city-level scores, with the averaging method
and data-dependence caveat documented in the [project report](PROJECT_REPORT.md).

## Editor diagnostics

Pylance diagnostics were checked for the modified application, model,
recommendation, and reporting modules. No diagnostics were reported after
removing unused model imports.
