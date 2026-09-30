"""Non-Japanese text analysis (e.g. sentiment).

Implements DES-AIDS-022 (REQ-AIDS-026): runs a configured non-Japanese NLP
pipeline on text to perform the requested operation and reports the
result.
"""

from __future__ import annotations

from dataclasses import dataclass

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_SUPPORTED_OPERATIONS = ("sentiment",)
_analyzer = SentimentIntensityAnalyzer()


def _label(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


@dataclass(frozen=True)
class NLPResult:
    scores: dict
    labels: list


# @id CODE-AIDS-026
# @implements REQ-AIDS-026
# @design DES-AIDS-022
def analyze_text(texts: list, operation: str = "sentiment", language: str = "en") -> NLPResult:
    """Run ``operation`` (e.g. sentiment analysis) over ``texts``."""
    if operation not in _SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported NLP operation: {operation!r}")

    scored = [_analyzer.polarity_scores(text) for text in texts]
    labels = [_label(score["compound"]) for score in scored]
    scores = {"compound": [score["compound"] for score in scored]}

    return NLPResult(scores=scores, labels=labels)
