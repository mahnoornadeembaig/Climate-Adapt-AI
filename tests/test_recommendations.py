import unittest

import pandas as pd

from recommendations import climate_analysis_recommendations


class ClimateRecommendationTests(unittest.TestCase):
    def test_gives_cooling_and_water_guidance_for_warming_and_drying_trends(self):
        rows = []
        for year in range(2001, 2025):
            elapsed = year - 2001
            rows.append({
                "year": year,
                "avg_tmean_c": 24 + elapsed * 0.04,
                "annual_rainfall_mm": 800 - elapsed * 8,
                "days_tmax_35c_or_above": 30 + elapsed,
            })

        suggestions = climate_analysis_recommendations(
            pd.DataFrame(rows)
        )

        self.assertTrue(any("Pilot shade" in item for item in suggestions))
        self.assertTrue(any("water-efficient irrigation" in item for item in suggestions))
        self.assertTrue(any("not forecasts" in item for item in suggestions))

    def test_explains_when_history_is_too_short(self):
        recent_history = pd.DataFrame({
            "year": range(2020, 2025),
            "avg_tmean_c": [24, 24.2, 24.4, 24.6, 24.8],
            "annual_rainfall_mm": [800, 790, 780, 770, 760],
        })

        suggestions = climate_analysis_recommendations(recent_history)

        self.assertTrue(any("At least 10 annual records" in item for item in suggestions))

    def test_explains_when_annual_records_are_missing(self):
        suggestions = climate_analysis_recommendations(pd.DataFrame())

        self.assertIn(
            "Annual climate history is not available yet. Load city-level "
            "annual records before using climate-based guidance.",
            suggestions,
        )

    def test_explains_when_annual_climate_values_are_all_missing(self):
        annual_history = pd.DataFrame({
            "year": range(2001, 2011),
            "avg_tmean_c": [None] * 10,
            "annual_rainfall_mm": [None] * 10,
        })

        suggestions = climate_analysis_recommendations(annual_history)

        self.assertIn(
            "Temperature and rainfall history is incomplete, so climate "
            "trend-based suggestions cannot be calculated.",
            suggestions,
        )
        self.assertFalse(
            any("nan" in suggestion.lower() for suggestion in suggestions)
        )


if __name__ == "__main__":
    unittest.main()
