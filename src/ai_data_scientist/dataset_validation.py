"""Independent-dataset overlap comparison (narrowed scope).

Implements DES-AIDS-045 (REQ-AIDS-057). Per the approved design, this
module operates only on already-loaded dataframes: ``compare_datasets``
checks key overlap and per-column value agreement between a primary
dataset and a candidate independent dataset. Automated dataset
*discovery* (e.g. searching Kaggle or other catalogs) is explicitly
out of scope for this repository and is not implemented here; callers
are expected to load the candidate dataset themselves before calling
this function.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

_VALID_RELATIONSHIPS = frozenset({"unknown", "independent", "derived", "overlapping"})


# @id CODE-AIDS-081
# @implements REQ-AIDS-057
# @design DES-AIDS-045
@dataclass(frozen=True)
class ColumnComparison:
    """Agreement statistics for one mapped column pair."""

    primary_column: str
    candidate_column: str
    matched_rows: int
    mismatched_rows: int
    agreement_rate: float | None


@dataclass(frozen=True)
class DatasetComparisonReport:
    """Outcome of comparing a primary dataset against a candidate dataset."""

    candidate_relationship: str
    matched_keys: int
    primary_only_keys: int
    candidate_only_keys: int
    column_comparisons: tuple[ColumnComparison, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.candidate_relationship not in _VALID_RELATIONSHIPS:
            raise ValueError(
                f"candidate_relationship must be one of {sorted(_VALID_RELATIONSHIPS)}, "
                f"got {self.candidate_relationship!r}."
            )


# @id CODE-AIDS-082
# @implements REQ-AIDS-057 REQ-AIDS-062
# @design DES-AIDS-045 DES-AIDS-050
def compare_datasets(
    primary: pd.DataFrame,
    candidate: pd.DataFrame,
    key_mapping: dict[str, str],
    value_mapping: dict[str, str],
    candidate_relationship: str = "unknown",
) -> DatasetComparisonReport:
    """Compare ``primary`` against an independent ``candidate`` dataset.

    ``key_mapping`` maps primary key column name(s) -> candidate column
    name(s), used to join the two datasets. ``value_mapping`` maps
    primary value column name -> candidate value column name for
    per-column agreement checks on the joined rows.

    Rows whose key is null on either side are excluded from
    ``matched_keys``/``primary_only_keys``/``candidate_only_keys`` and from
    the per-column agreement computation (REQ-AIDS-062): otherwise two
    null keys (e.g. both ``None``) would incorrectly count as a matched key
    pair under Python tuple-set equality.
    """
    primary_keys = list(key_mapping.keys())
    candidate_keys = list(key_mapping.values())

    eligible_primary = primary.dropna(subset=primary_keys)
    eligible_candidate = candidate.dropna(subset=candidate_keys)

    primary_key_values = set(
        map(tuple, eligible_primary[primary_keys].itertuples(index=False, name=None))
    )
    candidate_key_values = set(
        map(tuple, eligible_candidate[candidate_keys].itertuples(index=False, name=None))
    )

    matched_keys = primary_key_values & candidate_key_values
    primary_only_keys = primary_key_values - candidate_key_values
    candidate_only_keys = candidate_key_values - primary_key_values

    merged = eligible_primary.merge(
        eligible_candidate,
        left_on=primary_keys,
        right_on=candidate_keys,
        how="inner",
        suffixes=("_primary", "_candidate"),
    )

    column_comparisons: list[ColumnComparison] = []
    for primary_column, candidate_column in value_mapping.items():
        primary_col_name = (
            f"{primary_column}_primary" if primary_column in candidate.columns else primary_column
        )
        candidate_col_name = (
            f"{candidate_column}_candidate"
            if candidate_column in primary.columns
            else candidate_column
        )
        if primary_col_name not in merged.columns or candidate_col_name not in merged.columns:
            continue
        matches = merged[primary_col_name] == merged[candidate_col_name]
        matched_rows = int(matches.sum())
        mismatched_rows = int((~matches).sum())
        total = matched_rows + mismatched_rows
        agreement_rate = (matched_rows / total) if total else None
        column_comparisons.append(
            ColumnComparison(
                primary_column=primary_column,
                candidate_column=candidate_column,
                matched_rows=matched_rows,
                mismatched_rows=mismatched_rows,
                agreement_rate=agreement_rate,
            )
        )

    return DatasetComparisonReport(
        candidate_relationship=candidate_relationship,
        matched_keys=len(matched_keys),
        primary_only_keys=len(primary_only_keys),
        candidate_only_keys=len(candidate_only_keys),
        column_comparisons=tuple(column_comparisons),
    )
