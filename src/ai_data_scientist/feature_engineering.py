"""Feature engineering operations.

Implements DES-AIDS-013 (REQ-AIDS-015): applies the requested encoding,
scaling, or feature selection transformation to a dataframe and reports the
resulting feature set.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.preprocessing import StandardScaler

_SUPPORTED_OPERATIONS = ("one_hot", "scale")


@dataclass(frozen=True)
class FeatureResult:
    dataframe: pd.DataFrame
    added_columns: list
    removed_columns: list


# @id CODE-AIDS-015
# @implements REQ-AIDS-015
# @design DES-AIDS-013
def engineer_features(
    df: pd.DataFrame, operation: str, columns: list | None = None
) -> FeatureResult:
    """Apply ``operation`` (e.g. one-hot encoding, scaling) to ``df``."""
    if operation not in _SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported feature engineering operation: {operation!r}")

    target_columns = columns or list(df.columns)

    if operation == "one_hot":
        result_df = pd.get_dummies(df, columns=target_columns)
        added_columns = [c for c in result_df.columns if c not in df.columns]
        removed_columns = [c for c in target_columns if c not in result_df.columns]
    else:  # scale
        result_df = df.copy()
        scaler = StandardScaler()
        result_df[target_columns] = scaler.fit_transform(df[target_columns])
        added_columns = []
        removed_columns = []

    return FeatureResult(
        dataframe=result_df, added_columns=added_columns, removed_columns=removed_columns
    )
