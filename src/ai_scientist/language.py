"""Language detection for ai_scientist responses and metadata."""

from ai_data_scientist.language_router import detect_language as _detect_language


# @id CODE-AISCI-001
# @implements REQ-AISCI-001
# @design DES-AISCI-001
# @id CODE-AISCI-010
# @implements REQ-AISCI-010
# @design DES-AISCI-007
def detect_language(text: str) -> str:
    """Reuse ai-data-scientist's deterministic language detector."""
    return _detect_language(text)
