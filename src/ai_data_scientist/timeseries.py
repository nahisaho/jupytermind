"""Time series analysis and forecasting.

Implements DES-AIDS-016 (REQ-AIDS-018): decomposes or forecasts a requested
time series and reports trend, seasonality, or forecast values.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose

_SUPPORTED_OPERATIONS = ("decompose", "forecast")


@dataclass(frozen=True)
class TimeSeriesResult:
    trend: object
    seasonality: object
    forecast: object


# @id CODE-AIDS-018
# @implements REQ-AIDS-018
# @design DES-AIDS-016
def analyze_time_series(
    series: pd.Series,
    operation: str = "decompose",
    params: dict | None = None,
) -> TimeSeriesResult:
    """Decompose or forecast ``series`` according to ``operation``."""
    if operation not in _SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported time series operation: {operation!r}")
    params = dict(params or {})

    if operation == "decompose":
        period = params.get("period")
        decomposition = seasonal_decompose(
            series, model=params.get("model", "additive"), period=period
        )
        return TimeSeriesResult(
            trend=decomposition.trend,
            seasonality=decomposition.seasonal,
            forecast=None,
        )

    # forecast
    model = ExponentialSmoothing(
        series,
        trend=params.get("trend", "add"),
        seasonal=params.get("seasonal"),
        seasonal_periods=params.get("seasonal_periods"),
    ).fit()
    steps = params.get("steps", 1)
    forecast = model.forecast(steps)
    return TimeSeriesResult(trend=None, seasonality=None, forecast=forecast)
