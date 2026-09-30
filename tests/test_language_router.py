"""Tests for the bilingual language router (REQ-AIDS-001)."""

from ai_data_scientist.language_router import detect_language

PAIRS = [
    ("このデータを分析してください。", "ja"),
    ("Please analyze this dataset.", "en"),
    ("売上の傾向を教えて", "ja"),
    ("What is the correlation between price and sales?", "en"),
    ("欠損値を補完してください", "ja"),
    ("Clean the missing values in this column.", "en"),
    ("散布図を作成して", "ja"),
    ("Generate a histogram for the age column.", "en"),
    ("異常値を検出して", "ja"),
    ("Summarize the key insights from this notebook.", "en"),
]


# @id TEST-AIDS-001
# @verifies REQ-AIDS-001
def test_TEST_AIDS_001():
    for text, expected in PAIRS:
        assert detect_language(text) == expected
