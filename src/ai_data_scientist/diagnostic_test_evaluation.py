"""Diagnostic test performance evaluation (DES-AIDS-105 / REQ-AIDS-105).

Pure function module: no network, database, or ML-model call.
"""

from __future__ import annotations

import math


def _is_non_negative_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


# @id CODE-AIDS-159
# @implements REQ-AIDS-105
# @design DES-AIDS-105
def evaluate_diagnostic_test(
    true_positive: int, false_negative: int, false_positive: int, true_negative: int
) -> dict[str, float]:
    """Compute standard 2x2-confusion-matrix diagnostic-accuracy metrics."""
    for name, value in (
        ("true_positive", true_positive),
        ("false_negative", false_negative),
        ("false_positive", false_positive),
        ("true_negative", true_negative),
    ):
        if not _is_non_negative_int(value):
            raise ValueError(f"{name}: must be a non-negative int")

    if (true_positive + false_negative) == 0:
        raise ValueError("true_positive, false_negative: must not both be zero")
    if (false_positive + true_negative) == 0:
        raise ValueError("false_positive, true_negative: must not both be zero")
    if (true_positive + false_positive) == 0:
        raise ValueError("true_positive, false_positive: must not both be zero")
    if (true_negative + false_negative) == 0:
        raise ValueError("true_negative, false_negative: must not both be zero")

    sensitivity = true_positive / (true_positive + false_negative)
    specificity = true_negative / (true_negative + false_positive)
    ppv = true_positive / (true_positive + false_positive)
    npv = true_negative / (true_negative + false_negative)
    positive_likelihood_ratio = math.inf if specificity == 1 else sensitivity / (1 - specificity)
    negative_likelihood_ratio = math.inf if specificity == 0 else (1 - sensitivity) / specificity
    youden_j = sensitivity + specificity - 1

    return {
        "sensitivity": sensitivity,
        "specificity": specificity,
        "ppv": ppv,
        "npv": npv,
        "positive_likelihood_ratio": positive_likelihood_ratio,
        "negative_likelihood_ratio": negative_likelihood_ratio,
        "youden_j": youden_j,
    }
