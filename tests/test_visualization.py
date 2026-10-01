"""Tests for visualization generation (REQ-AIDS-007)."""

from pathlib import Path

import nbformat
import pandas as pd

from ai_data_scientist.project_manager import enqueue_write, ensure_notebook, resolve_project
from ai_data_scientist.visualization import build_image_output, render_chart


# @id TEST-AIDS-007
# @verifies REQ-AIDS-007
def test_TEST_AIDS_007(tmp_path):
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})

    png_bytes = render_chart(df, kind="scatter", x="x", y="y")
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    output = build_image_output(png_bytes)
    assert output["output_type"] == "execute_result"
    assert "image/png" in output["data"]

    handle = resolve_project("viz-project", projects_root=tmp_path)
    ensure_notebook(handle)

    def add_cell(nb):
        import nbformat

        cell = nbformat.v4.new_code_cell("render_chart(...)")
        cell["outputs"] = [output]
        nb.cells.append(cell)

    enqueue_write(handle, add_cell)

    import nbformat

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    assert "image/png" in notebook.cells[0]["outputs"][0]["data"]


# @id TEST-AIDS-039
# @verifies REQ-AIDS-007
def test_TEST_AIDS_039_record_chart_persists_output_with_execution_count(tmp_path):
    from ai_data_scientist.visualization import record_chart

    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})
    png_bytes = render_chart(df, kind="scatter", x="x", y="y")

    handle = resolve_project("chart-record-project", projects_root=tmp_path)
    ensure_notebook(handle)

    execution_count = record_chart(
        handle, "render_chart(df, kind='scatter', x='x', y='y')", png_bytes
    )

    assert execution_count == 1
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    cell = notebook.cells[0]
    assert cell["execution_count"] == 1
    assert "image/png" in cell["outputs"][0]["data"]
    assert cell["outputs"][0]["execution_count"] == 1


# @id TEST-AIDS-049
# @verifies REQ-AIDS-040
def test_TEST_AIDS_049_documents_kernel_consistency_contract():
    import inspect

    from ai_data_scientist import visualization

    doc = inspect.getdoc(visualization.record_chart) or ""
    assert "never executed against" in doc or "not executed against" in doc

    skill_path = (
        Path(__file__).resolve().parent.parent
        / ".github"
        / "skills"
        / "ai-data-scientist"
        / "SKILL.md"
    )
    skill_text = skill_path.read_text(encoding="utf-8")
    assert "never execute the stored code string against the live" in skill_text
