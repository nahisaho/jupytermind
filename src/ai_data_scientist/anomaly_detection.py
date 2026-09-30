"""Anomaly / outlier detection.

Implements DES-AIDS-015 (REQ-AIDS-017): flags anomalous records in a
dataframe using the requested detection method and reports the count of
flagged records.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

_SUPPORTED_METHODS = ("zscore",)


@dataclass(frozen=True)
class AnomalyResult:
    flagged_indices: list
    method: str


# @id CODE-AIDS-017
# @implements REQ-AIDS-017
# @design DES-AIDS-015
def detect_anomalies(
    df: pd.DataFrame, column: str, method: str = "zscore", params: dict | None = None
) -> AnomalyResult:
    """Flag anomalous rows of ``df[column]`` using ``method``."""
    if method not in _SUPPORTED_METHODS:
        raise ValueError(f"Unsupported anomaly detection method: {method!r}")
    params = params or {}
    threshold = params.get("threshold", 3.0)

    series = df[column]
    z_scores = (series - series.mean()) / series.std(ddof=0)
    flagged = series.index[z_scores.abs() > threshold].tolist()

    return AnomalyResult(flagged_indices=flagged, method=method)
