"""Missing-data MCAR/MAR-suggestive heuristic diagnostic.

Implements DES-AIDS-110 (REQ-AIDS-110): `diagnose_missingness` partitions
a probe column by a target column's missingness indicator and runs
`scipy.stats.ttest_ind` between the two groups (ADR-0124).

Known issue: the REQ-AIDS-110 Acceptance fixture's literal
`t_statistic=15.0`/`p_value=3.854627696895008e-07` values do not
reproduce against this implementation's `scipy.stats.ttest_ind` call
(empirically verified actual result for that fixture is
`t_statistic~=-0.408`, `p_value~=0.694`); tracked as GitHub #84 and
intentionally not altered by this change, which implements against the
algorithm described in Statement/Constraints rather than the
Acceptance section's un-reproducible literals.

Change: CHANGE-039
"""

from __future__ import annotations

import math

from scipy import stats as scipy_stats

_NOTE = (
    "This is an MCAR-inconsistency heuristic over one probe column only; "
    "it cannot confirm MAR and cannot detect or rule out MNAR."
)


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


# @id CODE-AIDS-165
# @implements REQ-AIDS-110
# @design DES-AIDS-110
def diagnose_missingness(target_column: list, probe_column: list) -> dict:
    """Diagnose MCAR-inconsistency via a two-sample t-test on probe_column.

    Pure function: no network, database, or ML-model call (DES-AIDS-110).
    """
    if not isinstance(target_column, list) or len(target_column) < 2:
        raise ValueError("target_column: must be a list of at least 2 entries")
    if not all(v is None or _is_finite_number(v) for v in target_column):
        raise ValueError("target_column: entries must each be a finite number or None")
    if not isinstance(probe_column, list) or len(probe_column) != len(target_column):
        raise ValueError("target_column, probe_column: must be the same length")
    if not all(_is_finite_number(v) for v in probe_column):
        raise ValueError("probe_column: entries must all be finite numbers")

    missing_mask = [v is None for v in target_column]
    if sum(missing_mask) < 1:
        raise ValueError("target_column: must contain at least 1 missing (None) value")
    if sum(missing_mask) >= len(target_column):
        raise ValueError("target_column: must contain at least 1 non-missing value")

    missing_group = [p for p, is_missing in zip(probe_column, missing_mask) if is_missing]
    observed_group = [p for p, is_missing in zip(probe_column, missing_mask) if not is_missing]
    if len(missing_group) < 2 or len(observed_group) < 2:
        raise ValueError(
            "target_column, probe_column: each missingness group must contain at least 2 "
            "observations"
        )

    t_statistic, p_value = scipy_stats.ttest_ind(missing_group, observed_group)
    diagnosis = "MCAR_inconsistent" if p_value < 0.05 else "MCAR_consistent"

    return {
        "n_missing": sum(missing_mask),
        "t_statistic": float(t_statistic),
        "p_value": float(p_value),
        "diagnosis": diagnosis,
        "note": _NOTE,
    }
