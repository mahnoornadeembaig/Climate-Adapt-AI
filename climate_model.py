from dataclasses import dataclass
from datetime import date
from math import pi

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


FEATURE_COLUMNS = (
    "tmax_c",
    "tmin_c",
    "tmean_c",
    "precipitation_mm",
    "mean_temperature_7d_c",
    "rainfall_7d_mm",
    "day_of_year_sin",
    "day_of_year_cos",
)


@dataclass(frozen=True)
class RegressionMetrics:
    mae: float
    rmse: float


@dataclass(frozen=True)
class CityForecast:
    city: str
    forecast_date: date
    mean_temperature_c: float
    rainfall_mm: float
    test_days: int
    training_days: int
    temperature_metrics: RegressionMetrics
    temperature_baseline_metrics: RegressionMetrics
    rainfall_metrics: RegressionMetrics
    rainfall_baseline_metrics: RegressionMetrics
    trained_through_date: date


@dataclass(frozen=True)
class ForecastRun:
    forecasts: dict[str, CityForecast]
    unavailable_cities: dict[str, str]
    test_year: int


def _metrics(actual: pd.Series, predicted: np.ndarray) -> RegressionMetrics:
    return RegressionMetrics(
        mae=float(mean_absolute_error(actual, predicted)),
        rmse=float(np.sqrt(mean_squared_error(actual, predicted))),
    )


def _add_season_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    day_of_year = result["target_date"].dt.day_of_year
    angle = 2 * pi * (day_of_year - 1) / 365.25
    result["day_of_year_sin"] = np.sin(angle)
    result["day_of_year_cos"] = np.cos(angle)
    return result


def _prepare_daily_data(daily_data: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "date",
        "location",
        "tmean_c",
        "precipitation_mm",
    }
    missing_columns = required_columns.difference(daily_data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Climate data is missing required columns: {missing}."
        )

    frame = daily_data.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["location"] = frame["location"].astype("string").str.strip()

    for column in (
        "tmax_c",
        "tmin_c",
        "tmean_c",
        "precipitation_mm",
    ):
        if column not in frame.columns:
            frame[column] = frame["tmean_c"]
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(
        subset=[
            "date",
            "location",
            "tmax_c",
            "tmin_c",
            "tmean_c",
            "precipitation_mm",
        ]
    )
    frame = frame[frame["location"] != ""]
    frame = frame[frame["precipitation_mm"] >= 0]
    return frame.sort_values(["location", "date"]).drop_duplicates(
        subset=["location", "date"],
        keep="last",
    )


def _city_training_frame(city_data: pd.DataFrame) -> pd.DataFrame:
    frame = city_data.sort_values("date").copy().reset_index(drop=True)
    frame["mean_temperature_7d_c"] = (
        frame["tmean_c"].rolling(window=7, min_periods=7).mean()
    )
    frame["rainfall_7d_mm"] = (
        frame["precipitation_mm"].rolling(window=7, min_periods=7).sum()
    )
    frame["target_date"] = frame["date"].shift(-1)
    frame["target_temperature_c"] = frame["tmean_c"].shift(-1)
    frame["target_rainfall_mm"] = frame["precipitation_mm"].shift(-1)

    consecutive_day = frame["date"].diff().eq(pd.Timedelta(days=1))
    frame["continuous_history"] = (
        consecutive_day.rolling(window=6, min_periods=6).sum().eq(6)
    )
    frame["consecutive_target"] = frame["target_date"].eq(
        frame["date"] + pd.Timedelta(days=1)
    )
    frame = _add_season_features(frame)
    return frame


def _make_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_iter=150,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        early_stopping=False,
        random_state=42,
    )


def _forecast_one_city(
    city: str,
    city_data: pd.DataFrame,
    test_year: int,
) -> tuple[CityForecast | None, str | None]:
    latest = city_data.sort_values("date").copy().reset_index(drop=True)
    training_frame = _city_training_frame(latest)
    valid_history = (
        training_frame["continuous_history"]
        & training_frame["consecutive_target"]
    )
    examples = training_frame.loc[
        valid_history
        & training_frame[list(FEATURE_COLUMNS)].notna().all(axis=1)
    ].copy()

    training = examples[examples["target_date"].dt.year < test_year]
    testing = examples[examples["target_date"].dt.year == test_year]
    if len(training) < 365 or len(testing) < 100:
        return None, (
            f"Not enough consecutive daily data to train and test for "
            f"{test_year}."
        )

    x_train = training[list(FEATURE_COLUMNS)]
    x_test = testing[list(FEATURE_COLUMNS)]
    temperature_model = _make_model()
    rainfall_model = _make_model()

    temperature_model.fit(x_train, training["target_temperature_c"])
    rainfall_model.fit(
        x_train,
        np.log1p(training["target_rainfall_mm"]),
    )

    temperature_test_prediction = temperature_model.predict(x_test)
    rainfall_test_prediction = np.maximum(
        0,
        np.expm1(rainfall_model.predict(x_test)),
    )

    latest_features = _city_training_frame(latest).iloc[[-1]].copy()
    if not bool(latest_features.iloc[0]["continuous_history"]):
        return None, (
            "The latest records do not contain seven consecutive days "
            "needed for the next-day estimate."
        )
    latest_date = latest_features.iloc[0]["date"]
    forecast_date = latest_date + pd.Timedelta(days=1)
    latest_features["target_date"] = forecast_date
    latest_features = _add_season_features(latest_features)
    x_forecast = latest_features[list(FEATURE_COLUMNS)]

    all_examples = examples[list(FEATURE_COLUMNS)]
    final_temperature_model = _make_model()
    final_rainfall_model = _make_model()
    final_temperature_model.fit(
        all_examples,
        examples["target_temperature_c"],
    )
    final_rainfall_model.fit(
        all_examples,
        np.log1p(examples["target_rainfall_mm"]),
    )

    future_temperature = float(
        final_temperature_model.predict(x_forecast)[0]
    )
    future_rainfall = max(
        0.0,
        float(np.expm1(final_rainfall_model.predict(x_forecast)[0])),
    )

    return CityForecast(
        city=city,
        forecast_date=forecast_date.date(),
        mean_temperature_c=future_temperature,
        rainfall_mm=future_rainfall,
        test_days=len(testing),
        training_days=len(training),
        temperature_metrics=_metrics(
            testing["target_temperature_c"],
            temperature_test_prediction,
        ),
        temperature_baseline_metrics=_metrics(
            testing["target_temperature_c"],
            testing["tmean_c"].to_numpy(),
        ),
        rainfall_metrics=_metrics(
            testing["target_rainfall_mm"],
            rainfall_test_prediction,
        ),
        rainfall_baseline_metrics=_metrics(
            testing["target_rainfall_mm"],
            testing["precipitation_mm"].to_numpy(),
        ),
        trained_through_date=latest["date"].max().date(),
    ), None


def train_city_forecasts(
    daily_data: pd.DataFrame,
    test_year: int = 2024,
) -> ForecastRun:
    """Train city-specific one-day-ahead models with a chronological holdout."""
    frame = _prepare_daily_data(daily_data)
    if frame.empty:
        raise ValueError("No valid daily climate records are available.")

    forecasts = {}
    unavailable_cities = {}
    for city, city_data in frame.groupby("location", sort=True):
        forecast, reason = _forecast_one_city(
            str(city),
            city_data,
            test_year,
        )
        if forecast is None:
            unavailable_cities[str(city)] = reason or "Model unavailable."
        else:
            forecasts[str(city)] = forecast

    if not forecasts:
        reasons = "; ".join(unavailable_cities.values())
        raise ValueError(
            "No city has enough data for a reliable train/test split. "
            f"{reasons}"
        )

    return ForecastRun(
        forecasts=forecasts,
        unavailable_cities=unavailable_cities,
        test_year=test_year,
    )
