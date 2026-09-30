"""Statistical analysis.

Implements DES-AIDS-008 (REQ-AIDS-006): correlation/statistical tests
reported alongside a natural-language interpretation in the requested
response language.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy import stats as scipy_stats


@dataclass(frozen=True)
class StatResult:
    statistic: float
    p_value: float
    interpretation: str


def _interpret(r: float, p_value: float, language: str) -> str:
    strength = "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.3 else "weak"
    direction = "positive" if r >= 0 else "negative"
    if language == "ja":
        strength_ja = {"strong": "強い", "moderate": "中程度の", "weak": "弱い"}[strength]
        direction_ja = "正" if r >= 0 else "負"
        return (
            f"相関係数は {r:.4f} (p={p_value:.4g}) で、{strength_ja}{direction_ja}の相関が"
            "見られます。"
        )
    return (
        f"The correlation coefficient is {r:.4f} (p={p_value:.4g}), indicating a "
        f"{strength} {direction} correlation."
    )


# @id CODE-AIDS-006
# @implements REQ-AIDS-006
# @design DES-AIDS-008
def correlation(df: pd.DataFrame, col_a: str, col_b: str, language: str = "en") -> StatResult:
    """Compute the Pearson correlation between two columns of ``df``."""
    r, p_value = scipy_stats.pearsonr(df[col_a], df[col_b])
    return StatResult(
        statistic=float(r),
        p_value=float(p_value),
        interpretation=_interpret(float(r), float(p_value), language),
    )
