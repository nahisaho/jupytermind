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


# @id TEST-AIDS-106
# @verifies REQ-AIDS-045
def test_TEST_AIDS_106_heading_prefixed_cell_with_stale_evidence_is_still_flagged(tmp_path):
    """GitHub #30: a markdown cell that starts with a heading ("#") but
    still carries a ```evidence block must not be excluded from evidence
    validation just because of the leading heading."""
    handle = resolve_project("audit-heading-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.42"}, execution_count=1)
        ],
    )
    stale_manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.99", "claim_type": "correlation"},
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"# Stale heading claim.\n\n```evidence\n{stale_manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    messages = [finding.message for finding in report.findings]
    assert any("missing or stale evidence" in message for message in messages)
    stale_finding = next(f for f in report.findings if "missing or stale evidence" in f.message)
    assert stale_finding.cell_index == 1


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


# @id TEST-AIDS-128
# @verifies REQ-AIDS-066
def test_TEST_AIDS_128_insight_body_contradicting_cited_value_warns(tmp_path):
    """GitHub #45: the body claims "0.123" while the verified cited_value is
    "0.954"; this must surface a warning without failing report.ok."""
    handle = resolve_project("audit-contradiction-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="macro_f1=0.954\n")],
    )
    manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.954", "claim_type": "metric"},
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"macro-F1 は 0.123 と低く、モデルは使えません。\n\n```evidence\n{manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is True
    contradiction_findings = [
        f for f in report.findings if f.severity == "warning" and "0.954" in f.message
    ]
    assert len(contradiction_findings) == 1
    assert contradiction_findings[0].cell_index == 1


# @id TEST-AIDS-129
# @verifies REQ-AIDS-066
def test_TEST_AIDS_129_insight_body_mentioning_cited_value_has_no_contradiction_warning(tmp_path):
    handle = resolve_project("audit-no-contradiction-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="macro_f1=0.954\n")],
    )
    manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.954", "claim_type": "metric"},
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"macro-F1 は 0.954 と高く、良好です。\n\n```evidence\n{manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is True
    assert not any(f.severity == "warning" and "0.954" in f.message for f in report.findings)


# @id TEST-AIDS-130
# @verifies REQ-AIDS-066
def test_TEST_AIDS_130_insight_body_with_rounded_restatement_has_no_contradiction_warning(tmp_path):
    handle = resolve_project("audit-rounded-ok-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="macro_f1=0.954\n")],
    )
    manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.954", "claim_type": "metric"},
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"macro-F1 は 0.95 と高く、良好です。\n\n```evidence\n{manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is True
    assert not any(f.severity == "warning" and "0.954" in f.message for f in report.findings)


# @id TEST-AIDS-137
# @verifies REQ-AIDS-069
def test_TEST_AIDS_137_second_evidence_block_with_stale_value_is_flagged(tmp_path):
    """GitHub #44: a cell with two ```evidence blocks must have both
    validated, not only the first."""
    handle = resolve_project("audit-multi-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.42"}, execution_count=1)
        ],
    )
    first_manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.42", "claim_type": "correlation"},
        separators=(",", ":"),
    )
    second_manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.99", "claim_type": "correlation"},
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"First claim is fine.\n\n```evidence\n{first_manifest}\n```\n\n"
            f"Second claim is stale.\n\n```evidence\n{second_manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    error_messages = [f.message for f in report.findings if f.severity == "error"]
    assert any(
        "0.99" in message or "missing or stale evidence" in message for message in error_messages
    )
    stale_finding = next(
        f for f in report.findings if f.severity == "error" and "0.99" in f.message
    )
    assert stale_finding.cell_index == 1


# @id TEST-AIDS-138
# @verifies REQ-AIDS-069
def test_TEST_AIDS_138_malformed_evidence_block_is_reported_not_skipped(tmp_path):
    handle = resolve_project("audit-malformed-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.42"}, execution_count=1)
        ],
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell("Broken claim.\n\n```evidence\n{not valid json\n```")
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    assert any(
        f.severity == "error" and "malformed evidence block" in f.message.lower()
        for f in report.findings
    )


# @id TEST-AIDS-139
# @verifies REQ-AIDS-069
def test_TEST_AIDS_139_supporting_evidence_entry_unresolved_is_flagged(tmp_path):
    handle = resolve_project("audit-supporting-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.42"}, execution_count=1)
        ],
    )
    manifest = json.dumps(
        {
            "execution_count": 1,
            "cited_value": "0.42",
            "claim_type": "correlation",
            "supporting_evidence": [{"execution_count": 1, "cited_value": "9.99"}],
        },
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"Claim with unresolved supporting evidence.\n\n```evidence\n{manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    assert any(f.severity == "error" and "9.99" in f.message for f in report.findings)


# @id TEST-AIDS-140
# @verifies REQ-AIDS-069
def test_TEST_AIDS_140_malformed_supporting_evidence_entry_is_flagged(tmp_path):
    handle = resolve_project("audit-malformed-supporting-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.42"}, execution_count=1)
        ],
    )
    manifest = json.dumps(
        {
            "execution_count": 1,
            "cited_value": "0.42",
            "claim_type": "correlation",
            "supporting_evidence": [{"execution_count": "not-an-int", "cited_value": "0.42"}],
        },
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"Claim with malformed supporting evidence.\n\n```evidence\n{manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    assert any(
        f.severity == "error" and "malformed supporting_evidence" in f.message.lower()
        for f in report.findings
    )


# @id TEST-AIDS-141
# @verifies REQ-AIDS-069
def test_TEST_AIDS_141_single_well_formed_block_without_supporting_evidence_unchanged(tmp_path):
    handle = resolve_project("audit-single-block-unchanged-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[
            nbformat.v4.new_output("execute_result", data={"text/plain": "0.42"}, execution_count=1)
        ],
    )
    manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.42", "claim_type": "correlation"},
        separators=(",", ":"),
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(f"相関は0.42です。\n\n```evidence\n{manifest}\n```")
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is True
    assert report.insight_cell_count == 1


# @id TEST-AIDS-142
# @verifies REQ-AIDS-070
def test_TEST_AIDS_142_heading_prefixed_result_paragraph_without_evidence_is_flagged(tmp_path):
    """GitHub #43: a heading-prefixed cell with a genuine result paragraph
    and no evidence manifest must be flagged, not silently excluded."""
    handle = resolve_project("audit-heading-no-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(notebook, execution_count=1)
    notebook.cells.append(
        nbformat.v4.new_markdown_cell("## 結果\n平均購入額は9.9万円で、喫煙者は非喫煙者の3倍です。")
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    missing_finding = next(f for f in report.findings if "no evidence manifest" in f.message)
    assert missing_finding.cell_index == 1


# @id TEST-AIDS-143
# @verifies REQ-AIDS-070
def test_TEST_AIDS_143_heading_only_cell_is_not_an_insight_candidate(tmp_path):
    handle = resolve_project("audit-heading-only-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(notebook, execution_count=1)
    notebook.cells.append(nbformat.v4.new_markdown_cell("## 結果\n"))
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is True
    assert report.insight_cell_count == 0


# @id TEST-AIDS-211
# @verifies REQ-AIDS-045
def test_TEST_AIDS_211_duplicate_execution_count_is_reported_as_warning(tmp_path):
    """GitHub #54: two executed code cells sharing execution_count must be
    reported (as a warning, since it does not necessarily indicate any
    specific insight is wrong) instead of passing unnoticed."""
    handle = resolve_project("audit-duplicate-execcount-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="AUC=0.9500\n")],
    )
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="AUC=0.9500 baseline\n")],
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    duplicate_finding = next(
        f for f in report.findings if "is shared by" in f.message and "execution_count" in f.message
    )
    assert duplicate_finding.severity == "warning"
    assert duplicate_finding.cell_index == 0
    assert "execution_count=1" in duplicate_finding.message
    assert "[0, 1]" in duplicate_finding.message


# @id TEST-AIDS-212
# @verifies REQ-AIDS-045
def test_TEST_AIDS_212_ambiguous_evidence_manifest_is_flagged_as_error(tmp_path):
    """GitHub #54: an insight's evidence manifest referencing an
    execution_count that now matches more than one executed cell's output
    must be flagged as an error, not resolved to whichever cell is first."""
    handle = resolve_project("audit-ambiguous-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="AUC=0.9500\n")],
    )
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="AUC=0.9500 baseline\n")],
    )
    manifest = json.dumps(
        {"execution_count": 1, "cited_value": "0.9500", "claim_type": "performance"}
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"The model reaches AUC 0.9500.\n\n```evidence\n{manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    ambiguous_finding = next(
        f for f in report.findings if "ambiguous" in f.message and f.cell_index == 2
    )
    assert ambiguous_finding.severity == "error"


# @id TEST-AIDS-292
# @verifies REQ-AIDS-045
def test_TEST_AIDS_292_ambiguous_supporting_evidence_entry_is_flagged_as_error(tmp_path):
    """GitHub #54: a `supporting_evidence` entry (not just the top-level
    evidence manifest) referencing an execution_count that matches more than
    one executed cell's output must also be flagged as ambiguous."""
    handle = resolve_project("audit-ambiguous-supporting-evidence-project", projects_root=tmp_path)
    ensure_notebook(handle)
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    _add_code_cell(
        notebook,
        execution_count=1,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="AUC=0.9500\n")],
    )
    _add_code_cell(
        notebook,
        execution_count=2,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="Recall=0.8800\n")],
    )
    _add_code_cell(
        notebook,
        execution_count=2,
        outputs=[nbformat.v4.new_output("stream", name="stdout", text="Recall=0.8800 baseline\n")],
    )
    manifest = json.dumps(
        {
            "execution_count": 1,
            "cited_value": "0.9500",
            "claim_type": "performance",
            "supporting_evidence": [{"execution_count": 2, "cited_value": "0.8800"}],
        }
    )
    notebook.cells.append(
        nbformat.v4.new_markdown_cell(
            f"The model reaches AUC 0.9500, supported by Recall 0.8800.\n\n"
            f"```evidence\n{manifest}\n```"
        )
    )
    _write(handle, notebook)

    report = audit_notebook(handle.notebook_path)

    assert report.ok is False
    ambiguous_finding = next(
        f
        for f in report.findings
        if "ambiguous" in f.message and "supporting_evidence" in f.message
    )
    assert ambiguous_finding.severity == "error"
    assert ambiguous_finding.cell_index == 3
