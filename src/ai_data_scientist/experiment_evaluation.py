"""A/B testing and experiment evaluation.

Implements DES-AIDS-020 (REQ-AIDS-022): computes the statistical
significance of the observed difference between two groups and reports
the result with a bilingual markdown interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy import stats as scipy_stats

_SUPPORTED_TESTS = ("ttest",)


@dataclass(frozen=True)
class ExperimentResult:
    statistic: float
    p_value: float
    interpretation: str


def _interpret(p_value: float, language: str) -> str:
    significant = p_value < 0.05
    if language == "ja":
        verdict = "統計的に有意な差があります" if significant else "統計的に有意な差は見られません"
        return f"p値は {p_value:.4g} で、{verdict} (有意水準0.05)。"
    verdict = (
        "a statistically significant difference"
        if significant
        else "no statistically significant difference"
    )
    return f"The p-value is {p_value:.4g}, indicating {verdict} (alpha=0.05)."


# @id CODE-AIDS-022
# @implements REQ-AIDS-022
# @design DES-AIDS-020
def evaluate_experiment(
    control: pd.Series,
    treatment: pd.Series,
    test: str = "ttest",
    language: str = "en",
) -> ExperimentResult:
    """Compute the significance of the difference between ``control`` and ``treatment``."""
    if test not in _SUPPORTED_TESTS:
        raise ValueError(f"Unsupported experiment test: {test!r}")

    statistic, p_value = scipy_stats.ttest_ind(control, treatment)

    return ExperimentResult(
        statistic=float(statistic),
        p_value=float(p_value),
        interpretation=_interpret(float(p_value), language),
    )
