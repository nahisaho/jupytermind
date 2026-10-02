"""Tests for project & notebook manager (REQ-AIDS-002/011/028/029)."""

import importlib
import threading

import nbformat
import pytest

from ai_data_scientist import project_manager
from ai_data_scientist.project_manager import (
    InvalidProjectNameError,
    enqueue_write,
    ensure_notebook,
    resolve_project,
)


# @id TEST-AIDS-028
# @verifies REQ-AIDS-028
def test_TEST_AIDS_028(tmp_path):
    for bad_name in ["../evil", "a/b", "/abs/path", "Has_Upper", "trailing-", "double--hyphen"]:
        with pytest.raises(InvalidProjectNameError):
            resolve_project(bad_name, projects_root=tmp_path)
    assert list(tmp_path.iterdir()) == []


# @id TEST-AIDS-002
# @verifies REQ-AIDS-002
def test_TEST_AIDS_002(tmp_path):
    handle = resolve_project("sales-2024", projects_root=tmp_path)
    created_path = ensure_notebook(handle)
    assert created_path.exists()
    matches = list(tmp_path.rglob("*.ipynb"))
    assert len(matches) == 1

    reused_path = ensure_notebook(handle)
    assert reused_path == created_path
    matches_again = list(tmp_path.rglob("*.ipynb"))
    assert len(matches_again) == 1


# @id TEST-AIDS-011
# @verifies REQ-AIDS-011
def test_TEST_AIDS_011(tmp_path):
    handle = resolve_project("history-project", projects_root=tmp_path)
    ensure_notebook(handle)

    def add_cell(nb):
        nb.cells.append(nbformat.v4.new_code_cell("1 + 1"))

    enqueue_write(handle, add_cell)
    enqueue_write(handle, add_cell)

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    nbformat.validate(notebook)
    assert len(notebook.cells) == 2


# @id TEST-AIDS-029
# @verifies REQ-AIDS-029
def test_TEST_AIDS_029(tmp_path):
    handle = resolve_project("concurrent-project", projects_root=tmp_path)
    ensure_notebook(handle)

    def make_cell_writer(marker):
        def add_cell(nb):
            nb.cells.append(nbformat.v4.new_code_cell(f"marker = '{marker}'"))

        return add_cell

    threads = [
        threading.Thread(target=enqueue_write, args=(handle, make_cell_writer(i)))
        for i in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    nbformat.validate(notebook)
    assert len(notebook.cells) == 10
    markers = {cell.source for cell in notebook.cells}
    assert len(markers) == 10


# @id TEST-AIDS-104
# @verifies REQ-AIDS-029
def test_TEST_AIDS_104_serialization_failure_does_not_corrupt_existing_notebook(tmp_path):
    """GitHub #27: a mutation that nbformat.validate() accepts but that fails
    at serialization time (e.g. a non-JSON-serializable metadata value) must
    never truncate or corrupt the already-written notebook on disk."""
    handle = resolve_project("atomic-write-project", projects_root=tmp_path)
    ensure_notebook(handle)

    def add_first_cell(nb):
        nb.cells.append(nbformat.v4.new_code_cell("first = 1"))

    enqueue_write(handle, add_first_cell)
    before = handle.notebook_path.read_text(encoding="utf-8")
    assert before  # the notebook has real, non-empty prior content

    def add_unserializable_cell(nb):
        cell = nbformat.v4.new_code_cell("second = 2")
        # A set is valid nbformat metadata structurally (validate() accepts
        # an arbitrary mapping) but is not JSON-serializable, so writing it
        # out fails at serialization time, not at validation time.
        cell["metadata"]["bad"] = {1, 2, 3}
        nb.cells.append(cell)

    with pytest.raises(TypeError):
        enqueue_write(handle, add_unserializable_cell)

    after = handle.notebook_path.read_text(encoding="utf-8")
    assert after == before

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    nbformat.validate(notebook)
    assert len(notebook.cells) == 1
    assert notebook.cells[0].source == "first = 1"


# @id TEST-AIDS-057
# @verifies REQ-AIDS-044
def test_TEST_AIDS_057_default_root_env_override_is_stable_across_cwd(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(workspace_root / "projects"))

    handle_from_root = resolve_project("stable-project")

    notebook_subdir = workspace_root / "projects" / "other-project" / "notebooks"
    notebook_subdir.mkdir(parents=True)
    monkeypatch.chdir(notebook_subdir)

    handle_from_subdir = resolve_project("stable-project")

    assert handle_from_root.root == handle_from_subdir.root
    assert handle_from_root.notebook_path == handle_from_subdir.notebook_path
    assert not (handle_from_root.root / "notebooks" / "projects").exists()


# @id TEST-AIDS-058
# @verifies REQ-AIDS-044
def test_TEST_AIDS_058_default_root_falls_back_to_import_time_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)
    workspace_root = tmp_path / "workspace-fallback"
    workspace_root.mkdir()
    original_cwd = tmp_path

    try:
        monkeypatch.chdir(workspace_root)
        importlib.reload(project_manager)

        handle_from_root = project_manager.resolve_project("stable-project")

        notebook_subdir = workspace_root / "projects" / "other-project" / "notebooks"
        notebook_subdir.mkdir(parents=True)
        monkeypatch.chdir(notebook_subdir)

        handle_from_subdir = project_manager.resolve_project("stable-project")

        assert handle_from_root.root == handle_from_subdir.root
        assert handle_from_root.notebook_path == handle_from_subdir.notebook_path
        assert handle_from_root.root == (workspace_root / "projects" / "stable-project").resolve()
    finally:
        monkeypatch.chdir(original_cwd)
        importlib.reload(project_manager)


# @id TEST-AIDS-070
# @verifies REQ-AIDS-049
def test_TEST_AIDS_070_data_dir_is_stable_and_ensure_data_dir_creates_it(tmp_path, monkeypatch):
    handle = resolve_project("data-dir-project", projects_root=tmp_path)
    ensure_notebook(handle)

    assert handle.data_dir == handle.root / "data"
    assert not handle.data_dir.exists()

    created = project_manager.ensure_data_dir(handle)

    assert created == handle.data_dir
    assert created.is_dir()

    # Calling again (e.g. from a different cwd) must not fail and must keep
    # pointing at the same stable, root-anchored location.
    monkeypatch.chdir(handle.notebook_path.parent)
    handle_again = resolve_project("data-dir-project", projects_root=tmp_path)
    assert handle_again.data_dir == handle.data_dir
    assert project_manager.ensure_data_dir(handle_again) == handle.data_dir


# @id TEST-AIDS-071
# @verifies REQ-AIDS-047
def test_TEST_AIDS_071_resolve_stable_path_falls_back_and_raises(tmp_path, monkeypatch):
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    monkeypatch.setattr(project_manager, "_IMPORT_TIME_CWD", workspace_root)

    target = workspace_root / "data" / "file.csv"
    target.parent.mkdir(parents=True)
    target.write_text("x", encoding="utf-8")

    other_dir = workspace_root / "elsewhere"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)

    resolved = project_manager.resolve_stable_path("data/file.csv")
    assert resolved == target.resolve()

    with pytest.raises(project_manager.StablePathResolutionError):
        project_manager.resolve_stable_path("data/missing.csv")


# @id TEST-AIDS-112
# @verifies REQ-AIDS-059
def test_TEST_AIDS_112_concurrent_mcp_write_risk_is_documented():
    """GitHub #34: SKILL.md and enqueue_write's docstring must both state the
    Jupyter-MCP concurrent-external-save risk and its mitigation. Documentation-
    only requirement (REQ-AIDS-059); no runtime behavior is asserted here."""
    from pathlib import Path

    skill_path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "skills"
        / "ai-data-scientist"
        / "SKILL.md"
    )
    skill_text = skill_path.read_text(encoding="utf-8")
    assert "Concurrent-write risk" in skill_text
    assert "MCP" in skill_text

    docstring = enqueue_write.__doc__ or ""
    assert "Concurrent-write risk" in docstring
    assert "MCP" in docstring
