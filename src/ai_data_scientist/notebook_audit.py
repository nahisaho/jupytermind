"""Read-only notebook execution/evidence audit.

Implements DES-AIDS-033 (REQ-AIDS-045): inspects a project notebook without
writing it back, reporting nbformat validity, unexecuted/error code cells,
chart outputs, and whether every insight-like markdown cell carries a
well-formed evidence manifest that resolves to a real executed cell output
(reusing insight_engine's cited-value matching rule).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import nbformat

from ai_data_scientist.insight_engine import _find_evidence_cell

_EVIDENCE_FENCE_PATTERN = re.compile(r"```evidence\n(.*?)\n```", re.DOTALL)
_REQUIRED_MANIFEST_KEYS = {"execution_count", "cited_value", "claim_type"}


@dataclass(frozen=True)
class NotebookAuditFinding:
    """A single audit observation tied to an optional cell index."""

    severity: str  # "error" | "warning"
    message: str
    cell_index: int | None = None


@dataclass(frozen=True)
class NotebookAuditReport:
    """Aggregated, read-only audit result for one notebook."""

    path: str
    nbformat_valid: bool
    code_cell_count: int
    executed_code_cell_count: int
    unexecuted_cell_indices: tuple[int, ...]
    error_cell_indices: tuple[int, ...]
    chart_cell_indices: tuple[int, ...]
    insight_cell_count: int
    findings: tuple[NotebookAuditFinding, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        """``True`` iff no error-level finding was recorded."""
        return not any(finding.severity == "error" for finding in self.findings)


def _extract_evidence_manifest(markdown_source: str) -> dict | None:
    match = _EVIDENCE_FENCE_PATTERN.search(markdown_source)
    if match is None:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _looks_like_insight_candidate(markdown_source: str) -> bool:
    stripped = markdown_source.strip()
    return bool(stripped) and not stripped.startswith("#")


# @id CODE-AIDS-053
# @implements REQ-AIDS-045
# @design DES-AIDS-033
def audit_notebook(path: Path | str) -> NotebookAuditReport:
    """Audit ``path`` read-only; never writes the notebook back to disk."""
    path = Path(path)
    try:
        notebook = nbformat.read(str(path), as_version=4)
        nbformat.validate(notebook)
    except Exception as exc:  # noqa: BLE001 - surface any parse/validate failure as a finding
        return NotebookAuditReport(
            path=str(path),
            nbformat_valid=False,
            code_cell_count=0,
            executed_code_cell_count=0,
            unexecuted_cell_indices=(),
            error_cell_indices=(),
            chart_cell_indices=(),
            insight_cell_count=0,
            findings=(
                NotebookAuditFinding("error", f"Notebook failed to parse or validate: {exc}", None),
            ),
        )

    findings: list[NotebookAuditFinding] = []
    code_cell_count = 0
    executed_code_cell_count = 0
    unexecuted_indices: list[int] = []
    error_indices: list[int] = []
    chart_indices: list[int] = []

    for index, cell in enumerate(notebook.cells):
        if cell.get("cell_type") != "code":
            continue
        code_cell_count += 1
        execution_count = cell.get("execution_count")
        if execution_count is None:
            unexecuted_indices.append(index)
            findings.append(
                NotebookAuditFinding(
                    "error", "Code cell has no execution_count (not executed).", index
                )
            )
        else:
            executed_code_cell_count += 1

        has_error = False
        has_chart = False
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                has_error = True
            data = output.get("data", {})
            if "image/png" in data:
                has_chart = True
        if has_error:
            error_indices.append(index)
            findings.append(NotebookAuditFinding("error", "Code cell has an error output.", index))
        if has_chart:
            chart_indices.append(index)

    insight_cell_count = 0
    for index, cell in enumerate(notebook.cells):
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", "")
        if not _looks_like_insight_candidate(source):
            continue

        manifest = _extract_evidence_manifest(source)
        if manifest is None:
            findings.append(
                NotebookAuditFinding(
                    "error",
                    "Markdown cell looks like an insight but has no evidence "
                    "manifest (missing ```evidence fenced JSON block).",
                    index,
                )
            )
            continue

        insight_cell_count += 1
        missing_keys = _REQUIRED_MANIFEST_KEYS - manifest.keys()
        if missing_keys:
            findings.append(
                NotebookAuditFinding(
                    "error",
                    f"Evidence manifest is missing required keys: {sorted(missing_keys)}.",
                    index,
                )
            )
            continue

        execution_count = manifest["execution_count"]
        cited_value = str(manifest["cited_value"])
        evidence_cell = _find_evidence_cell(notebook, execution_count, cited_value)
        if evidence_cell is None:
            findings.append(
                NotebookAuditFinding(
                    "error",
                    f"Evidence manifest references execution_count={execution_count!r} "
                    f"with cited_value={cited_value!r}, but no executed cell output "
                    "contains it (missing or stale evidence).",
                    index,
                )
            )

    return NotebookAuditReport(
        path=str(path),
        nbformat_valid=True,
        code_cell_count=code_cell_count,
        executed_code_cell_count=executed_code_cell_count,
        unexecuted_cell_indices=tuple(unexecuted_indices),
        error_cell_indices=tuple(error_indices),
        chart_cell_indices=tuple(chart_indices),
        insight_cell_count=insight_cell_count,
        findings=tuple(findings),
    )
