from datetime import datetime
from html import escape
from io import BytesIO
import re

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


COLUMN_LABELS = {
    "location": "City",
    "date": "Date",
    "year": "Year",
    "month": "Month",
    "days": "Daily Records",
    "days_tmax_35c_or_above": "Days at or above 35 °C",
    "tmax_c": "Maximum Temperature (°C)",
    "tmin_c": "Minimum Temperature (°C)",
    "tmean_c": "Mean Temperature (°C)",
    "avg_tmax_c": "Average Maximum Temperature (°C)",
    "avg_tmin_c": "Average Minimum Temperature (°C)",
    "avg_tmean_c": "Average Mean Temperature (°C)",
    "mean_temperature_c": "Mean Temperature (°C)",
    "maximum_temperature_c": "Average Maximum Temperature (°C)",
    "minimum_temperature_c": "Average Minimum Temperature (°C)",
    "annual_rainfall_mm": "Annual Rainfall (mm)",
    "average_annual_rainfall_mm": "Average Annual Rainfall (mm)",
    "temperature_trend_c_per_decade": "Temperature Change (°C per Decade)",
    "rainfall_trend_mm_per_decade": "Rainfall Change (mm per Decade)",
    "rainfall_trend_percent_per_decade": "Rainfall Change (% per Decade)",
    "highest_recorded_daily_max_c": "Highest Daily Maximum (°C)",
    "highest_annual_rainfall_mm": "Highest Annual Rainfall (mm)",
    "lowest_annual_rainfall_mm": "Lowest Annual Rainfall (mm)",
    "avg_monthly_rainfall_mm": "Average Monthly Rainfall (mm)",
    "average_daily_rainfall_mm": "Average Daily Rainfall (mm)",
    "total_rainfall_mm": "Total Rainfall (mm)",
    "precipitation_mm": "Rainfall (mm)",
    "source": "Data Source",
    "quality_flag": "Record Quality",
    "years_available": "Years Available",
    "total_records": "Total Records",
    "matched_records": "Matched Daily Records",
    "heat_days": "Hot Days",
    "extreme_rainfall_days": "Heavy Rain Days",
    "hot_percentile_days": "Very Hot Days",
    "heavy_rain_percentile_days": "Very Heavy Rain Days",
    "hot_day_threshold_90_c": "Hot-Day Threshold (°C)",
    "heavy_rain_threshold_95_mm": "Heavy-Rain Threshold (mm)",
    "total_heat_days_40c_or_more": "Days at or above 40 °C",
    "total_extreme_rain_days_50mm_or_more": "Days with at least 50 mm Rain",
    "temperature_difference_c": "Temperature Difference (°C)",
    "rainfall_difference_mm": "Rainfall Difference (mm)",
    "tmax_c_nasa": "NASA POWER Maximum Temperature (°C)",
    "tmin_c_nasa": "NASA POWER Minimum Temperature (°C)",
    "tmean_c_nasa": "NASA POWER Mean Temperature (°C)",
    "precipitation_mm_nasa": "NASA POWER Rainfall (mm)",
    "tmax_c_era5": "Open-Meteo ERA5 Maximum Temperature (°C)",
    "tmin_c_era5": "Open-Meteo ERA5 Minimum Temperature (°C)",
    "tmean_c_era5": "Open-Meteo ERA5 Mean Temperature (°C)",
    "precipitation_mm_era5": "Open-Meteo ERA5 Rainfall (mm)",
    "tmax_c_difference": "Maximum Temperature Difference (°C)",
    "tmin_c_difference": "Minimum Temperature Difference (°C)",
    "tmean_c_difference": "Mean Temperature Difference (°C)",
    "temperature_mae": "Temperature Mean Absolute Difference (°C)",
    "temperature_mae_c": "Temperature Mean Absolute Difference (°C)",
    "rainfall_mae": "Rainfall Mean Absolute Difference (mm)",
    "rainfall_mae_mm": "Rainfall Mean Absolute Difference (mm)",
    "nasa_mean_temperature": "NASA POWER Mean Temperature (°C)",
    "era5_mean_temperature": "Open-Meteo ERA5 Mean Temperature (°C)",
    "nasa_total_rainfall": "NASA POWER Total Rainfall (mm)",
    "era5_total_rainfall": "Open-Meteo ERA5 Total Rainfall (mm)",
    "nasa_mean_rainfall": "NASA POWER Average Rainfall (mm)",
    "era5_mean_rainfall": "Open-Meteo ERA5 Average Rainfall (mm)",
    "roof_area_m2": "Roof Area (m²)",
    "runoff_coefficient": "Roof Runoff Assumption",
    "collection_efficiency": "Collection Efficiency Assumption",
    "estimated_harvest_litres": "Estimated Harvest (L)",
    "estimated_harvest_m3": "Estimated Harvest (m³)",
    "green_space_area_m2": "Green Space Area (m²)",
    "daily_water_requirement_litres_m2": "Daily Water Need (L/m²)",
    "irrigation_days": "Irrigation Days per Year",
    "annual_water_demand_litres": "Annual Water Demand (L)",
    "estimated_rainwater_available_litres": "Estimated Rainwater Available (L)",
    "rainwater_used_for_irrigation_litres": "Rainwater Used for Irrigation (L)",
    "additional_water_required_litres": "Additional Water Needed (L)",
    "irrigation_coverage_percentage": "Irrigation Demand Covered (%)",
    "total_roof_area_m2": "Total Roof Area (m²)",
    "cool_roof_coverage_percentage": "Cool Roof Coverage (%)",
    "cool_roof_area_m2": "Cool Roof Area (m²)",
    "conventional_roof_area_m2": "Conventional Roof Area (m²)",
    "Measure": "Measure",
    "Model MAE": "Model Mean Absolute Error",
    "Previous-day MAE baseline": "Previous-day Mean Absolute Error",
    "Model RMSE": "Model Root Mean Squared Error",
    "Previous-day RMSE baseline": "Previous-day Root Mean Squared Error",
    "Estimate date": "Estimate Date",
    "Mean temperature estimate (°C)": "Mean Temperature Estimate (°C)",
    "Rainfall estimate (mm)": "Rainfall Estimate (mm)",
    "Latest observed date": "Latest Observed Date",
}


def user_friendly_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    labels = {
        column: COLUMN_LABELS.get(
            str(column),
            str(column).replace("_", " ").strip().title(),
        )
        for column in dataframe.columns
    }
    return dataframe.rename(columns=labels)


def build_csv_report(
    title: str,
    city: str,
    tables: list[tuple[str, pd.DataFrame]],
) -> bytes:
    report_tables = []
    for section, dataframe in tables:
        if dataframe.empty:
            continue
        display_frame = user_friendly_dataframe(dataframe)
        display_frame.insert(0, "Report Section", section)
        display_frame.insert(1, "Selected City", city)
        report_tables.append(display_frame)

    if not report_tables:
        raise ValueError("There is no climate or simulation data to export.")

    combined = pd.concat(report_tables, ignore_index=True, sort=False)
    combined.insert(0, "Report", title)
    return combined.to_csv(index=False).encode("utf-8-sig")


def build_pdf_report(
    title: str,
    city: str,
    tables: list[tuple[str, pd.DataFrame]],
    notes: list[str] | None = None,
) -> bytes:
    report_tables = [
        (section, user_friendly_dataframe(dataframe))
        for section, dataframe in tables
        if not dataframe.empty
    ]
    if not report_tables:
        raise ValueError("There is no climate or simulation data to export.")

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title=title,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportSection",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#176443"),
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="ReportCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        wordWrap="CJK",
    ))
    styles.add(ParagraphStyle(
        name="ReportHeader",
        parent=styles["ReportCell"],
        fontName="Helvetica-Bold",
        textColor=colors.white,
    ))

    story = [
        Paragraph(escape(title), styles["Title"]),
        Paragraph(
            f"Selected city: {escape(city)}",
            styles["Normal"],
        ),
        Paragraph(
            f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}",
            styles["Normal"],
        ),
    ]
    story.append(Spacer(1, 0.15 * inch))

    if notes:
        story.append(Paragraph("Notes", styles["Heading2"]))
        for note in notes:
            story.append(Paragraph(
                f"• {escape(note)}",
                styles["BodyText"],
            ))
        story.append(Spacer(1, 0.12 * inch))

    for section, dataframe in report_tables:
        story.append(Paragraph(escape(section), styles["ReportSection"]))
        max_rows = 100
        visible_frame = dataframe.head(max_rows)
        table_data = [[
            Paragraph(escape(str(column)), styles["ReportHeader"])
            for column in visible_frame.columns
        ]]
        for row in visible_frame.itertuples(index=False, name=None):
            table_data.append([
                Paragraph(
                    escape("" if pd.isna(value) else str(value)),
                    styles["ReportCell"],
                )
                for value in row
            ])

        column_count = max(1, len(visible_frame.columns))
        column_width = document.width / column_count
        report_table = Table(
            table_data,
            colWidths=[column_width] * column_count,
            repeatRows=1,
            hAlign="LEFT",
        )
        report_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176443")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#eff5f1"),
            ]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d3dfd7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(report_table)

        if len(dataframe) > max_rows:
            story.append(Paragraph(
                f"Showing the first {max_rows} of {len(dataframe)} rows.",
                styles["Italic"],
            ))
        story.append(Spacer(1, 0.12 * inch))

    document.build(story)
    return buffer.getvalue()


def report_filename(title: str, city: str, extension: str) -> str:
    base_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        f"{title}_{city}".lower(),
    ).strip("_")
    return f"{base_name}.{extension}"
