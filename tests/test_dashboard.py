"""Tests for interactive dashboard rendering (REQ-AIDS-024)."""

import nbformat
import pandas as pd

from ai_data_scientist.dashboard import render_dashboard


# @id TEST-AIDS-024
# @verifies REQ-AIDS-024
def test_TEST_AIDS_024():
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})
    spec = {"kind": "scatter", "x": "x", "y": "y"}

    output = render_dashboard(df, spec)

    assert output["output_type"] == "display_data"
    assert "text/html" in output["data"]
    html = output["data"]["text/html"]
    assert "plotly" in html.lower()

    notebook = nbformat.v4.new_notebook()
    cell = nbformat.v4.new_code_cell("render_dashboard(df, spec)")
    cell["outputs"] = [output]
    notebook.cells.append(cell)
    nbformat.validate(notebook)
