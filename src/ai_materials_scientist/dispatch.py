"""Request dispatcher for ai_materials_scientist (DES-AIMS-001)."""

from __future__ import annotations

import json
from pathlib import Path

from ai_data_scientist.language_router import detect_language as _detect_language

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = (
    REPO_ROOT / ".github" / "skills" / "ai-materials-scientist" / "manifest.json"
)


def load_manifest(manifest_path: Path | None = None) -> dict:
    """Load the static method-name-to-module manifest (DES-AIMS-001)."""
    path = manifest_path or DEFAULT_MANIFEST_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def _matched_methods(request_text: str, manifest: dict) -> list[str]:
    lowered = request_text.lower()
    matched = []
    for method, entry in manifest.items():
        names = entry.get("names", {})
        candidates = list(names.get("en", [])) + list(names.get("ja", []))
        if any(
            (candidate.lower() in lowered) if candidate.isascii() else (candidate in request_text)
            for candidate in candidates
        ):
            matched.append(method)
    return matched


# @id CODE-AIMS-001
# @implements REQ-AIMS-001 REQ-AIMS-002
# @design DES-AIMS-001
def dispatch(
    request_text: str,
    language: str | None = None,
    manifest_path: Path | None = None,
) -> dict:
    """Classify ``request_text`` and dispatch to exactly one matched module.

    ``language`` may be supplied explicitly; otherwise it is detected from
    ``request_text`` (REQ-AIMS-001) and propagated into the result so every
    downstream (module handler, clarification, rejection) path can render
    its user-facing text in that language.
    """
    if not isinstance(request_text, str):
        raise ValueError("request_text: must be a str")  # noqa: TRY004
    if language is not None and language not in ("en", "ja"):
        raise ValueError("language: must be 'en' or 'ja' when explicitly supplied")
    detected_language = language or _detect_language(request_text)
    manifest = load_manifest(manifest_path)
    matched = _matched_methods(request_text, manifest)

    if len(matched) == 1:
        return {
            "outcome": "dispatch",
            "module": matched[0],
            "language": detected_language,
            # Populated once the matched module's handler is implemented and
            # wired in (DES-AIMS-010..070); absent any handler yet, this is
            # explicitly None rather than an omitted key, per DES-AIMS-001's
            # DispatchResult {module, handler_result} contract.
            "handler_result": None,
        }
    if len(matched) > 1:
        return {
            "outcome": "clarification",
            "candidates": matched,
            "language": detected_language,
            "clarification_question": _render_clarification(matched, detected_language),
        }
    return {
        "outcome": "rejected",
        "language": detected_language,
        "rejected_method": _render_rejection(detected_language),
    }


def _render_clarification(candidates: list[str], language: str) -> str:
    """Render a single-sentence clarification question in ``language``.

    Method names (e.g. ``phase-field``) are the only permitted non-``language``
    tokens, per REQ-AIMS-001's acceptance.
    """
    names = "、".join(candidates) if language == "ja" else ", ".join(candidates)
    if language == "ja":
        return f"{names} のどちらを意図していますか。明確にしてください。"
    return f"Did you mean {names}? Please clarify which method you want."


def _render_rejection(language: str) -> str:
    """Render a single-sentence rejection message in ``language``."""
    if language == "ja":
        return "対応するシミュレーション手法が要求から認識されませんでした。"
    return "No supported simulation method was recognized in your request."
