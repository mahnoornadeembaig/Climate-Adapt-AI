import unittest

import numpy as np
import pandas as pd

from climate_model import train_city_forecasts


class ClimateModelTests(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range("2020-01-01", "2024-12-31", freq="D")
        rows = []
        for city, temperature_offset in (
            ("City A", 0.0),
            ("City B", 2.0),
        ):
            for index, current_date in enumerate(dates):
                seasonal = np.sin(
                    2 * np.pi * current_date.day_of_year / 365.25
                )
                mean_temperature = (
                    22 + temperature_offset + 8 * seasonal
                    + 0.2 * np.sin(index / 13)
                )
                rainfall = max(
                    0.0,
                    2.0 + 1.5 * np.sin(index / 11)
                    + 0.1 * np.cos(index / 3),
                )
                rows.append({
                    "date": current_date,
                    "location": city,
                    "tmax_c": mean_temperature + 5,
                    "tmin_c": mean_temperature - 5,
                    "tmean_c": mean_temperature,
                    "precipitation_mm": rainfall,
                })
        self.daily_data = pd.DataFrame(rows)

    def test_trains_city_models_and_evaluates_chronological_holdout(self):
        result = train_city_forecasts(self.daily_data)

        self.assertEqual(result.test_year, 2024)
        self.assertEqual(set(result.forecasts), {"City A", "City B"})
        for forecast in result.forecasts.values():
            self.assertEqual(forecast.forecast_date.isoformat(), "2025-01-01")
            self.assertEqual(forecast.test_days, 366)
            self.assertGreater(forecast.training_days, forecast.test_days)
            self.assertGreaterEqual(forecast.rainfall_mm, 0)
            self.assertGreaterEqual(forecast.temperature_metrics.mae, 0)
            self.assertGreaterEqual(forecast.rainfall_metrics.rmse, 0)

    def test_supports_an_earlier_chronological_holdout(self):
        result = train_city_forecasts(self.daily_data, test_year=2023)

        self.assertEqual(result.test_year, 2023)
        for forecast in result.forecasts.values():
            self.assertEqual(forecast.test_days, 365)
            self.assertGreater(forecast.training_days, 0)

    def test_rejects_missing_required_climate_columns(self):
        incomplete = self.daily_data.drop(columns=["precipitation_mm"])

        with self.assertRaisesRegex(ValueError, "precipitation_mm"):
            train_city_forecasts(incomplete)

    def test_does_not_train_across_missing_calendar_days(self):
        gap_date = pd.Timestamp("2022-06-15")
        data_with_gap = self.daily_data[
            ~(
                self.daily_data["location"].eq("City A")
                & self.daily_data["date"].eq(gap_date)
            )
        ]

        result = train_city_forecasts(data_with_gap)

        self.assertIn("City A", result.forecasts)
        self.assertIn("City B", result.forecasts)


if __name__ == "__main__":
    unittest.main()
