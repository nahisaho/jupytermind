"""Semantic data-quality checks: schema-driven anomaly detection and
independent-dataset overlap validation.

Implements DES-AIDS-043 (REQ-AIDS-055). This module is deliberately
separate from ``anomaly_detection`` (which performs statistical
z-score outlier detection on a single numeric column); here, anomalies
are semantic constraint violations defined by a declarative schema
(ranges, allowed categories, non-null, uniqueness), and overlap
validation cross-checks summary statistics between a primary dataset
and an independent reference.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


# @id CODE-AIDS-076
# @implements REQ-AIDS-055
# @design DES-AIDS-043
@dataclass(frozen=True)
class AnomalyRecord:
    """A single schema-constraint violation."""

    column: str
    rule: str
    row_count: int
    message: str
    row_indices: tuple[int, ...] = ()


# @id CODE-AIDS-077
# @implements REQ-AIDS-055
# @design DES-AIDS-043
def detect_anomalies(df: pd.DataFrame, schema: dict) -> tuple[AnomalyRecord, ...]:
    """Detect semantic constraint violations declared by ``schema``.

    ``schema`` maps column name -> a dict of constraints, any of:
      - ``"min"`` / ``"max"``: numeric range bounds (inclusive).
      - ``"allowed"``: iterable of permitted categorical values.
      - ``"not_null"``: bool, require no missing values.
      - ``"unique"``: bool, require no duplicate values.
    Unknown columns in ``schema`` that are absent from ``df`` are skipped.
    """
    records: list[AnomalyRecord] = []
    for column, rules in schema.items():
        if column not in df.columns:
            continue
        series = df[column]

        if rules.get("not_null"):
            missing = series.isna()
            if missing.any():
                records.append(
                    AnomalyRecord(
                        column=column,
                        rule="not_null",
                        row_count=int(missing.sum()),
                        message=f"Column {column!r} has {int(missing.sum())} null value(s).",
                        row_indices=tuple(series.index[missing]),
                    )
                )

        if "min" in rules or "max" in rules:
            numeric = pd.to_numeric(series, errors="coerce")
            below = (
                numeric < rules["min"] if "min" in rules else pd.Series(False, index=series.index)
            )
            above = (
                numeric > rules["max"] if "max" in rules else pd.Series(False, index=series.index)
            )
            out_of_range = (below | above) & numeric.notna()
            if out_of_range.any():
                records.append(
                    AnomalyRecord(
                        column=column,
                        rule="range",
                        row_count=int(out_of_range.sum()),
                        message=(
                            f"Column {column!r} has {int(out_of_range.sum())} value(s) "
                            f"outside [{rules.get('min')}, {rules.get('max')}]."
                        ),
                        row_indices=tuple(series.index[out_of_range]),
                    )
                )

        if "allowed" in rules:
            allowed = set(rules["allowed"])
            disallowed = ~series.isin(allowed) & series.notna()
            if disallowed.any():
                records.append(
                    AnomalyRecord(
                        column=column,
                        rule="allowed_values",
                        row_count=int(disallowed.sum()),
                        message=(
                            f"Column {column!r} has {int(disallowed.sum())} value(s) "
                            f"not in the allowed set."
                        ),
                        row_indices=tuple(series.index[disallowed]),
                    )
                )

        if rules.get("unique"):
            duplicated = series.duplicated(keep=False) & series.notna()
            if duplicated.any():
                records.append(
                    AnomalyRecord(
                        column=column,
                        rule="unique",
                        row_count=int(duplicated.sum()),
                        message=f"Column {column!r} has {int(duplicated.sum())} duplicate value(s).",
                        row_indices=tuple(series.index[duplicated]),
                    )
                )

    return tuple(records)


# @id CODE-AIDS-078
# @implements REQ-AIDS-055
# @design DES-AIDS-043
@dataclass(frozen=True)
class OverlapMismatch:
    """A single column whose summary statistic disagrees between datasets."""

    column: str
    primary_value: float
    reference_value: float
    relative_difference: float


def validate_anomalies(
    primary: pd.DataFrame,
    reference: pd.DataFrame,
    columns: list[str],
    tolerance: float = 0.1,
) -> tuple[OverlapMismatch, ...]:
    """Compare per-column means between an independent ``reference`` dataset
    and ``primary``, flagging columns whose relative difference exceeds
    ``tolerance``. Used to validate that detected anomalies are not an
    artifact of a single dataset.
    """
    mismatches: list[OverlapMismatch] = []
    for column in columns:
        if column not in primary.columns or column not in reference.columns:
            continue
        primary_mean = float(pd.to_numeric(primary[column], errors="coerce").mean())
        reference_mean = float(pd.to_numeric(reference[column], errors="coerce").mean())
        if reference_mean == 0:
            continue
        relative_difference = abs(primary_mean - reference_mean) / abs(reference_mean)
        if relative_difference > tolerance:
            mismatches.append(
                OverlapMismatch(
                    column=column,
                    primary_value=primary_mean,
                    reference_value=reference_mean,
                    relative_difference=relative_difference,
                )
            )
    return tuple(mismatches)
