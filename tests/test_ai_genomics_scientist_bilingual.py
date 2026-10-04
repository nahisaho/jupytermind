"""Tests for ai_genomics_scientist bilingual instruction support (REQ-AGENOM-001)."""

from __future__ import annotations

import re

_JAPANESE_RE = re.compile(
    "[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\u3400-\u4dbf\uff66-\uff9f]"
)
_PERMITTED_ASCII_CHARS = re.compile(r"[A-Za-z0-9`\-/.,_%\s]")


def _is_all_japanese_prose(text: str) -> bool:
    has_japanese = any(_JAPANESE_RE.match(character) for character in text)
    all_permitted = all(
        _JAPANESE_RE.match(character) or _PERMITTED_ASCII_CHARS.match(character)
        for character in text
    )
    return has_japanese and all_permitted


def _is_all_english_prose(text: str) -> bool:
    return not any(_JAPANESE_RE.match(character) for character in text)


# @id TEST-AGENOM-001
# @verifies REQ-AGENOM-001
def test_TEST_AGENOM_001_keeps_dispatch_and_prose_in_the_request_language():
    from ai_genomics_scientist.dispatch import dispatch

    japanese_requests = [
        "配列特徴量解析を実行したい",
        "バリアント効果注釈を実行したい",
        "スプライス部位強度を実行したい",
        "遺伝子セットエンリッチメントを実行したい",
        "配列アラインメントを実行したい",
    ]
    english_requests = [
        "I want to run sequence-features",
        "I want to run variant-effect-annotation",
        "I want to run splice-site-strength",
        "I want to run gene-set-enrichment",
        "I want to run pairwise-sequence-alignment",
    ]

    for request_text in japanese_requests:
        result = dispatch(request_text)
        assert result["language"] == "ja"
        assert result["outcome"] == "dispatch"
        assert result["handler_result"]["ok"] is False
        assert _is_all_japanese_prose(result["handler_result"]["constraint"])

    for request_text in english_requests:
        result = dispatch(request_text)
        assert result["language"] == "en"
        assert result["outcome"] == "dispatch"
        assert result["handler_result"]["ok"] is False
        assert _is_all_english_prose(result["handler_result"]["constraint"])

    japanese_clarification = dispatch("sequence-features と splice-site-strength のどちらですか")
    assert japanese_clarification["outcome"] == "clarification"
    assert japanese_clarification["language"] == "ja"
    assert _is_all_japanese_prose(japanese_clarification["clarification_question"])

    english_clarification = dispatch("Should I use sequence-features or splice-site-strength here?")
    assert english_clarification["outcome"] == "clarification"
    assert english_clarification["language"] == "en"
    assert _is_all_english_prose(english_clarification["clarification_question"])

    japanese_rejection = dispatch("今日の天気はどうですか")
    assert japanese_rejection["outcome"] == "rejected"
    assert japanese_rejection["language"] == "ja"
    assert _is_all_japanese_prose(japanese_rejection["rejected_method"])

    english_rejection = dispatch("What is the weather today?")
    assert english_rejection["outcome"] == "rejected"
    assert english_rejection["language"] == "en"
    assert _is_all_english_prose(english_rejection["rejected_method"])


# @id TEST-AGENOM-061
# @verifies REQ-AGENOM-001
def test_TEST_AGENOM_061_localizes_missing_parameter_guidance_in_japanese_without_bare_english_prose():
    from ai_genomics_scientist.dispatch import dispatch

    result = dispatch("遺伝子セットエンリッチメントを実行したい")

    assert result["language"] == "ja"
    assert result["outcome"] == "dispatch"
    assert result["handler_result"] == {
        "ok": False,
        "parameter": "params",
        "constraint": "`request_text` に埋め込まれた `JSON` オブジェクトとして抽出可能でなければなりません",
        "language": "ja",
    }
