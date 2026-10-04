"""Statistical analysis.

Implements DES-AIDS-008 (REQ-AIDS-006): correlation/statistical tests
reported alongside a natural-language interpretation in the requested
response language.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd
from scipy import stats as scipy_stats


@dataclass(frozen=True)
class StatResult:
    statistic: float
    p_value: float
    interpretation: str


def p_display(p_value: float) -> str:
    """Format ``p_value`` for display, bounding near-zero values (DES-AIDS-053).

    Change: CHANGE-004 (REQ-AIDS-065).
    """
    if p_value < 1e-4:
        return "p < 1e-4"
    return f"p={p_value:.4g}"


# @id CODE-AIDS-087
# @implements REQ-AIDS-067
# @design DES-AIDS-055
def _interpret(
    r: float,
    p_value: float,
    language: str,
    significance_threshold: float = 0.05,
) -> str:
    if math.isnan(r) or math.isnan(p_value):
        if language == "ja":
            return "相関係数を算出できません(統計量がNaNです)。欠損値を確認してください。"
        return (
            "The correlation could not be computed (the statistic is NaN); "
            "check the input columns for missing values."
        )
    p_text = p_display(p_value)
    if p_value >= significance_threshold:
        if language == "ja":
            return f"相関係数は {r:.4f} ({p_text}) で、統計的に明確な相関は見られません。"
        return (
            f"The correlation coefficient is {r:.4f} ({p_text}), and no "
            "statistically clear correlation is observed."
        )
    strength = "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.3 else "weak"
    direction = "positive" if r >= 0 else "negative"
    if language == "ja":
        strength_ja = {"strong": "強い", "moderate": "中程度の", "weak": "弱い"}[strength]
        direction_ja = "正" if r >= 0 else "負"
        return f"相関係数は {r:.4f} ({p_text}) で、{strength_ja}{direction_ja}の相関が見られます。"
    return (
        f"The correlation coefficient is {r:.4f} ({p_text}), indicating a "
        f"{strength} {direction} correlation."
    )


# @id CODE-AIDS-006
# @implements REQ-AIDS-006 REQ-AIDS-063 REQ-AIDS-065
# @design DES-AIDS-008 DES-AIDS-051 DES-AIDS-053
def correlation(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    language: str = "en",
    significance_threshold: float = 0.05,
) -> StatResult:
    """Compute the Pearson correlation between two columns of ``df``."""
    if not 0.0 <= significance_threshold <= 1.0:
        raise ValueError("significance_threshold must be within [0.0, 1.0].")
    r, p_value = scipy_stats.pearsonr(df[col_a], df[col_b])
    return StatResult(
        statistic=float(r),
        p_value=float(p_value),
        interpretation=_interpret(float(r), float(p_value), language, significance_threshold),
    )
