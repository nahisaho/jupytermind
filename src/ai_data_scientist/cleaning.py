"""Data cleaning operations.

Implements DES-AIDS-006 (REQ-AIDS-004): performs a requested cleaning
operation and reports the row/column impact.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

_SUPPORTED_OPERATIONS = ("drop_duplicates", "drop_na", "fillna")


@dataclass(frozen=True)
class CleaningReport:
    dataframe: pd.DataFrame
    rows_before: int
    rows_after: int
    rows_removed: int
    columns_affected: list


# @id CODE-AIDS-004
# @implements REQ-AIDS-004
# @design DES-AIDS-006
def clean_dataset(
    df: pd.DataFrame, operation: str, columns: list | None = None, fill_value=None
) -> CleaningReport:
    """Apply ``operation`` to ``df`` and report its row/column impact."""
    if operation not in _SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported cleaning operation: {operation!r}")

    rows_before = len(df)
    target_columns = columns or list(df.columns)

    if operation == "drop_duplicates":
        cleaned = df.drop_duplicates()
        columns_affected = list(df.columns)
    elif operation == "drop_na":
        cleaned = df.dropna(subset=target_columns)
        columns_affected = target_columns
    else:  # fillna
        cleaned = df.copy()
        cleaned[target_columns] = cleaned[target_columns].fillna(fill_value)
        columns_affected = target_columns

    rows_after = len(cleaned)
    return CleaningReport(
        dataframe=cleaned,
        rows_before=rows_before,
        rows_after=rows_after,
        rows_removed=rows_before - rows_after,
        columns_affected=columns_affected,
    )
