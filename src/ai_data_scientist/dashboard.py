"""Interactive dashboard rendering.

Implements DES-AIDS-023 (REQ-AIDS-024): renders an interactive widget or
chart embedded in the notebook output, extending the MVP's static chart
rendering with an interactive HTML MIME bundle.
"""

from __future__ import annotations

import nbformat
import pandas as pd
import plotly.express as px

_SUPPORTED_KINDS = ("scatter", "line", "bar")


# @id CODE-AIDS-024
# @implements REQ-AIDS-024
# @design DES-AIDS-023
def render_dashboard(df: pd.DataFrame, spec: dict) -> nbformat.NotebookNode:
    """Render ``df`` per ``spec`` as an interactive HTML output bundle."""
    kind = spec.get("kind", "scatter")
    if kind not in _SUPPORTED_KINDS:
        raise ValueError(f"Unsupported dashboard chart kind: {kind!r}")

    plot_fn = {"scatter": px.scatter, "line": px.line, "bar": px.bar}[kind]
    figure = plot_fn(df, x=spec.get("x"), y=spec.get("y"))
    html = figure.to_html(include_plotlyjs="cdn", full_html=False)

    return nbformat.v4.new_output(
        "display_data",
        data={"text/html": html, "text/plain": "<interactive plotly dashboard>"},
    )
