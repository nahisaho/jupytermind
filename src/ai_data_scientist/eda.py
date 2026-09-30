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


# @id CODE-AIDS-005
# @implements REQ-AIDS-005
# @design DES-AIDS-007
def explore(df: pd.DataFrame) -> EDAReport:
    """Compute summary statistics, dtypes and non-null counts for ``df``."""
    describe = df.describe().to_dict()
    dtypes = {column: str(dtype) for column, dtype in df.dtypes.items()}
    non_null_counts = df.count().to_dict()
    return EDAReport(describe=describe, dtypes=dtypes, non_null_counts=non_null_counts)
