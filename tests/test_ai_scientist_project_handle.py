"""Tests for ai_scientist project handle resolution and workspace setup."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ai_data_scientist.project_manager import InvalidProjectNameError


# @id TEST-AISCI-002
# @verifies REQ-AISCI-002
def test_TEST_AISCI_002_reuses_ai_data_scientist_project_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(tmp_path / "projects"))

    from ai_scientist.project_handle import resolve_research_project

    for bad_name in ["../evil", "a/b", "Has_Upper", "double--hyphen", "trailing-"]:
        with pytest.raises(InvalidProjectNameError):
            resolve_research_project(bad_name)

    assert list((tmp_path / "projects").glob("**/*")) == []


# @id TEST-AISCI-040
# @verifies REQ-AISCI-002
def test_TEST_AISCI_040_rejects_non_string_name_with_the_same_error_type(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(tmp_path / "projects"))

    from ai_scientist.project_handle import resolve_research_project

    for bad_name in [None, 123, ""]:
        with pytest.raises(InvalidProjectNameError):
            resolve_research_project(bad_name)

    assert list((tmp_path / "projects").glob("**/*")) == []


# @id TEST-AISCI-003
# @verifies REQ-AISCI-003
def test_TEST_AISCI_003_creates_research_workspace_once_under_stable_root(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects-root"
    monkeypatch.setenv("AI_DATA_SCIENTIST_PROJECTS_ROOT", str(projects_root))

    from ai_scientist.project_handle import PHASE_DIRECTORIES, resolve_research_project

    handle = resolve_research_project("paper-alpha")

    expected_dirs = {handle.root / directory for directory in PHASE_DIRECTORIES.values()}
    assert expected_dirs == {
        handle.planning_dir,
        handle.literature_dir,
        handle.design_dir,
        handle.manuscript_dir,
        handle.review_dir,
        handle.reproducibility_dir,
        handle.presentation_dir,
    }
    assert all(path.is_dir() for path in expected_dirs)
    assert handle.notebook_path == handle.root / "notebooks" / "paper-alpha.ipynb"

    before = {path.relative_to(handle.root): path.stat().st_mtime_ns for path in expected_dirs}

    drifted_cwd = handle.root / "presentation"
    monkeypatch.chdir(drifted_cwd)
    again = resolve_research_project("paper-alpha")

    after = {path.relative_to(again.root): path.stat().st_mtime_ns for path in expected_dirs}
    assert again.root == handle.root
    assert again.notebook_path == handle.notebook_path
    assert before == after
