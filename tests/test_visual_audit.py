"""Tests for the visual-readability audit phase (REQ-AIDS-053)."""

import base64
import struct

import nbformat

from ai_data_scientist.notebook_audit import audit_notebook, audit_visual_outputs
from ai_data_scientist.project_manager import ensure_notebook, resolve_project


def _png(width: int, height: int, uniform: bool) -> bytes:
    """Build a minimal, syntactically valid PNG for byte-size-based testing.

    Not a fully rendered/valid raster (no real IDAT compression is
    performed); only the signature + IHDR header matter for
    ``_png_dimensions``, plus overall byte length for the near-empty
    heuristic, so a short, deterministic payload is used for "uniform" and a
    long, high-entropy payload for "non-uniform".
    """
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + b"\x00\x00\x00\x00"
    if uniform:
        payload = b"\x00" * 16
    else:
        payload = bytes((i * 37 + 11) % 256 for i in range(width * height))
    return signature + ihdr + payload


def _write(handle, notebook):
    with handle.notebook_path.open("w", encoding="utf-8") as fh:
        nbformat.write(notebook, fh)


def _add_chart_cell(notebook, png_bytes: bytes, chart_metadata: dict | None = None):
    cell = nbformat.v4.new_code_cell("render_chart(...)")
    cell["execution_count"] = 1
    encoded = base64.b64encode(png_bytes).decode("ascii")
    cell["outputs"] = [nbformat.v4.new_output("execute_result", data={"image/png": encoded})]
    if chart_metadata is not None:
        cell["metadata"]["chart"] = chart_metadata
    notebook.cells.append(cell)
    return cell


# @id TEST-AIDS-083
# @verifies REQ-AIDS-053
def test_TEST_AIDS_083_missing_glyphs_metadata_is_reported_not_readable():
    notebook = nbformat.v4.new_notebook()
    _add_chart_cell(
        notebook,
        _png(100, 100, uniform=False),
        chart_metadata={
            "missing_glyphs": [25903, 20986],
            "title": "支出",
            "xlabel": "年",
            "ylabel": "値",
            "legend": "凡例",
        },
    )

    findings = audit_visual_outputs(notebook, (0,))
    codes = {f.code for f in findings}
    assert "missing_glyphs" in codes


# @id TEST-AIDS-084
# @verifies REQ-AIDS-053
def test_TEST_AIDS_084_complete_metadata_chart_is_readable():
    notebook = nbformat.v4.new_notebook()
    _add_chart_cell(
        notebook,
        _png(100, 100, uniform=False),
        chart_metadata={
            "missing_glyphs": [],
            "title": "Expenditure",
            "xlabel": "Year",
            "ylabel": "Value",
            "legend": "Legend",
        },
    )

    findings = audit_visual_outputs(notebook, (0,))
    assert findings == ()


# @id TEST-AIDS-085
# @verifies REQ-AIDS-053
def test_TEST_AIDS_085_near_empty_image_detected_distinct_from_missing_glyphs():
    notebook = nbformat.v4.new_notebook()
    _add_chart_cell(notebook, _png(200, 200, uniform=True), chart_metadata=None)

    findings = audit_visual_outputs(notebook, (0,))
    codes = {f.code for f in findings}
    assert "near_empty_image" in codes
    assert "missing_glyphs" not in codes


# @id TEST-AIDS-086
# @verifies REQ-AIDS-053
def test_TEST_AIDS_086_audit_notebook_backward_compatible_when_visual_audit_disabled(tmp_path):
    handle = resolve_project("visual-audit-off", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_chart_cell(
        notebook,
        _png(50, 50, uniform=True),
        chart_metadata={"missing_glyphs": [1, 2]},
    )
    _write(handle, notebook)

    report_without_visual_audit = audit_notebook(handle.notebook_path)
    assert report_without_visual_audit.ok
    assert report_without_visual_audit.visual_findings == ()

    report_with_visual_audit = audit_notebook(handle.notebook_path, visual_audit=True)
    assert not report_with_visual_audit.ok
    assert len(report_with_visual_audit.visual_findings) > 0
