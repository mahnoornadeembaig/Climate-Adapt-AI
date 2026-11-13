import pandas as pd


def climate_analysis_recommendations(
    annual_data: pd.DataFrame,
) -> list[str]:
    required_columns = {"year", "avg_tmean_c", "annual_rainfall_mm"}
    if annual_data.empty or not {"year"}.issubset(annual_data.columns):
        return [
            "Annual climate history is not available yet. Load city-level "
            "annual records before using climate-based guidance."
        ]

    frame = annual_data.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    for column in ("avg_tmean_c", "annual_rainfall_mm"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    available_columns = required_columns.intersection(frame.columns)
    if len(available_columns) == 1:
        return [
            "Temperature and rainfall history is incomplete, so climate "
            "trend-based suggestions cannot be calculated."
        ]

    frame = frame.dropna(subset=["year"])
    yearly = frame.groupby("year", as_index=False).mean(numeric_only=True)
    if len(yearly) < 10:
        return [
            "At least 10 annual records are needed for trend-based "
            "suggestions. Continue with the simulation guidance for now."
        ]

    yearly = yearly.sort_values("year")
    has_temperature_data = (
        "avg_tmean_c" in yearly.columns
        and yearly["avg_tmean_c"].notna().any()
    )
    has_rainfall_data = (
        "annual_rainfall_mm" in yearly.columns
        and yearly["annual_rainfall_mm"].notna().any()
    )
    if not has_temperature_data and not has_rainfall_data:
        return [
            "Temperature and rainfall history is incomplete, so climate "
            "trend-based suggestions cannot be calculated."
        ]

    comparison_years = min(5, len(yearly) // 2)
    early = yearly.head(comparison_years)
    recent = yearly.tail(comparison_years)
    early_period = f"{int(early['year'].min())}–{int(early['year'].max())}"
    recent_period = (
        f"{int(recent['year'].min())}–{int(recent['year'].max())}"
    )
    suggestions = []

    if has_temperature_data:
        temp_change = (
            recent["avg_tmean_c"].mean()
            - early["avg_tmean_c"].mean()
        )
        hot_day_change = None
        if "days_tmax_35c_or_above" in yearly.columns:
            hot_day_change = (
                recent["days_tmax_35c_or_above"].mean()
                - early["days_tmax_35c_or_above"].mean()
            )

        if pd.isna(temp_change):
            suggestions.append(
                "Temperature trend suggestions are unavailable because "
                "one of the comparison periods has incomplete data."
            )
        elif temp_change >= 0.5 or (
            hot_day_change is not None and hot_day_change >= 5
        ):
            suggestions.append(
                f"Mean temperature changed by {temp_change:+.1f} °C between "
                f"{early_period} and {recent_period}. Pilot shade, trees, "
                "and reflective roofs in the hottest occupied areas; "
                "measure indoor conditions before expanding."
            )
        else:
            suggestions.append(
                f"Mean temperature changed by {temp_change:+.1f} °C between "
                f"{early_period} and {recent_period}. Continue low-cost "
                "shade and ventilation measures and review the trend "
                "annually before scaling larger projects."
            )

    if has_rainfall_data:
        early_rainfall = early["annual_rainfall_mm"].mean()
        recent_rainfall = recent["annual_rainfall_mm"].mean()
        if pd.isna(early_rainfall) or pd.isna(recent_rainfall):
            suggestions.append(
                "Rainfall trend suggestions are unavailable because one "
                "of the comparison periods has incomplete data."
            )
        else:
            rainfall_change = recent_rainfall - early_rainfall
            rainfall_change_pct = (
                rainfall_change / early_rainfall * 100
                if early_rainfall > 0
                else None
            )
            if rainfall_change_pct is not None and rainfall_change_pct <= -15:
                suggestions.append(
                    f"Average annual rainfall was {abs(rainfall_change_pct):.0f}% "
                    f"lower in {recent_period} than in {early_period}. "
                    "Prioritize water-efficient irrigation and appropriately "
                    "sized rainwater storage, with a dependable supplementary "
                    "water source."
                )
            elif (
                rainfall_change_pct is not None
                and rainfall_change_pct >= 15
            ):
                suggestions.append(
                    f"Average annual rainfall was {rainfall_change_pct:.0f}% "
                    f"higher in {recent_period} than in {early_period}. "
                    "Review drainage, safe overflow routes, and rainwater "
                    "storage before increasing collection."
                )
            else:
                suggestions.append(
                    f"Average annual rainfall changed by {rainfall_change:+.0f} "
                    f"mm between {early_period} and {recent_period}. "
                    "Size rainwater storage using monthly rainfall and demand, "
                    "not annual totals alone."
                )

    suggestions.append(
        "These suggestions compare historical averages; they are "
        "transparent planning guidance, not forecasts or proof that an "
        "adaptation measure will work locally."
    )
    return suggestions


def rainwater_recommendations(harvested_litres: float) -> list[str]:
    if harvested_litres < 20_000:
        storage_advice = (
            "The estimated harvest is under 20,000 litres per year. "
            "Treat it as a supplementary supply and prioritize high-value "
            "non-potable uses."
        )
    else:
        storage_advice = (
            f"Plan covered storage and safe overflow for an estimated "
            f"{harvested_litres:,.0f} litres per year, sized around "
            "monthly demand and seasonal rainfall."
        )

    return [
        storage_advice,
        "Include first-flush diversion and filtration; do not use collected "
        "water for drinking without appropriate testing and treatment.",
    ]


def green_space_recommendations(coverage_percentage: float) -> list[str]:
    if coverage_percentage >= 100:
        coverage_advice = (
            "The estimate covers the simulated annual irrigation demand. "
            "Use storage and efficient irrigation to address dry periods; "
            "annual totals do not guarantee water is available when needed."
        )
    elif coverage_percentage >= 50:
        coverage_advice = (
            "Rainwater covers at least half of the simulated demand. "
            "Prioritize drip irrigation, mulch, and drought-tolerant plants "
            "to reduce the remaining water requirement."
        )
    else:
        coverage_advice = (
            "The estimate covers less than half of the simulated demand. "
            "Prioritize smaller, high-value green areas and arrange a "
            "reliable supplementary water source."
        )

    return [
        coverage_advice,
        "Review actual seasonal water use before expanding the irrigated "
        "area; this comparison does not account for evaporation or losses.",
    ]


def cool_roof_recommendations(
    coverage_percentage: int,
) -> list[str]:
    if coverage_percentage == 0:
        coverage_advice = (
            "No cool-roof area is selected. Consider a small pilot on "
            "sun-exposed roofs above frequently occupied rooms."
        )
    elif coverage_percentage < 50:
        coverage_advice = (
            "Prioritize the most sun-exposed roofs and occupied spaces "
            "first, then review the results before expanding coverage."
        )
    else:
        coverage_advice = (
            "Consider phased installation and regular surface maintenance "
            "across the selected area."
        )

    return [
        coverage_advice,
        "Measure indoor temperatures and energy use before and after "
        "installation; this calculator reports area only and does not "
        "predict cooling or savings.",
    ]
