"""Tests for ai_chemistry_scientist bilingual instruction support (REQ-ACHEM-001)."""

from __future__ import annotations

import re

_JAPANESE_RE = re.compile(
    "[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\u3400-\u4dbf\uff66-\uff9f]"
)
# Method-name / unit-symbol / numeric tokens permitted inside either-language
# prose without counting as the "other" language (REQ-ACHEM-001 acceptance).
_PERMITTED_ASCII_CHARS = re.compile(r"[A-Za-z0-9\-/.,_%\s]")


def _is_all_japanese_prose(text: str) -> bool:
    has_japanese = any(_JAPANESE_RE.match(ch) for ch in text)
    all_permitted = all(_JAPANESE_RE.match(ch) or _PERMITTED_ASCII_CHARS.match(ch) for ch in text)
    return has_japanese and all_permitted


def _is_all_english_prose(text: str) -> bool:
    return not any(_JAPANESE_RE.match(ch) for ch in text)


# @id TEST-ACHEM-001
# @verifies REQ-ACHEM-001
def test_TEST_ACHEM_001_japanese_fixture_produces_all_japanese_response():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("分子記述子を計算したい")

    assert result["language"] == "ja"
    assert result["outcome"] == "dispatch"


# @id TEST-ACHEM-930
# @verifies REQ-ACHEM-001
def test_TEST_ACHEM_930_english_fixture_produces_all_english_response():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("I want to calculate molecular descriptors")

    assert result["language"] == "en"
    assert result["outcome"] == "dispatch"


# @id TEST-ACHEM-931
# @verifies REQ-ACHEM-001
def test_TEST_ACHEM_931_japanese_clarification_is_pure_japanese_prose():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("ADMET予測かドッキングスコアのどちらで計算しますか")

    assert result["outcome"] == "clarification"
    assert result["language"] == "ja"
    assert _is_all_japanese_prose(result["clarification_question"])


# @id TEST-ACHEM-932
# @verifies REQ-ACHEM-001
def test_TEST_ACHEM_932_english_clarification_is_pure_english_prose():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("Should I use admet prediction or docking score here?")

    assert result["outcome"] == "clarification"
    assert result["language"] == "en"
    assert _is_all_english_prose(result["clarification_question"])


# @id TEST-ACHEM-933
# @verifies REQ-ACHEM-001
def test_TEST_ACHEM_933_japanese_rejection_is_pure_japanese_prose():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("今日の天気はどうですか")

    assert result["outcome"] == "rejected"
    assert result["language"] == "ja"
    assert _is_all_japanese_prose(result["rejected_method"])


# @id TEST-ACHEM-934
# @verifies REQ-ACHEM-001
def test_TEST_ACHEM_934_english_rejection_is_pure_english_prose():
    from ai_chemistry_scientist.dispatch import dispatch

    result = dispatch("What is the weather today?")

    assert result["outcome"] == "rejected"
    assert result["language"] == "en"
    assert _is_all_english_prose(result["rejected_method"])
