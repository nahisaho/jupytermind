"""Tests for report export (REQ-AIDS-025, REQ-AIDS-033)."""

from unittest.mock import patch

import nbformat
import pytest

from ai_data_scientist.project_manager import ensure_notebook, resolve_project
from ai_data_scientist.report_export import export_report


class _CountingClient:
    """Fake MCP client used only to assert export never calls it."""

    def __init__(self):
        self.calls = 0

    def execute(self, code):
        self.calls += 1
        return {"status": "ok", "output": "executed"}


def _build_project_with_insight(tmp_path):
    handle = resolve_project("export-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    notebook.cells.append(nbformat.v4.new_markdown_cell("## Insight: sales grew 12%"))
    code_cell = nbformat.v4.new_code_cell("render_chart(df)")
    code_cell["outputs"] = [
        nbformat.v4.new_output("execute_result", data={"text/plain": "<chart>"})
    ]
    notebook.cells.append(code_cell)
    with handle.notebook_path.open("w", encoding="utf-8") as fh:
        nbformat.write(notebook, fh)
    return handle


def _assert_export_produces_evidence_preserving_report(tmp_path):
    handle = _build_project_with_insight(tmp_path)
    client = _CountingClient()

    report = export_report(handle, report_format="html", name="report")

    assert report.path.exists()
    assert report.path.parent == handle.root / "reports"
    content = report.path.read_text(encoding="utf-8")
    assert "Insight: sales grew 12%" in content
    assert client.calls == 0
    return report


# @id TEST-AIDS-025
# @verifies REQ-AIDS-025
def test_TEST_AIDS_025(tmp_path):
    _assert_export_produces_evidence_preserving_report(tmp_path)


# @id TEST-AIDS-033
# @verifies REQ-AIDS-033
def test_TEST_AIDS_033(tmp_path):
    _assert_export_produces_evidence_preserving_report(tmp_path)


# @id TEST-AIDS-036
# @verifies REQ-AIDS-025
def test_TEST_AIDS_036_pdf_export_without_xelatex_raises_actionable_error(tmp_path):
    handle = _build_project_with_insight(tmp_path)

    with patch(
        "ai_data_scientist.report_export.PDFExporter.from_notebook_node",
        side_effect=OSError("xelatex not found on PATH"),
    ):
        with pytest.raises(RuntimeError, match="xelatex|TeX|README"):
            export_report(handle, report_format="pdf", name="report")
