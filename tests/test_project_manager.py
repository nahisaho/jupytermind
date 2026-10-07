"""Tests for project & notebook manager (REQ-AIDS-002/011/028/029).

Change: CHANGE-033
"""

import importlib
import threading
from pathlib import Path

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


# ---------------------------------------------------------------------------
# REQ-AIDS-093 / DES-AIDS-093 (GitHub #72): slug-verified ancestor-directory
# discovery of an existing projects root, so a freshly started process/kernel
# whose own import-time cwd has already drifted inside an existing
# projects/<slug>/... tree rediscovers that same tree instead of recreating
# a nested projects/<slug>/notebooks/projects/<slug> path.
#
# All 9 scenarios are proven end-to-end across a real OS process boundary via
# `subprocess.run` (TEST-AIDS-331/332/337/340-345), since that is the exact
# failure mode reported in #72 (a *different process* importing the module
# fresh with an already-drifted cwd) and is the "required subprocess-based
# regression test" DES-AIDS-093 calls for. Scenarios 3-6/8/9 are additionally
# unit-tested directly against `_discover_ancestor_projects_root` (a pure
# function of `start`/`name`, per the DES-AIDS-093 "unit-tested directly"
# interface), which DES-AIDS-093 calls for "in addition to" the required
# subprocess coverage.
# ---------------------------------------------------------------------------

import subprocess
import sys


def _subprocess_resolve(cwd, name, env_root=None):
    """Run a fresh Python process that imports project_manager from ``cwd``
    and returns the resolved/created notebook path, proving real cross-process
    behavior (not importlib.reload within the same process)."""
    import os

    env = dict(os.environ)
    repo_src = str(_repo_src_dir())
    env["PYTHONPATH"] = repo_src + os.pathsep + env.get("PYTHONPATH", "")
    if env_root is not None:
        env["AI_DATA_SCIENTIST_PROJECTS_ROOT"] = str(env_root)
    else:
        env.pop("AI_DATA_SCIENTIST_PROJECTS_ROOT", None)
    code = (
        "from ai_data_scientist.project_manager import resolve_project, ensure_notebook\n"
        f"handle = resolve_project({name!r})\n"
        "print(ensure_notebook(handle))\n"
        "print(handle.root)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"subprocess failed: {result.stderr}"
    lines = result.stdout.strip().splitlines()
    return Path(lines[0]), Path(lines[1])


def _repo_src_dir():
    return Path(__file__).resolve().parents[1] / "src"


# @id TEST-AIDS-331
# @verifies REQ-AIDS-093
def test_TEST_AIDS_331_subprocess_drifted_cwd_discovers_existing_root(tmp_path, monkeypatch):
    """Scenario (1): a brand-new process whose cwd is already the project's
    own notebooks dir, env var unset, discovers the pre-existing root instead
    of recreating a nested projects/<slug>/notebooks/projects/<slug> tree."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)
    monkeypatch.chdir(workspace_root)

    first_notebook, first_root = _subprocess_resolve(workspace_root, "drift-project")

    notebooks_dir = first_root / "notebooks"
    assert notebooks_dir.is_dir()

    second_notebook, second_root = _subprocess_resolve(notebooks_dir, "drift-project")

    assert second_root == first_root
    assert second_notebook == first_notebook
    assert not (first_root / "notebooks" / "projects").exists()


# @id TEST-AIDS-332
# @verifies REQ-AIDS-093
def test_TEST_AIDS_332_subprocess_env_var_wins_over_discovery(tmp_path, monkeypatch):
    """Scenario (2): same drifted cwd, but the env var is set to a distinct,
    separately existing projects_root; the env var takes strict precedence
    over ancestor discovery."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)
    monkeypatch.chdir(workspace_root)
    _, original_root = _subprocess_resolve(workspace_root, "drift-project")
    notebooks_dir = original_root / "notebooks"

    other_root_parent = tmp_path / "other-workspace"
    other_projects_root = other_root_parent / "projects"
    other_projects_root.mkdir(parents=True)

    _, resolved_root = _subprocess_resolve(
        notebooks_dir, "drift-project", env_root=other_projects_root
    )

    assert resolved_root == (other_projects_root / "drift-project").resolve()
    assert resolved_root != original_root


# @id TEST-AIDS-333
# @verifies REQ-AIDS-093
def test_TEST_AIDS_333_discover_returns_none_when_no_ancestor_matches(tmp_path):
    """Scenario (3): no ancestor is both named exactly "projects" and already
    contains this slug anywhere; discovery returns None (caller falls back
    to the existing <import-time cwd>/projects default)."""
    start = tmp_path / "a" / "b" / "c"
    start.mkdir(parents=True)

    assert project_manager._discover_ancestor_projects_root(start, "my-project") is None


# @id TEST-AIDS-334
# @verifies REQ-AIDS-093
def test_TEST_AIDS_334_discover_skips_unrelated_projects_named_ancestor(tmp_path):
    """Scenario (4): cwd sits beneath an unrelated ancestor literally named
    "projects" that does not yet contain this project's slug (e.g. a personal
    ~/projects/<repo> workspace convention); discovery must not misfire."""
    unrelated_projects = tmp_path / "projects"
    start = unrelated_projects / "some-repo" / "subdir"
    start.mkdir(parents=True)

    assert project_manager._discover_ancestor_projects_root(start, "my-project") is None


# @id TEST-AIDS-335
# @verifies REQ-AIDS-093
def test_TEST_AIDS_335_discover_skips_nested_non_matching_projects_dir(tmp_path):
    """Scenario (5): cwd sits beneath another project's own nested directory
    that happens to be named "projects" but does not contain this slug; the
    walk skips it and continues outward to an eligible outer root."""
    outer_root = tmp_path / "outer" / "projects"
    (outer_root / "my-project").mkdir(parents=True)
    inner_decoy = outer_root / "my-project" / "generated-output" / "projects"
    inner_decoy.mkdir(parents=True)
    start = inner_decoy / "deep"
    start.mkdir()

    discovered = project_manager._discover_ancestor_projects_root(start, "my-project")

    assert discovered == outer_root.resolve()


# @id TEST-AIDS-336
# @verifies REQ-AIDS-093
def test_TEST_AIDS_336_discover_selects_cwd_itself(tmp_path):
    """Scenario (6): cwd itself is exactly a directory named "projects" that
    already contains this slug; selected immediately as the zero-th
    candidate."""
    projects_dir = tmp_path / "projects"
    (projects_dir / "my-project").mkdir(parents=True)

    discovered = project_manager._discover_ancestor_projects_root(projects_dir, "my-project")

    assert discovered == projects_dir.resolve()


# @id TEST-AIDS-337
# @verifies REQ-AIDS-093
def test_TEST_AIDS_337_subprocess_slug_literally_projects_round_trips(tmp_path, monkeypatch):
    """Scenario (7): a project whose own slug is literally "projects" still
    disambiguates correctly end-to-end across a real process boundary."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)
    monkeypatch.chdir(workspace_root)

    first_notebook, first_root = _subprocess_resolve(workspace_root, "projects")
    notebooks_dir = first_root / "notebooks"

    second_notebook, second_root = _subprocess_resolve(notebooks_dir, "projects")

    assert second_root == first_root
    assert second_notebook == first_notebook
    assert not (first_root / "notebooks" / "projects").exists()


# @id TEST-AIDS-338
# @verifies REQ-AIDS-093
def test_TEST_AIDS_338_discover_treats_slug_file_as_non_match(tmp_path):
    """Scenario (8): an ancestor literally named "projects" whose would-be
    slug entry exists but is a regular file, not a directory, is treated as
    a non-match; the walk continues outward to an eligible outer root."""
    outer_root = tmp_path / "outer" / "projects"
    (outer_root / "my-project").mkdir(parents=True)
    inner_projects = outer_root / "my-project" / "notebooks" / "projects"
    inner_projects.mkdir(parents=True)
    (inner_projects / "my-project").write_text("not a directory", encoding="utf-8")
    start = inner_projects / "my-project"  # cwd below the file is impossible; walk from parent
    start = inner_projects

    discovered = project_manager._discover_ancestor_projects_root(start, "my-project")

    assert discovered == outer_root.resolve()


# @id TEST-AIDS-339
# @verifies REQ-AIDS-093
def test_TEST_AIDS_339_discover_selects_nearest_of_two_matching_ancestors(tmp_path):
    """Scenario (9): two ancestors both satisfy name=="projects" and contain
    the requested slug (a leftover/duplicated tree further up the ancestry);
    the nearer one (walking outward from start) is selected deterministically."""
    outer_projects = tmp_path / "outer" / "projects"
    (outer_projects / "my-project").mkdir(parents=True)
    inner_projects = outer_projects / "my-project" / "projects"
    (inner_projects / "my-project").mkdir(parents=True)
    start = inner_projects / "my-project"

    discovered = project_manager._discover_ancestor_projects_root(start, "my-project")

    assert discovered == inner_projects.resolve()


# Scenarios 3-6/8/9 are additionally proven end-to-end across a real OS
# process boundary via subprocess.run (not just the direct unit tests above),
# because DES-AIDS-093 requires "all subprocess-based" regression-test
# scenarios and lists the direct unit tests as *in addition to*, not a
# substitute for, that subprocess evidence.


# @id TEST-AIDS-340
# @verifies REQ-AIDS-093
def test_TEST_AIDS_340_subprocess_no_ancestor_match_falls_back(tmp_path, monkeypatch):
    """Scenario (3), subprocess: no ancestor is both named "projects" and
    already contains this slug; a fresh process falls back to
    <import-time cwd>/projects."""
    start = tmp_path / "a" / "b" / "c"
    start.mkdir(parents=True)
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)

    _, root = _subprocess_resolve(start, "no-ancestor-project")

    assert root == (start / "projects" / "no-ancestor-project").resolve()


# @id TEST-AIDS-341
# @verifies REQ-AIDS-093
def test_TEST_AIDS_341_subprocess_skips_unrelated_projects_named_ancestor(tmp_path, monkeypatch):
    """Scenario (4), subprocess: cwd sits beneath an unrelated ancestor
    literally named "projects" that does not yet contain this project's
    slug (e.g. a personal ~/projects/<repo> workspace); a fresh process must
    not misfire onto it and instead falls back to <import-time cwd>/projects."""
    unrelated_projects = tmp_path / "projects"
    start = unrelated_projects / "some-repo" / "subdir"
    start.mkdir(parents=True)
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)

    _, root = _subprocess_resolve(start, "my-project")

    assert root == (start / "projects" / "my-project").resolve()
    assert root != (unrelated_projects / "my-project").resolve()


# @id TEST-AIDS-342
# @verifies REQ-AIDS-093
def test_TEST_AIDS_342_subprocess_skips_nested_non_matching_projects_dir(tmp_path, monkeypatch):
    """Scenario (5), subprocess: cwd sits beneath another project's own
    nested directory that happens to be named "projects" but does not
    contain this slug; a fresh process skips it and discovers the eligible
    outer root instead of falling back or misfiring on the decoy."""
    outer_root = tmp_path / "outer" / "projects"
    (outer_root / "my-project").mkdir(parents=True)
    inner_decoy = outer_root / "my-project" / "generated-output" / "projects"
    inner_decoy.mkdir(parents=True)
    start = inner_decoy / "deep"
    start.mkdir()
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)

    _, root = _subprocess_resolve(start, "my-project")

    assert root == (outer_root / "my-project").resolve()
    assert not (inner_decoy / "my-project").exists()


# @id TEST-AIDS-343
# @verifies REQ-AIDS-093
def test_TEST_AIDS_343_subprocess_selects_cwd_itself(tmp_path, monkeypatch):
    """Scenario (6), subprocess: cwd itself is exactly a directory named
    "projects" that already contains this slug; a fresh process selects it
    immediately as the zero-th candidate."""
    projects_dir = tmp_path / "projects"
    (projects_dir / "my-project").mkdir(parents=True)
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)

    _, root = _subprocess_resolve(projects_dir, "my-project")

    assert root == (projects_dir / "my-project").resolve()


# @id TEST-AIDS-344
# @verifies REQ-AIDS-093
def test_TEST_AIDS_344_subprocess_treats_slug_file_as_non_match(tmp_path, monkeypatch):
    """Scenario (8), subprocess: an ancestor literally named "projects" whose
    would-be slug entry exists but is a regular file, not a directory, is
    treated as a non-match by a fresh process; the walk continues outward to
    the eligible outer root rather than raising or misresolving."""
    outer_root = tmp_path / "outer" / "projects"
    (outer_root / "my-project").mkdir(parents=True)
    inner_projects = outer_root / "my-project" / "notebooks" / "projects"
    inner_projects.mkdir(parents=True)
    (inner_projects / "my-project").write_text("not a directory", encoding="utf-8")
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)

    _, root = _subprocess_resolve(inner_projects, "my-project")

    assert root == (outer_root / "my-project").resolve()


# @id TEST-AIDS-345
# @verifies REQ-AIDS-093
def test_TEST_AIDS_345_subprocess_selects_nearest_of_two_matching_ancestors(tmp_path, monkeypatch):
    """Scenario (9), subprocess: two ancestors both satisfy name=="projects"
    and contain the requested slug (a leftover/duplicated tree further up the
    ancestry); a fresh process deterministically selects the nearer one."""
    outer_projects = tmp_path / "outer" / "projects"
    (outer_projects / "my-project").mkdir(parents=True)
    inner_projects = outer_projects / "my-project" / "projects"
    (inner_projects / "my-project").mkdir(parents=True)
    start = inner_projects / "my-project"
    monkeypatch.delenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", raising=False)

    _, root = _subprocess_resolve(start, "my-project")

    assert root == (inner_projects / "my-project").resolve()
