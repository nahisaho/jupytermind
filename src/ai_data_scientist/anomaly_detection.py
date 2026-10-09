"""Anomaly / outlier detection.

Implements DES-AIDS-015 (REQ-AIDS-017): flags anomalous records in a
dataframe using the requested detection method and reports the count of
flagged records.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

_SUPPORTED_METHODS = ("zscore",)
_MULTIVARIATE_ANOMALY_METHODS = ("isolation_forest", "lof")


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


# @id CODE-AIDS-172
# @implements REQ-AIDS-112
# @design DES-AIDS-116
def detect_multivariate_anomalies(
    method: str, x: list[list[float]], n_neighbors: int = 20
) -> dict[str, list]:
    """Flag multivariate outliers in ``x`` using ``isolation_forest`` or ``lof``.

    Independent of, and never reads or writes, ``detect_anomalies``'s own
    ``_SUPPORTED_METHODS`` value domain.
    """
    if method not in _MULTIVARIATE_ANOMALY_METHODS:
        raise ValueError(f"Unsupported method: {method!r}")
    if method == "lof" and n_neighbors < 1:
        raise ValueError(f"n_neighbors ({n_neighbors}) must be >= 1")

    x_arr = np.asarray(x, dtype=float)

    if method == "isolation_forest":
        model = IsolationForest(n_estimators=50, random_state=42)
        labels = model.fit_predict(x_arr).tolist()
    else:  # lof
        effective_n_neighbors = min(n_neighbors, len(x_arr) - 1)
        model = LocalOutlierFactor(n_neighbors=effective_n_neighbors)
        labels = model.fit_predict(x_arr).tolist()

    is_outlier = [label == -1 for label in labels]
    return {"labels": labels, "is_outlier": is_outlier}
