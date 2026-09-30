"""Visualization generation.

Implements DES-AIDS-009 (REQ-AIDS-007): renders a requested chart to a PNG
image and packages it as an nbformat-compatible output MIME bundle.
"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import pandas as pd

_SUPPORTED_KINDS = ("scatter", "line", "bar", "hist")


# @id CODE-AIDS-007
# @implements REQ-AIDS-007
# @design DES-AIDS-009
def render_chart(
    df: pd.DataFrame, kind: str = "scatter", x: str | None = None, y: str | None = None
) -> bytes:
    """Render ``df`` as ``kind`` chart and return PNG bytes."""
    if kind not in _SUPPORTED_KINDS:
        raise ValueError(f"Unsupported chart kind: {kind!r}")

    fig, ax = plt.subplots()
    try:
        if kind == "hist":
            df[x].plot(kind="hist", ax=ax)
        else:
            df.plot(kind=kind, x=x, y=y, ax=ax)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png")
        return buffer.getvalue()
    finally:
        plt.close(fig)


# @id CODE-AIDS-034
# @implements REQ-AIDS-007
# @design DES-AIDS-009
def build_image_output(png_bytes: bytes) -> nbformat.NotebookNode:
    """Wrap PNG bytes as an nbformat execute_result output with image/png data."""
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return nbformat.v4.new_output(
        "execute_result",
        data={"image/png": encoded, "text/plain": "<matplotlib chart>"},
    )
