import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "dashboard.py"
TEST_USERNAME = "climate-app-test-user"


def authenticated_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH)).run(timeout=90)
    app.session_state["authenticated_user_v2"] = TEST_USERNAME
    app.run(timeout=90)
    return app


class DashboardAppTests(unittest.TestCase):
    def test_public_pages_and_report_controls_render(self):
        with patch.dict(os.environ):
            os.environ.pop("CLIMATEADAPTAI_DEVELOPER_MODE", None)
            app = authenticated_app()

            public_pages = [
                "Overview",
                "Compare Cities",
                "Compare Data Sources",
                "Climate Trends & Extreme Weather",
                "Climate Predictions",
                "Adaptation Simulations",
                "Saved Scenario Results",
                "Climate Insights & Data Coverage",
            ]
            self.assertNotIn(
                "Developer: Database Information",
                app.radio[0].options,
            )

            for page in public_pages:
                with self.subTest(page=page):
                    app.radio[0].set_value(page).run(timeout=90)
                    self.assertFalse(
                        app.exception,
                        [item.message for item in app.exception],
                    )
                    expected_downloads = (
                        0 if page == "Adaptation Simulations" else 2
                    )
                    self.assertEqual(
                        len(app.download_button),
                        expected_downloads,
                    )

    def test_developer_database_page_is_opt_in(self):
        with patch.dict(
            os.environ,
            {"CLIMATEADAPTAI_DEVELOPER_MODE": "1"},
        ):
            app = authenticated_app()
            self.assertIn(
                "Developer: Database Information",
                app.radio[0].options,
            )
            app.radio[0].set_value(
                "Developer: Database Information"
            ).run(timeout=90)

            self.assertFalse(
                app.exception,
                [item.message for item in app.exception],
            )

    def test_predictions_render_for_all_cities(self):
        app = authenticated_app()
        app.radio[0].set_value("Climate Predictions").run(timeout=90)

        cities = [
            "Gujranwala, Punjab, Pakistan",
            "Gujrat, Punjab, Pakistan",
            "Islamabad, Pakistan",
            "Lahore, Punjab, Pakistan",
            "Rawalpindi, Punjab, Pakistan",
        ]
        for city in cities:
            with self.subTest(city=city):
                app.selectbox(key="research_city_selector").set_value(city)
                app.run(timeout=90)
                self.assertFalse(
                    app.exception,
                    [item.message for item in app.exception],
                )
                self.assertTrue(any(
                    "Estimate date: 2025-01-01" in str(item.value)
                    for item in app.info
                ))
                page_markdown = "\n".join(
                    str(item.value) for item in app.markdown
                )
                self.assertIn("Estimated Mean Temperature", page_markdown)
                self.assertIn("Estimated Rainfall", page_markdown)

    def test_simulations_keep_downloadable_results(self):
        app = authenticated_app()
        app.selectbox(key="research_city_selector").set_value(
            "Gujrat, Punjab, Pakistan"
        )
        app.radio[0].set_value("Adaptation Simulations").run(timeout=90)

        app.selectbox[0].set_value(2001)
        app.number_input[0].set_value(600.0)
        app.button(
            key=(
                "FormSubmitter:rainwater_form-"
                "Calculate Rainwater Harvest"
            )
        ).click().run(timeout=90)
        self.assertIn(
            "Gujrat, Punjab, Pakistan::Rainwater harvesting",
            app.session_state["simulation_reports"],
        )

        app.selectbox[1].set_value(2010)
        app.number_input[1].set_value(500.0)
        app.button(
            key=(
                "FormSubmitter:green_space_form-"
                "Run Green Space Simulation"
            )
        ).click().run(timeout=90)
        self.assertIn(
            "Gujrat, Punjab, Pakistan::Urban green space",
            app.session_state["simulation_reports"],
        )

        app.number_input[5].set_value(500.0)
        app.slider[4].set_value(100)
        app.button(
            key=(
                "FormSubmitter:cool_roof_form-"
                "Calculate Cool Roof Scenario"
            )
        ).click().run(timeout=90)
        self.assertFalse(
            app.exception,
            [item.message for item in app.exception],
        )
        self.assertIn(
            "Gujrat, Punjab, Pakistan::Cool roof",
            app.session_state["simulation_reports"],
        )
        self.assertEqual(len(app.download_button), 2)


if __name__ == "__main__":
    unittest.main()
