"""Japanese NLP via the pinned GiNZA (`ja_ginza`) pipeline.

Implements DES-AIDS-021 (REQ-AIDS-023, ADR-0006): runs the GiNZA Japanese
NLP pipeline on Japanese text to perform the requested operation and
reports the result.
"""

from __future__ import annotations

from dataclasses import dataclass

import spacy

_SUPPORTED_OPERATIONS = ("tokenize",)
_nlp = None  # module-level lazily-loaded ja_ginza pipeline singleton


def _get_pipeline():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("ja_ginza")
    return _nlp


@dataclass(frozen=True)
class JapaneseNLPResult:
    tokens: list
    pos_tags: list


# @id CODE-AIDS-023
# @implements REQ-AIDS-023
# @design DES-AIDS-021
def analyze_japanese_text(text: str, operation: str = "tokenize") -> JapaneseNLPResult:
    """Tokenize and POS-tag ``text`` using the pinned ja_ginza pipeline."""
    if operation not in _SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported Japanese NLP operation: {operation!r}")

    doc = _get_pipeline()(text)
    tokens = [token.text for token in doc]
    pos_tags = [token.pos_ for token in doc]

    return JapaneseNLPResult(tokens=tokens, pos_tags=pos_tags)
