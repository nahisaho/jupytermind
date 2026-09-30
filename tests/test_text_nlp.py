"""Tests for non-Japanese text analysis / sentiment (REQ-AIDS-026)."""

from ai_data_scientist.text_nlp import analyze_text

_LABELED_SAMPLE = [
    ("I absolutely love this product, it works great!", "positive"),
    ("This is the worst experience I have ever had.", "negative"),
    ("What a wonderful and delightful surprise.", "positive"),
    ("I am so disappointed and frustrated with this service.", "negative"),
    ("This is fantastic, thank you so much!", "positive"),
    ("Terrible quality, I want a refund immediately.", "negative"),
    ("Best purchase I've made all year, highly recommend.", "positive"),
    ("Awful, broken, and a complete waste of money.", "negative"),
    ("I am happy and satisfied with the results.", "positive"),
    ("I hate how buggy and unreliable this is.", "negative"),
]


# @id TEST-AIDS-026
# @verifies REQ-AIDS-026
def test_TEST_AIDS_026():
    texts = [text for text, _ in _LABELED_SAMPLE]
    expected_labels = [label for _, label in _LABELED_SAMPLE]

    result = analyze_text(texts, operation="sentiment", language="en")

    matches = sum(
        1 for predicted, expected in zip(result.labels, expected_labels) if predicted == expected
    )
    assert matches / len(expected_labels) >= 0.8
