"""Insight & evidence engine.

Implements DES-AIDS-010 (REQ-AIDS-009/010/027, ADR-0003): validates that a
candidate insight is backed by an actually-executed notebook cell whose
output contains the cited value, embeds a structured evidence manifest in
the insight markdown cell, and refuses to write anything when evidence is
missing.
"""

from __future__ import annotations

import json
import re

import nbformat

from ai_data_scientist.project_manager import ProjectHandle, enqueue_write

_MANIFEST_FENCE = "```evidence\n{payload}\n```"


class EvidenceMissingError(ValueError):
    """Raised when no executed cell backs a candidate insight's evidence."""


class CitedValueNotFoundError(ValueError):
    """Raised when a cited-value pattern has no match in a result's output."""


# @id CODE-AIDS-125
# @implements REQ-AIDS-010
# @design DES-AIDS-010
class AmbiguousEvidenceError(EvidenceMissingError):
    """Raised when more than one executed cell matches the same evidence.

    GitHub #54: duplicate ``execution_count`` values (common after a kernel
    restart or appending to a notebook in a new session) can make more than
    one code cell match an insight's ``execution_count``/``cited_value``
    pair. Silently resolving to whichever cell is encountered first risks
    attributing an insight to the wrong evidence, so this is raised instead
    (a subclass of ``EvidenceMissingError`` so callers that already treat
    missing evidence as "withhold the insight" handle this the same way).
    """


# @id CODE-AIDS-047
# @implements REQ-AIDS-039
# @design DES-AIDS-027
def extract_cited_value(result: dict, pattern: str) -> str:
    """Extract the exact substring a caller should pass as ``cited_value``.

    Searches ``result["output"]`` (the dict returned by
    ``mcp_gateway.run_and_record``/``execute_cell``) for ``pattern`` and
    returns its first capture group verbatim, or the whole match when
    ``pattern`` defines no group. Raises ``CitedValueNotFoundError`` on no
    match instead of returning a guessed or empty value, so callers never
    hand-transcribe (and risk rounding/mistyping) a value for
    ``record_insight``.
    """
    output = str(result.get("output", ""))
    match = re.search(pattern, output)
    if match is None:
        raise CitedValueNotFoundError(
            f"Pattern {pattern!r} did not match the result output; "
            "no cited value could be extracted."
        )
    return match.group(1) if match.lastindex else match.group(0)


def _cell_output_contains(cell, cited_value: str) -> bool:
    for output in cell.get("outputs", []):
        for value in output.get("data", {}).values():
            if cited_value in str(value):
                return True
        # GitHub #29: execute_result/display_data outputs store their
        # payload under "data", but print()-produced stream output stores
        # it under "text" instead; a value genuinely printed by the
        # executed cell is equally valid evidence.
        if output.get("output_type") == "stream" and cited_value in str(output.get("text", "")):
            return True
    return False


def _matching_evidence_cells(notebook, execution_count: int, cited_value: str) -> list:
    """Return every code cell whose execution_count/output matches evidence."""
    return [
        cell
        for cell in notebook.cells
        if cell.get("cell_type") == "code"
        and cell.get("execution_count") == execution_count
        and _cell_output_contains(cell, cited_value)
    ]


def _find_evidence_cell(notebook, execution_count: int, cited_value: str):
    """Return the single code cell matching this evidence, or ``None``.

    GitHub #54 (CODE-AIDS-125, REQ-AIDS-010): raises
    ``AmbiguousEvidenceError`` instead of silently returning the first
    match when more than one code cell shares the same ``execution_count``
    and both produced ``cited_value`` in their output (e.g. after a kernel
    restart or appending to a notebook in a new session re-uses an
    ``execution_count``); callers must not guess which cell is the real
    evidentiary basis.
    """
    matches = _matching_evidence_cells(notebook, execution_count, cited_value)
    if len(matches) > 1:
        raise AmbiguousEvidenceError(
            f"{len(matches)} executed cells share execution_count="
            f"{execution_count!r} and an output containing {cited_value!r}; "
            "the evidentiary cell is ambiguous."
        )
    return matches[0] if matches else None


# @id CODE-AIDS-009
# @implements REQ-AIDS-009
# @design DES-AIDS-010
# @id CODE-AIDS-010
# @implements REQ-AIDS-010
# @design DES-AIDS-010
# @id CODE-AIDS-027
# @implements REQ-AIDS-027
# @design DES-AIDS-010
def record_insight(
    handle: ProjectHandle,
    insight_text: str,
    evidence_execution_count: int,
    cited_value: str,
    claim_type: str,
    language: str = "en",
) -> None:
    """Append an evidence-backed insight markdown cell, or refuse to.

    Verifies the executed evidentiary cell exists and actually produced
    ``cited_value`` before writing anything; raises ``EvidenceMissingError``
    (REQ-AIDS-010) without touching the notebook otherwise. Raises
    ``AmbiguousEvidenceError`` (a subclass of ``EvidenceMissingError``)
    instead of guessing when more than one executed cell matches the same
    ``execution_count``/``cited_value`` pair (GitHub #54).
    """
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    try:
        evidence_cell = _find_evidence_cell(notebook, evidence_execution_count, cited_value)
    except AmbiguousEvidenceError as exc:
        message = (
            f"Insight '{insight_text}' の根拠セルが一意に決まらないため記録を保留しました"
            f"(execution_count={evidence_execution_count}の実行済みセルが複数あり、"
            "いずれも該当する出力を含みます)。"
            if language == "ja"
            else (f"Withheld insight '{insight_text}': evidence is ambiguous ({exc}).")
        )
        raise AmbiguousEvidenceError(message) from exc
    if evidence_cell is None:
        message = (
            f"Insight '{insight_text}' に根拠となる実行済みセル(execution_count="
            f"{evidence_execution_count})が見つからないため記録を保留しました。"
            if language == "ja"
            else (
                f"Could not establish supporting evidence for insight "
                f"'{insight_text}' (no executed cell with execution_count="
                f"{evidence_execution_count} producing '{cited_value}'); withheld."
            )
        )
        raise EvidenceMissingError(message)

    manifest = json.dumps(
        {
            "execution_count": evidence_execution_count,
            "cited_value": cited_value,
            "claim_type": claim_type,
        },
        separators=(",", ":"),
    )
    source = f"{insight_text}\n\n{_MANIFEST_FENCE.format(payload=manifest)}"

    def add_cell(nb):
        nb.cells.append(nbformat.v4.new_markdown_cell(source))

    enqueue_write(handle, add_cell)
