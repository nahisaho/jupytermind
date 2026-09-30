"""Tests for Japanese NLP via GiNZA (REQ-AIDS-023)."""

import spacy

from ai_data_scientist.japanese_nlp import analyze_japanese_text

_REFERENCE_SENTENCE = "今日は良い天気です。"


# @id TEST-AIDS-023
# @verifies REQ-AIDS-023
def test_TEST_AIDS_023():
    result = analyze_japanese_text(_REFERENCE_SENTENCE, operation="tokenize")

    nlp = spacy.load("ja_ginza")
    doc = nlp(_REFERENCE_SENTENCE)
    reference_tokens = [tok.text for tok in doc]
    reference_pos = [tok.pos_ for tok in doc]

    assert result.tokens == reference_tokens
    assert result.pos_tags == reference_pos
