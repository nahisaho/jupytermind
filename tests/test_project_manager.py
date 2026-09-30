"""Tests for project & notebook manager (REQ-AIDS-002/011/028/029)."""

import threading

import nbformat
import pytest

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
