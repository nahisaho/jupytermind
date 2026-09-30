"""Tests for time series analysis and forecasting (REQ-AIDS-018)."""

import numpy as np
import pandas as pd
import pytest
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from ai_data_scientist.timeseries import analyze_time_series


def _synthetic_seasonal_series():
    periods = 48
    t = np.arange(periods)
    trend = 0.5 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 12)
    values = 100 + trend + seasonal
    return pd.Series(values, index=pd.date_range("2020-01-01", periods=periods, freq="MS"))


# @id TEST-AIDS-018
# @verifies REQ-AIDS-018
def test_TEST_AIDS_018():
    series = _synthetic_seasonal_series()
    params = {"seasonal_periods": 12, "trend": "add", "seasonal": "add", "steps": 6}

    result = analyze_time_series(series, operation="forecast", params=params)

    reference_model = ExponentialSmoothing(
        series,
        trend=params["trend"],
        seasonal=params["seasonal"],
        seasonal_periods=params["seasonal_periods"],
    ).fit()
    reference_forecast = reference_model.forecast(params["steps"])

    forecast_values = pd.Series(result.forecast)
    assert len(forecast_values) == params["steps"]
    assert np.allclose(forecast_values.to_numpy(), reference_forecast.to_numpy(), rtol=0, atol=1e-6)


# @id TEST-AIDS-035
# @verifies REQ-AIDS-018
def test_TEST_AIDS_035_forecast_with_insufficient_seasonal_cycles_raises_clear_error():
    short_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    params = {"seasonal_periods": 12, "trend": "add", "seasonal": "add", "steps": 3}

    with pytest.raises(
        ValueError, match=r"requires at least 24 observations \(2 .* seasonal_periods\)"
    ):
        analyze_time_series(short_series, operation="forecast", params=params)
