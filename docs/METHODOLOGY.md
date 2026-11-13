# Methodology

## Study data

The project includes two daily gridded climate datasets covering
2001-01-01–2024-12-31 for Gujranwala, Gujrat, Islamabad, Lahore, and
Rawalpindi. Each source file contains 43,830 rows (8,766 per city) and has no
missing cells or duplicate city/date rows in the checked files. The NASA
POWER file has `OK` quality flags for all rows.

The included NASA POWER series for Islamabad and Rawalpindi are identical
across the full period. The corresponding Open-Meteo ERA5 city series differ.
Therefore, NASA-based model results for those two cities are identical and
should not be interpreted as independent local validation.

## Next-day temperature and rainfall model

The model is implemented in `climate_model.py` and uses
`data/multi_city_climate_data.csv`. Each city has separate
`HistGradientBoostingRegressor` models for next-day mean temperature and
rainfall. Features for day *t + 1* are available at the end of day *t*:

- Day-*t* maximum, minimum, and mean temperature and rainfall.
- Seven-day trailing mean temperature and total rainfall.
- Sine and cosine encodings of the target date's day of year.

Rainfall is fitted in `log1p` space and transformed back with `expm1`;
predictions are clipped at zero. The model uses 150 boosting iterations,
15 maximum leaf nodes, L2 regularization of 1.0, and a fixed random seed.

### Evaluation design

The evaluation is chronological. Three separate runs hold out 2022, 2023, and
2024; each run trains only on target dates before its holdout year. Calendar
gaps are excluded from training examples so a missing day is not treated as a
consecutive observation. Every city has 7,663 training examples and 365 test
days for 2022, 8,028 training examples and 365 test days for 2023, and 8,393
training examples and 366 test days for 2024.

Two metrics are shown:

- **MAE**: average absolute prediction error.
- **RMSE**: square-root of average squared error, which penalizes larger
  misses more strongly.

Both metrics are compared with a persistence baseline that predicts the
previous day's temperature or rainfall. Lower scores are better. The report
summarizes the mean of each metric across the five city-specific scores; these
are not pooled row-level scores, and the Islamabad and Rawalpindi records are
not independent in the NASA POWER source. After evaluation, the displayed
next-day estimate is refit on all available history. Since the included data
ends on 2024-12-31, the displayed estimate is for 2025-01-01. It is a
historical model demonstration, not a current forecast.

## Trend-based adaptation guidance

`recommendations.py` compares the first and most recent five-year means. It
requires at least ten annual records.

- A mean-temperature increase of at least 0.5 °C, or an increase of at least
  five annual days at or above 35 °C, triggers a recommendation to pilot
  shade, trees, and reflective roofs.
- A rainfall change of at least 15% up or down prompts water-supply or
  drainage-focused guidance.
- Smaller rainfall changes lead to advice to size storage using monthly
  rainfall and demand instead of annual totals alone.

These are transparent comparison rules, not forecasts or evidence that a
measure will work at a particular site. If climate values are absent or
incomplete, the app explains that recommendations cannot be calculated.

## Adaptation scenario calculations

All calculators use historical planning assumptions; they do not model
infrastructure performance or future climate.

### Rainwater harvesting

```text
estimated litres =
    annual rainfall (mm)
    × roof area (m²)
    × runoff share
    × collection efficiency
```

This uses the unit relationship that 1 mm of rain on 1 m² is 1 litre.
Storage capacity, first-flush losses, rainfall timing, and roof conditions are
not modeled.

### Green-space irrigation

```text
annual demand (L) =
    green-space area (m²)
    × daily water need (L/m²/day)
    × irrigation days

estimated available rainwater (L) =
    annual rainfall (mm)
    × collection roof area (m²)
    × runoff share
    × collection efficiency
```

Rainwater used is the lesser of annual demand and estimated availability;
coverage is used water divided by demand. The comparison does not account for
storage, seasonal timing, evaporation, leakage, or irrigation losses.

### Cool roofs

The calculator multiplies total roof area by the selected coverage percentage.
It reports cool-roof and conventional-roof area only; it does not predict
temperature reduction, energy savings, cost, or health outcomes.

## Sources

- [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
