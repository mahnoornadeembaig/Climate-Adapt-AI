import unittest

import pandas as pd

from reporting import (
    build_csv_report,
    build_pdf_report,
    report_filename,
    user_friendly_dataframe,
)


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.tables = [
            (
                "Annual climate history",
                pd.DataFrame({
                    "location": ["Test City"],
                    "year": [2024],
                    "avg_tmean_c": [25.3],
                    "annual_rainfall_mm": [812.5],
                }),
            )
        ]

    def test_user_facing_tables_use_readable_labels(self):
        readable = user_friendly_dataframe(self.tables[0][1])

        self.assertIn("City", readable.columns)
        self.assertIn("Average Mean Temperature (°C)", readable.columns)
        self.assertIn("Annual Rainfall (mm)", readable.columns)

    def test_csv_report_includes_city_and_section_context(self):
        contents = build_csv_report(
            "Climate summary",
            "Test City",
            self.tables,
        ).decode("utf-8-sig")

        self.assertIn("Selected City", contents)
        self.assertIn("Test City", contents)
        self.assertIn("Annual climate history", contents)

    def test_pdf_report_is_a_valid_pdf_document(self):
        contents = build_pdf_report(
            "Climate summary",
            "Test City",
            self.tables,
            ["Historical climate estimates are not local station readings."],
        )

        self.assertTrue(contents.startswith(b"%PDF-"))

    def test_filename_is_safe_and_readable(self):
        self.assertEqual(
            report_filename(
                "Climate trends",
                "Lahore, Punjab, Pakistan",
                "pdf",
            ),
            "climate_trends_lahore_punjab_pakistan.pdf",
        )


if __name__ == "__main__":
    unittest.main()
