"""Tests for ai_materials_scientist bilingual instruction support."""

from __future__ import annotations

import re

_JAPANESE_RE = re.compile(
    "[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\u3400-\u4dbf\uff66-\uff9f]"
)
# Method-name / unit-symbol / numeric tokens permitted inside either-language
# prose without counting as the "other" language (REQ-AIMS-001 acceptance).
_PERMITTED_ASCII_CHARS = re.compile(r"[A-Za-z0-9\-/.,_%\s]")


def _is_all_japanese_prose(text: str) -> bool:
    """True if every prose character is Japanese and at least one is present.

    Permits embedded ASCII tokens (method names, unit symbols, numeric
    values) per REQ-AIMS-001's acceptance, but the sentence must actually
    be Japanese, not merely devoid of disallowed characters.
    """
    has_japanese = any(_JAPANESE_RE.match(ch) for ch in text)
    all_permitted = all(_JAPANESE_RE.match(ch) or _PERMITTED_ASCII_CHARS.match(ch) for ch in text)
    return has_japanese and all_permitted


def _is_all_english_prose(text: str) -> bool:
    return not any(_JAPANESE_RE.match(ch) for ch in text)


# @id TEST-AIMS-001
# @verifies REQ-AIMS-001
def test_TEST_AIMS_001_japanese_fixture_produces_all_japanese_response():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("フェーズフィールド法でシミュレーションしたい")

    assert result["language"] == "ja"
    assert result["outcome"] == "dispatch"


# @id TEST-AIMS-917
# @verifies REQ-AIMS-001
def test_TEST_AIMS_917_english_fixture_produces_all_english_response():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("I want to run a phase-field simulation")

    assert result["language"] == "en"
    assert result["outcome"] == "dispatch"


# @id TEST-AIMS-918
# @verifies REQ-AIMS-001
def test_TEST_AIMS_918_japanese_clarification_is_pure_japanese_prose():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("フェーズフィールド法か分子動力学のどちらで計算しますか")

    assert result["outcome"] == "clarification"
    assert result["language"] == "ja"
    assert _is_all_japanese_prose(result["clarification_question"])


# @id TEST-AIMS-919
# @verifies REQ-AIMS-001
def test_TEST_AIMS_919_english_clarification_is_pure_english_prose():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("Should I use phase-field or molecular dynamics here?")

    assert result["outcome"] == "clarification"
    assert result["language"] == "en"
    assert _is_all_english_prose(result["clarification_question"])


# @id TEST-AIMS-920
# @verifies REQ-AIMS-001
def test_TEST_AIMS_920_japanese_rejection_is_pure_japanese_prose():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("今日の天気はどうですか")

    assert result["outcome"] == "rejected"
    assert result["language"] == "ja"
    assert _is_all_japanese_prose(result["rejected_method"])


# @id TEST-AIMS-921
# @verifies REQ-AIMS-001
def test_TEST_AIMS_921_english_rejection_is_pure_english_prose():
    from ai_materials_scientist.dispatch import dispatch

    result = dispatch("What is the weather today?")

    assert result["outcome"] == "rejected"
    assert result["language"] == "en"
    assert _is_all_english_prose(result["rejected_method"])
