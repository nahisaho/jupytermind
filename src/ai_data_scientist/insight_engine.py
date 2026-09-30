"""Insight & evidence engine.

Implements DES-AIDS-010 (REQ-AIDS-009/010/027, ADR-0003): validates that a
candidate insight is backed by an actually-executed notebook cell whose
output contains the cited value, embeds a structured evidence manifest in
the insight markdown cell, and refuses to write anything when evidence is
missing.
"""

from __future__ import annotations

import json

import nbformat

from ai_data_scientist.project_manager import ProjectHandle, enqueue_write

_MANIFEST_FENCE = "```evidence\n{payload}\n```"


class EvidenceMissingError(ValueError):
    """Raised when no executed cell backs a candidate insight's evidence."""


def _find_evidence_cell(notebook, execution_count: int, cited_value: str):
    for cell in notebook.cells:
        if cell.get("cell_type") != "code":
            continue
        if cell.get("execution_count") != execution_count:
            continue
        for output in cell.get("outputs", []):
            for value in output.get("data", {}).values():
                if cited_value in str(value):
                    return cell
    return None


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
    (REQ-AIDS-010) without touching the notebook otherwise.
    """
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    evidence_cell = _find_evidence_cell(notebook, evidence_execution_count, cited_value)
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
