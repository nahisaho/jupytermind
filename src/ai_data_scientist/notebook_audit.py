"""Read-only notebook execution/evidence audit.

Implements DES-AIDS-033 (REQ-AIDS-045): inspects a project notebook without
writing it back, reporting nbformat validity, unexecuted/error code cells,
chart outputs, and whether every insight-like markdown cell carries a
well-formed evidence manifest that resolves to a real executed cell output
(reusing insight_engine's cited-value matching rule).
"""

from __future__ import annotations

import base64
import json
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

import nbformat

from ai_data_scientist import project_manager
from ai_data_scientist.insight_engine import _find_evidence_cell

_EVIDENCE_FENCE_PATTERN = re.compile(r"```evidence\n(.*?)\n```", re.DOTALL)
_REQUIRED_MANIFEST_KEYS = {"execution_count", "cited_value", "claim_type"}
# A chart whose compressed PNG payload holds fewer than this many bytes per
# pixel is treated as suspiciously uniform/near-empty (DES-AIDS-041): a real
# rendered chart (axes, ticks, text, data) compresses far less efficiently
# than a solid-fill or all-white canvas of the same dimensions. Approximate
# by design (no imaging dependency is added for an exact pixel scan).
_NEAR_EMPTY_BYTES_PER_PIXEL_THRESHOLD = 0.02
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class NotebookAuditFinding:
    """A single audit observation tied to an optional cell index."""

    severity: str  # "error" | "warning"
    message: str
    cell_index: int | None = None


@dataclass(frozen=True)
class VisualAuditFinding:
    """A single visual-readability observation for one chart output."""

    chart_cell_index: int
    code: str  # e.g. "missing_glyphs", "near_empty_image", "missing_label"
    severity: str  # "error" | "warning"
    details: dict = field(default_factory=dict)


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
    visual_findings: tuple[VisualAuditFinding, ...] = field(default_factory=tuple)

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
    if not stripped:
        return False
    # GitHub #30: a heading-prefixed cell ("# ...") was unconditionally
    # excluded, letting malformed evidence in such cells bypass validation.
    # A cell that genuinely carries an evidence manifest is a candidate
    # regardless of a leading heading.
    if _EVIDENCE_FENCE_PATTERN.search(stripped):
        return True
    return not stripped.startswith("#")


def _png_dimensions(png_bytes: bytes) -> tuple[int, int] | None:
    """Parse (width, height) from a PNG's IHDR chunk; ``None`` if malformed."""
    if not png_bytes.startswith(_PNG_SIGNATURE) or len(png_bytes) < 24:
        return None
    width, height = struct.unpack(">II", png_bytes[16:24])
    return width, height


# @id CODE-AIDS-073
# @implements REQ-AIDS-053
# @design DES-AIDS-041
def audit_visual_outputs(
    notebook, chart_cell_indices: tuple[int, ...]
) -> tuple[VisualAuditFinding, ...]:
    """Inspect each chart cell's authoring metadata and image output.

    Reads ``cell["metadata"]["chart"]`` (written by callers such as
    ``visualization.record_chart``) for ``missing_glyphs``, ``title``,
    ``xlabel``, ``ylabel`` and ``legend``; and decodes the cell's
    ``image/png`` output to approximate whether it is suspiciously
    near-empty (DES-AIDS-041).
    """
    findings: list[VisualAuditFinding] = []
    for index in chart_cell_indices:
        cell = notebook.cells[index]
        has_image_output = any(
            output.get("data", {}).get("image/png") for output in cell.get("outputs", [])
        )
        chart_metadata = cell.get("metadata", {}).get("chart")

        # GitHub #28: a chart-bearing cell whose authoring metadata is
        # absent, empty, or not a mapping must be flagged "unaudited"
        # rather than silently treated as passing the glyph/label checks
        # below, which require a usable mapping to read from.
        if has_image_output and not (isinstance(chart_metadata, dict) and chart_metadata):
            findings.append(
                VisualAuditFinding(
                    chart_cell_index=index,
                    code="unaudited",
                    severity="warning",
                    details={},
                )
            )
        if not isinstance(chart_metadata, dict):
            chart_metadata = {}

        missing_glyphs = chart_metadata.get("missing_glyphs")
        if missing_glyphs:
            findings.append(
                VisualAuditFinding(
                    chart_cell_index=index,
                    code="missing_glyphs",
                    severity="error",
                    details={"codepoints": missing_glyphs},
                )
            )

        for label_field in ("title", "xlabel", "ylabel", "legend"):
            if chart_metadata and not chart_metadata.get(label_field):
                findings.append(
                    VisualAuditFinding(
                        chart_cell_index=index,
                        code="missing_label",
                        severity="warning",
                        details={"field": label_field},
                    )
                )

        for output in cell.get("outputs", []):
            encoded = output.get("data", {}).get("image/png")
            if not encoded:
                continue
            png_bytes = base64.b64decode(encoded)
            dimensions = _png_dimensions(png_bytes)
            if dimensions is None:
                continue
            width, height = dimensions
            pixel_count = max(width * height, 1)
            bytes_per_pixel = len(png_bytes) / pixel_count
            if bytes_per_pixel < _NEAR_EMPTY_BYTES_PER_PIXEL_THRESHOLD:
                findings.append(
                    VisualAuditFinding(
                        chart_cell_index=index,
                        code="near_empty_image",
                        severity="error",
                        details={"bytes_per_pixel": bytes_per_pixel},
                    )
                )

    return tuple(findings)


# @id CODE-AIDS-053
# @implements REQ-AIDS-045
# @design DES-AIDS-033
# @id CODE-AIDS-057
# @implements REQ-AIDS-047
# @design DES-AIDS-035
def audit_notebook(path: Path | str, visual_audit: bool = False) -> NotebookAuditReport:
    """Audit ``path`` read-only; never writes the notebook back to disk.

    When ``visual_audit`` is ``True`` (default ``False``, fully backward
    compatible), also runs ``audit_visual_outputs`` over every detected
    chart cell and appends any readability finding as an error-severity
    ``NotebookAuditFinding`` so it affects ``report.ok`` (REQ-AIDS-053).
    """
    path = Path(path)
    try:
        resolved_path = project_manager.resolve_stable_path(path)
    except project_manager.StablePathResolutionError as exc:
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
                NotebookAuditFinding("error", f"Notebook path could not be resolved: {exc}", None),
            ),
        )

    try:
        notebook = nbformat.read(str(resolved_path), as_version=4)
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

    # @id CODE-AIDS-058
    # @implements REQ-AIDS-048
    # @design DES-AIDS-036
    # Detect the one documented self-audit pattern: the notebook's own last
    # cell, still running (no execution_count yet), whose source invokes
    # audit_notebook. That cell cannot have an execution_count by definition
    # (it is the audit call itself), so it must not be flagged as a failure.
    last_index = len(notebook.cells) - 1
    self_audit_index: int | None = None
    if last_index >= 0:
        last_cell = notebook.cells[last_index]
        if (
            last_cell.get("cell_type") == "code"
            and last_cell.get("execution_count") is None
            and "audit_notebook" in last_cell.get("source", "")
        ):
            self_audit_index = last_index

    for index, cell in enumerate(notebook.cells):
        if cell.get("cell_type") != "code":
            continue
        code_cell_count += 1
        execution_count = cell.get("execution_count")
        if index == self_audit_index:
            findings.append(
                NotebookAuditFinding(
                    "warning",
                    "Trailing cell invokes audit_notebook and has not finished "
                    "executing yet; excluded from unexecuted-cell findings.",
                    index,
                )
            )
        elif execution_count is None:
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

    visual_findings: tuple[VisualAuditFinding, ...] = ()
    if visual_audit:
        visual_findings = audit_visual_outputs(notebook, tuple(chart_indices))
        for visual_finding in visual_findings:
            findings.append(
                NotebookAuditFinding(
                    visual_finding.severity,
                    f"Visual readability issue ({visual_finding.code}): {visual_finding.details}",
                    visual_finding.chart_cell_index,
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
        visual_findings=visual_findings,
    )
