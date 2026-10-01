"""Exploratory data analysis.

Implements DES-AIDS-007 (REQ-AIDS-005): summary statistics, dtypes, and
missing-value counts matching pandas describe()/info() reference values.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class EDAReport:
    describe: dict
    dtypes: dict
    non_null_counts: dict
    missing_summary: dict
    categorical_summary: dict


DEFAULT_TOP_N = 10


# @id CODE-AIDS-005
# @implements REQ-AIDS-005
# @design DES-AIDS-007
# @id CODE-AIDS-051
# @implements REQ-AIDS-043
# @design DES-AIDS-031
def explore(df: pd.DataFrame, top_n: int = DEFAULT_TOP_N) -> EDAReport:
    """Compute summary statistics, dtypes and non-null counts for ``df``.

    Also reports, per column, a missing-value count/ratio, and, for
    categorical (object/category/bool) columns, a unique-value count and
    the ``top_n`` most frequent values with their counts and ratios
    (``truncated`` is set when more unique values exist than ``top_n``).
    The existing ``describe``/``dtypes``/``non_null_counts`` fields are
    unchanged by this extension.
    """
    describe = df.describe().to_dict() if len(df.columns) > 0 else {}
    dtypes = {column: str(dtype) for column, dtype in df.dtypes.items()}
    non_null_counts = df.count().to_dict()

    row_count = len(df)
    missing_summary = {}
    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        missing_ratio = (missing_count / row_count) if row_count else 0.0
        missing_summary[column] = {
            "missing_count": missing_count,
            "missing_ratio": missing_ratio,
        }

    categorical_summary = {}
    categorical_columns = df.select_dtypes(include=["object", "str", "category", "bool"]).columns
    for column in categorical_columns:
        value_counts = df[column].value_counts(dropna=True)
        unique_count = int(value_counts.shape[0])
        non_null_total = int(value_counts.sum())
        top_values = [
            {
                "value": value,
                "count": int(count),
                "ratio": (count / non_null_total) if non_null_total else 0.0,
            }
            for value, count in value_counts.head(top_n).items()
        ]
        categorical_summary[column] = {
            "unique_count": unique_count,
            "top_values": top_values,
            "truncated": unique_count > top_n,
        }

    return EDAReport(
        describe=describe,
        dtypes=dtypes,
        non_null_counts=non_null_counts,
        missing_summary=missing_summary,
        categorical_summary=categorical_summary,
    )
