"""Feature engineering operations.

Implements DES-AIDS-013 (REQ-AIDS-015): applies the requested encoding,
scaling, group-wise aggregation, categorical interaction, missing-value
flagging, or explicit-edge binning transformation to a dataframe and reports
the resulting feature set.

Also implements DES-AIDS-061 (REQ-AIDS-073): a leakage-safe fit/transform
API that separates statistics estimation (``fit_features``) from
transformation application (``transform_features``), so a cross-validation
caller can fit on a training fold and transform a disjoint fold without ever
deriving statistics from the held-out rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from sklearn.preprocessing import StandardScaler

_SUPPORTED_OPERATIONS = (
    "one_hot",
    "scale",
    "aggregate",
    "interaction",
    "missing_flag",
    "bin",
)
_SUPPORTED_AGG_FUNCS = ("mean", "sum", "count_eq")


@dataclass(frozen=True)
class FeatureResult:
    dataframe: pd.DataFrame
    added_columns: list[str]
    removed_columns: list[str]
    definitions: dict = field(default_factory=dict)


# @id CODE-AIDS-093
# @implements REQ-AIDS-073
# @design DES-AIDS-061
@dataclass(frozen=True)
class FittedFeatureState:
    operation: str
    columns: tuple
    scaler: StandardScaler


def _require_params(operation: str, params: dict, required: list) -> None:
    missing = [name for name in required if name not in params or params[name] is None]
    if missing:
        raise ValueError(f"Missing required params for operation {operation!r}: {missing}")


# @id CODE-AIDS-015
# @implements REQ-AIDS-015
# @design DES-AIDS-013
def engineer_features(
    df: pd.DataFrame, operation: str, columns: list[str] | None = None, **params
) -> FeatureResult:
    """Apply ``operation`` (e.g. one-hot encoding, scaling) to ``df``."""
    if operation not in _SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported feature engineering operation: {operation!r}")

    target_columns = columns or list(df.columns)
    definitions: dict = {}

    if operation == "one_hot":
        result_df = pd.get_dummies(df, columns=target_columns)
        added_columns = [c for c in result_df.columns if c not in df.columns]
        removed_columns = [c for c in target_columns if c not in result_df.columns]
        for col in added_columns:
            definitions[col] = f"one_hot encoding of {', '.join(target_columns)}"
    elif operation == "scale":
        result_df = df.copy()
        scaler = StandardScaler()
        result_df[target_columns] = scaler.fit_transform(df[target_columns])
        added_columns = []
        removed_columns = []
    elif operation == "aggregate":
        _require_params(operation, params, ["group_col", "agg_func"])
        group_col = params["group_col"]
        agg_func = params["agg_func"]
        if agg_func not in _SUPPORTED_AGG_FUNCS:
            raise ValueError(f"Unsupported agg_func: {agg_func!r}")
        if agg_func == "count_eq":
            _require_params(operation, params, ["compare_value"])
        result_df = df.copy()
        added_columns = []
        for source_col in target_columns:
            new_col = f"{source_col}_{agg_func}_by_{group_col}"
            if agg_func == "count_eq":
                compare_value = params["compare_value"]
                result_df[new_col] = (
                    df[source_col].eq(compare_value).groupby(df[group_col]).transform("sum")
                )
            else:
                result_df[new_col] = df.groupby(group_col)[source_col].transform(agg_func)
            definitions[new_col] = f"aggregate({agg_func}) of {source_col} grouped by {group_col}"
            added_columns.append(new_col)
        removed_columns = []
    elif operation == "interaction":
        _require_params(operation, params, ["col_a", "col_b"])
        col_a = params["col_a"]
        col_b = params["col_b"]
        result_df = df.copy()
        new_col = f"{col_a}__{col_b}_interaction"
        result_df[new_col] = df[col_a].astype("string") + "__" + df[col_b].astype("string")
        definitions[new_col] = f"interaction of {col_a} and {col_b}"
        added_columns = [new_col]
        removed_columns = []
    elif operation == "missing_flag":
        result_df = df.copy()
        added_columns = []
        for col in target_columns:
            new_col = f"{col}_missing_flag"
            result_df[new_col] = df[col].isna()
            definitions[new_col] = f"missing_flag of {col}"
            added_columns.append(new_col)
        removed_columns = []
    else:  # bin
        _require_params(operation, params, ["edges"])
        edges = params["edges"]
        result_df = df.copy()
        added_columns = []
        for col in target_columns:
            new_col = f"{col}_bin"
            result_df[new_col] = pd.cut(df[col], bins=edges, right=True, include_lowest=True)
            definitions[new_col] = f"bin of {col} with edges {edges}"
            added_columns.append(new_col)
        removed_columns = []

    return FeatureResult(
        dataframe=result_df,
        added_columns=added_columns,
        removed_columns=removed_columns,
        definitions=definitions,
    )


# @id CODE-AIDS-094
# @implements REQ-AIDS-073
# @design DES-AIDS-061
def fit_features(df: pd.DataFrame, operation: str, columns: list[str]) -> FittedFeatureState:
    """Estimate statistics for ``operation`` from ``df`` only (no leakage)."""
    if operation != "scale":
        raise ValueError(f"Unsupported fit_features operation: {operation!r}")
    scaler = StandardScaler()
    scaler.fit(df[columns])
    return FittedFeatureState(operation=operation, columns=tuple(columns), scaler=scaler)


# @id CODE-AIDS-095
# @implements REQ-AIDS-073
# @design DES-AIDS-061
def transform_features(fitted_state: FittedFeatureState, df: pd.DataFrame) -> FeatureResult:
    """Apply ``fitted_state``'s already-estimated statistics to ``df``."""
    columns = list(fitted_state.columns)
    result_df = df.copy()
    result_df[columns] = fitted_state.scaler.transform(df[columns])
    return FeatureResult(dataframe=result_df, added_columns=[], removed_columns=[], definitions={})
