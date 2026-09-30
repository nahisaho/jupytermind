"""Bilingual (Japanese/English) instruction language detection."""

_JAPANESE_RANGES = (
    (0x3040, 0x309F),  # Hiragana
    (0x30A0, 0x30FF),  # Katakana
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x3400, 0x4DBF),  # CJK Extension A
    (0xFF66, 0xFF9F),  # Halfwidth Katakana
)


def _is_japanese_char(ch: str) -> bool:
    code = ord(ch)
    return any(low <= code <= high for low, high in _JAPANESE_RANGES)


# @id CODE-AIDS-001
# @implements REQ-AIDS-001
# @design DES-AIDS-002
def detect_language(text: str) -> str:
    """Detect whether ``text`` is Japanese ("ja") or English ("en").

    Deterministic, offline heuristic: any Japanese-script character present
    marks the instruction as Japanese; otherwise it is treated as English.
    """
    if any(_is_japanese_char(ch) for ch in text):
        return "ja"
    return "en"
