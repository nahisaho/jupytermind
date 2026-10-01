"""Tests for the insight & evidence engine (REQ-AIDS-009/010/027)."""

import json

import nbformat
import pytest

from ai_data_scientist.insight_engine import (
    CitedValueNotFoundError,
    EvidenceMissingError,
    extract_cited_value,
    record_insight,
)
from ai_data_scientist.project_manager import ensure_notebook, resolve_project


def _seed_executed_cell(handle, execution_count, output_text):
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    cell = nbformat.v4.new_code_cell("df['corr'].mean()")
    cell["execution_count"] = execution_count
    cell["outputs"] = [
        nbformat.v4.new_output(
            "execute_result",
            data={"text/plain": output_text},
            execution_count=execution_count,
        )
    ]
    notebook.cells.append(cell)
    with handle.notebook_path.open("w", encoding="utf-8") as fh:
        nbformat.write(notebook, fh)


def _assert_insight_recorded_with_evidence(tmp_path, project_name):
    handle = resolve_project(project_name, projects_root=tmp_path)
    ensure_notebook(handle)
    _seed_executed_cell(handle, execution_count=1, output_text="0.87")

    record_insight(
        handle,
        insight_text="Price and sales show a strong positive correlation.",
        evidence_execution_count=1,
        cited_value="0.87",
        claim_type="correlation",
        language="en",
    )

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    assert len(notebook.cells) == 2
    code_cell, insight_cell = notebook.cells
    assert code_cell["execution_count"] == 1
    assert insight_cell["cell_type"] == "markdown"

    fenced = insight_cell["source"].split("```evidence\n")[1].split("\n```")[0]
    manifest = json.loads(fenced)
    assert manifest["execution_count"] == 1
    assert manifest["cited_value"] == "0.87"
    assert manifest["claim_type"] == "correlation"
    assert "0.87" in str(code_cell["outputs"][0]["data"]["text/plain"])


# @id TEST-AIDS-009
# @verifies REQ-AIDS-009
def test_TEST_AIDS_009(tmp_path):
    _assert_insight_recorded_with_evidence(tmp_path, "insight-project")


# @id TEST-AIDS-027
# @verifies REQ-AIDS-027
def test_TEST_AIDS_027(tmp_path):
    _assert_insight_recorded_with_evidence(tmp_path, "insight-project-manifest")


# @id TEST-AIDS-010
# @verifies REQ-AIDS-010
def test_TEST_AIDS_010(tmp_path):
    handle = resolve_project("no-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)

    with pytest.raises(EvidenceMissingError):
        record_insight(
            handle,
            insight_text="This claim has no evidence.",
            evidence_execution_count=99,
            cited_value="0.87",
            claim_type="correlation",
            language="ja",
        )

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    assert len(notebook.cells) == 0


# @id TEST-AIDS-047
# @verifies REQ-AIDS-039
def test_TEST_AIDS_047():
    result = {"status": "ok", "output": "kagawa_gap_vs_mean=0.62\nother=1\n"}

    cited = extract_cited_value(result, r"kagawa_gap_vs_mean=(\S+)")

    assert cited == "0.62"


# @id TEST-AIDS-048
# @verifies REQ-AIDS-039
def test_TEST_AIDS_048():
    result = {"status": "ok", "output": "unrelated=1\n"}

    with pytest.raises(CitedValueNotFoundError):
        extract_cited_value(result, r"kagawa_gap_vs_mean=(\S+)")
