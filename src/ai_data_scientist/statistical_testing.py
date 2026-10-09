"""Hypothesis-testing dispatcher.

Implements DES-AIDS-108 (REQ-AIDS-108): a single `run_statistical_test`
dispatcher over 5 fixed `scipy.stats`/`statsmodels.stats.multitest`
hypothesis-testing procedures with Benjamini-Hochberg FDR correction.

Change: CHANGE-039
"""

from __future__ import annotations

import math

from scipy import stats as scipy_stats
from statsmodels.stats.multitest import multipletests

_TESTS = {"anova", "chi_square", "mann_whitney_u", "kruskal_wallis", "fdr_bh"}


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _validate_groups(groups, name: str) -> None:
    if not isinstance(groups, list) or len(groups) < 2:
        raise ValueError(f"{name}: must contain at least 2 groups")
    for group in groups:
        if (
            not isinstance(group, list)
            or len(group) < 2
            or not all(_is_finite_number(v) for v in group)
        ):
            raise ValueError(f"{name}: each group must be a list of >= 2 finite numbers")
    if all(len(set(group)) < 2 for group in groups):
        raise ValueError(f"{name}: at least one group must have non-zero variance")


def _run_anova(params: dict) -> dict:
    groups = params.get("groups")
    _validate_groups(groups, "groups")
    statistic, p_value = scipy_stats.f_oneway(*groups)
    return {"statistic": float(statistic), "p_value": float(p_value)}


def _run_chi_square(params: dict) -> dict:
    table = params.get("table")
    if not isinstance(table, list) or len(table) < 2:
        raise ValueError("table: must contain at least 2 rows")
    for row in table:
        if not isinstance(row, list) or len(row) < 2:
            raise ValueError("table: must contain at least 2 columns")
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError("table: entries must be non-negative integers")
    row_sums = [sum(row) for row in table]
    col_sums = [sum(col) for col in zip(*table)]
    if any(total <= 0 for total in row_sums) or any(total <= 0 for total in col_sums):
        raise ValueError("table: every row and column total must be > 0")
    statistic, p_value, dof, _ = scipy_stats.chi2_contingency(table, correction=False)
    return {"statistic": float(statistic), "p_value": float(p_value), "dof": int(dof)}


def _validate_sample(sample, name: str) -> None:
    if (
        not isinstance(sample, list)
        or len(sample) < 1
        or not all(_is_finite_number(v) for v in sample)
    ):
        raise ValueError(f"{name}: must be a list of >= 1 finite numbers")


def _run_mann_whitney_u(params: dict) -> dict:
    a = params.get("a")
    b = params.get("b")
    _validate_sample(a, "a")
    _validate_sample(b, "b")
    statistic, p_value = scipy_stats.mannwhitneyu(a, b, alternative="two-sided")
    return {"statistic": float(statistic), "p_value": float(p_value)}


def _run_kruskal_wallis(params: dict) -> dict:
    groups = params.get("groups")
    _validate_groups(groups, "groups")
    statistic, p_value = scipy_stats.kruskal(*groups)
    return {"statistic": float(statistic), "p_value": float(p_value)}


def _run_fdr_bh(params: dict) -> dict:
    p_values = params.get("p_values")
    if not isinstance(p_values, list) or len(p_values) < 1:
        raise ValueError("p_values: must be a list of at least 1 value")
    for value in p_values:
        if not _is_finite_number(value) or not (0 <= value <= 1):
            raise ValueError("p_values: each value must be in [0, 1]")
    rejected, corrected, _, _ = multipletests(p_values, method="fdr_bh")
    return {
        "rejected": [bool(v) for v in rejected],
        "corrected_p_values": [float(v) for v in corrected],
    }


_DISPATCH = {
    "anova": _run_anova,
    "chi_square": _run_chi_square,
    "mann_whitney_u": _run_mann_whitney_u,
    "kruskal_wallis": _run_kruskal_wallis,
    "fdr_bh": _run_fdr_bh,
}


# @id CODE-AIDS-162
# @implements REQ-AIDS-108
# @design DES-AIDS-108
def run_statistical_test(test: str, **params) -> dict:
    """Dispatch to one of 5 fixed hypothesis tests, validating params first.

    Pure function: no network, database, or ML-model call (DES-AIDS-108).
    """
    if test not in _TESTS:
        raise ValueError(
            "test: must be one of anova, chi_square, mann_whitney_u, kruskal_wallis, fdr_bh"
        )
    return _DISPATCH[test](params)
