"""Tests for ai_structural_biology_scientist bilingual support."""

from __future__ import annotations

import re

_JAPANESE_RE = re.compile(
    "[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\u3400-\u4dbf\uff66-\uff9f]"
)
_PERMITTED_ASCII_CHARS = re.compile(r"[A-Za-z0-9\-/.,_%\s]")


def _is_all_japanese_prose(text: str) -> bool:
    has_japanese = any(_JAPANESE_RE.match(ch) for ch in text)
    return has_japanese and all(
        _JAPANESE_RE.match(ch) or _PERMITTED_ASCII_CHARS.match(ch) for ch in text
    )


def _is_all_english_prose(text: str) -> bool:
    return not any(_JAPANESE_RE.match(ch) for ch in text)


# @id TEST-ASTRUCT-005
# @verifies REQ-ASTRUCT-001
def test_TEST_ASTRUCT_005_detects_request_language_and_keeps_clarification_and_rejection_prose_monolingual():
    from ai_structural_biology_scientist.dispatch import dispatch

    japanese_dispatch = dispatch("二次構造をヒューリスティックに評価したい")
    english_dispatch = dispatch("I want to evaluate secondary structure heuristically")
    japanese_clarification = dispatch("二次構造とコンタクトマップのどちらを使うべきですか")
    english_clarification = dispatch("Should I use secondary structure or residue contact map?")
    japanese_rejection = dispatch("今日の天気はどうですか")
    english_rejection = dispatch("What is the weather today?")

    assert japanese_dispatch["language"] == "ja"
    assert japanese_dispatch["outcome"] == "dispatch"
    assert english_dispatch["language"] == "en"
    assert english_dispatch["outcome"] == "dispatch"

    assert japanese_clarification["language"] == "ja"
    assert japanese_clarification["outcome"] == "clarification"
    assert _is_all_japanese_prose(japanese_clarification["clarification_question"])

    assert english_clarification["language"] == "en"
    assert english_clarification["outcome"] == "clarification"
    assert _is_all_english_prose(english_clarification["clarification_question"])

    assert japanese_rejection["language"] == "ja"
    assert japanese_rejection["outcome"] == "rejected"
    assert _is_all_japanese_prose(japanese_rejection["rejected_method"])

    assert english_rejection["language"] == "en"
    assert english_rejection["outcome"] == "rejected"
    assert _is_all_english_prose(english_rejection["rejected_method"])
