"""Univariate model-drift monitoring (Population Stability Index and KS test)."""

import math

from scipy.stats import ks_2samp

_ZERO_PROPORTION_FLOOR = 0.0001


def _is_finite_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value == value
        and abs(value) != float("inf")
    )


def _validate_numeric_list(values, name: str) -> None:
    if not isinstance(values, list) or len(values) == 0:
        raise ValueError(f"{name}: must be a non-empty list of finite numbers")
    if not all(_is_finite_number(v) for v in values):
        raise ValueError(f"{name}: entries must all be finite numbers")


# @id CODE-AIDS-166
# @implements REQ-AIDS-114
# @design DES-AIDS-112
def population_stability_index(expected: list, actual: list, n_bins: int = 10) -> dict:
    """Compute the Population Stability Index between two samples over equal-width bins."""
    _validate_numeric_list(expected, "expected")
    _validate_numeric_list(actual, "actual")
    if not isinstance(n_bins, int) or isinstance(n_bins, bool):
        raise ValueError("n_bins: must be an integer")
    if n_bins < 1:
        raise ValueError("n_bins: must be >= 1")
    if len(expected) < n_bins:
        raise ValueError("expected: must contain at least n_bins entries")

    lo, hi = min(expected), max(expected)
    if hi == lo:
        raise ValueError("expected: must span a non-zero range")

    width = (hi - lo) / n_bins

    def bin_index(value: float) -> int:
        if value <= lo:
            return 0
        if value >= hi:
            return n_bins - 1
        return min(int((value - lo) / width), n_bins - 1)

    expected_counts = [0] * n_bins
    actual_counts = [0] * n_bins
    for value in expected:
        expected_counts[bin_index(value)] += 1
    for value in actual:
        actual_counts[bin_index(value)] += 1

    psi = 0.0
    for e_count, a_count in zip(expected_counts, actual_counts):
        e_proportion = e_count / len(expected) or _ZERO_PROPORTION_FLOOR
        a_proportion = a_count / len(actual) or _ZERO_PROPORTION_FLOOR
        psi += (a_proportion - e_proportion) * math.log(a_proportion / e_proportion)

    return {"psi": psi, "drift_detected": psi >= 0.2}


# @id CODE-AIDS-167
# @implements REQ-AIDS-114
# @design DES-AIDS-112
def ks_drift_test(expected: list, actual: list) -> dict:
    """Run a two-sample Kolmogorov-Smirnov drift test between two samples."""
    _validate_numeric_list(expected, "expected")
    _validate_numeric_list(actual, "actual")

    stat_result = ks_2samp(expected, actual)
    return {
        "statistic": float(stat_result.statistic),
        "p_value": float(stat_result.pvalue),
        "drift_detected": float(stat_result.pvalue) < 0.05,
    }
