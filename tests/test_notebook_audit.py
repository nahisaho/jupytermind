"""Tests for the read-only notebook audit (REQ-AIDS-045)."""

import json

import nbformat

from ai_data_scientist.insight_engine import record_insight
from ai_data_scientist.notebook_audit import audit_notebook
from ai_data_scientist.project_manager import ensure_notebook, resolve_project


def _add_code_cell(notebook, execution_count=None, outputs=None):
    cell = nbformat.v4.new_code_cell("1 + 1")
    cell["execution_count"] = execution_count
    cell["outputs"] = outputs or []
    notebook.cells.append(cell)
    return cell


def _write(handle, notebook):
    with handle.notebook_path.open("w", encoding="utf-8") as fh:
        nbformat.write(notebook, fh)


# @id TEST-AIDS-059
# @verifies REQ-AIDS-045
def test_TEST_AIDS_059_well_formed_notebook_passes(tmp_path):
    handle = resolve_project("audit-ok-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.87"}, execution_count=1)
        ],
    )
    _write(handle, notebook)

    record_insight(
        handle,
        insight_text="X and Y show a strong positive correlation.",
        evidence_execution_count=1,
        cited_value="0.87",
        claim_type="correlation",
        language="en",
    )

    report = audit_notebook(handle.notebook_path)

    assert report.nbformat_valid is True
    assert report.ok is True
    assert report.code_cell_count == 1
    assert report.executed_code_cell_count == 1
    assert report.unexecuted_cell_indices == ()
    assert report.error_cell_indices == ()
    assert report.insight_cell_count == 1
    before = handle.notebook_path.read_bytes()
    audit_notebook(handle.notebook_path)
    after = handle.notebook_path.read_bytes()
    assert before == after


# @id TEST-AIDS-060
# @verifies REQ-AIDS-045
def test_TEST_AIDS_060_detects_unexecuted_error_and_chart_cells(tmp_path):
    handle = resolve_project("audit-mixed-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(notebook, execution_count=None)  # unexecuted
    _add_code_cell(
        notebook,
        execution_count=2,
        outputs=[nbformat.v4.new_output("error", ename="ValueError", evalue="boom")],
    )
    _add_code_cell(
        notebook,
        execution_count=3,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"image/png": "Zm9v"}, execution_count=3)
        ],
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    assert report.unexecuted_cell_indices == (0,)
    assert report.error_cell_indices == (1,)
    assert report.chart_cell_indices == (2,)


# @id TEST-AIDS-061
# @verifies REQ-AIDS-045
def test_TEST_AIDS_061_detects_missing_and_stale_evidence_manifest(tmp_path):
    handle = resolve_project("audit-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.42"}, execution_count=1)
        ],
    )
    # Narrative insight with no evidence manifest at all.
    notebook.cells.append(nbformat.v4.new_markdown_cell("The correlation is weak but notable."))
    # Insight with a manifest whose cited_value no longer exists in any output.
    stale_manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.99", "claim_type": "correlation"},
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(f"Stale claim.\n\n```evidence\n{stale_manifest}\n```")
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    messages = [finding.message for finding in report.findings]
    assert any("no evidence manifest" in message for message in messages)
    assert any("missing or stale evidence" in message for message in messages)
    missing_finding = next(f for f in report.findings if "no evidence manifest" in f.message)
    assert missing_finding.cell_index == 1
    stale_finding = next(f for f in report.findings if "missing or stale evidence" in f.message)
    assert stale_finding.cell_index == 2


# @id TEST-AIDS-062
# @verifies REQ-AIDS-045
def test_TEST_AIDS_062_invalid_notebook_file_is_reported_not_raised(tmp_path):
    bad_path = tmp_path / "not-a-notebook.ipynb"
    bad_path.write_text("{not valid json", encoding="utf-8")

    report = audit_notebook(bad_path)

    assert report.nbformat_valid is False
    assert report.ok is False
    assert any("failed to parse" in f.message.lower() for f in report.findings)


# @id TEST-AIDS-063
# @verifies REQ-AIDS-045
def test_TEST_AIDS_063_empty_notebook_is_well_formed_and_passes(tmp_path):
    handle = resolve_project("audit-empty-project", projects_root=tmp_path)
    ensure_notebook(handle)

    report = audit_notebook(handle.notebook_path)

    assert report.nbformat_valid is True
    assert report.ok is True
    assert report.code_cell_count == 0
    assert report.insight_cell_count == 0


# @id TEST-AIDS-066
# @verifies REQ-AIDS-047
def test_TEST_AIDS_066_resolves_relative_path_against_stable_workspace_root(tmp_path, monkeypatch):
    from ai_data_scientist import project_manager

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    monkeypatch.setattr(project_manager, "_IMPORT_TIME_CWD", workspace_root)
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)
    monkeypatch.chdir(workspace_root)

    handle = project_manager.resolve_project("audit-path-project")
    project_manager.ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(notebook, execution_count=1)
    _write(handle, notebook)

    relative_path = "projects/audit-path-project/notebooks/audit-path-project.ipynb"
    report_from_root = audit_notebook(relative_path)
    assert report_from_root.nbformat_valid is True

    monkeypatch.chdir(handle.notebook_path.parent)
    report_from_subdir = audit_notebook(relative_path)
    assert report_from_subdir.nbformat_valid is True
    assert report_from_subdir.ok == report_from_root.ok


# @id TEST-AIDS-067
# @verifies REQ-AIDS-047
def test_TEST_AIDS_067_unresolvable_path_reports_distinct_finding(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report = audit_notebook("does/not/exist.ipynb")

    assert report.nbformat_valid is False
    assert report.ok is False
    assert any("could not be resolved" in f.message.lower() for f in report.findings)
    assert not any("failed to parse" in f.message.lower() for f in report.findings)


# @id TEST-AIDS-068
# @verifies REQ-AIDS-048
def test_TEST_AIDS_068_trailing_self_audit_cell_excluded_from_failures(tmp_path):
    handle = resolve_project("audit-self-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(notebook, execution_count=1)
    self_audit_cell = nbformat.v4.new_code_cell(
        "from ai_data_scientist.notebook_audit import audit_notebook\n"
        "report = audit_notebook(NB_PATH)\nprint(report.ok)"
    )
    notebook.cells.append(self_audit_cell)
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is True
    assert report.unexecuted_cell_indices == ()
    assert any(
        f.severity == "warning" and "excluded from unexecuted-cell" in f.message
        for f in report.findings
    )


# @id TEST-AIDS-069
# @verifies REQ-AIDS-048
def test_TEST_AIDS_069_trailing_unexecuted_cell_without_audit_call_still_fails(tmp_path):
    handle = resolve_project("audit-nonself-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(notebook, execution_count=1)
    _add_code_cell(notebook, execution_count=None)
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    assert report.unexecuted_cell_indices == (1,)
