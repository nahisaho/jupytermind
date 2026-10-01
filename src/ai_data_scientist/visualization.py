"""Visualization generation.

Implements DES-AIDS-009 (REQ-AIDS-007): renders a requested chart to a PNG
image and packages it as an nbformat-compatible output MIME bundle.
"""

from __future__ import annotations

import base64
import io
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import pandas as pd

from ai_data_scientist.project_manager import ProjectHandle, enqueue_write, next_execution_count

_SUPPORTED_KINDS = ("scatter", "line", "bar", "hist")

# @id CODE-AIDS-054
# @implements REQ-AIDS-046
# @design DES-AIDS-034
_japanese_font_applied = False


def _contains_non_ascii(text: str | None) -> bool:
    """True if ``text`` contains a character matplotlib's default font
    cannot render legibly (anything outside the printable ASCII range)."""
    return bool(text) and any(ord(ch) > 127 for ch in text)


def _ensure_japanese_font() -> None:
    """Lazily register the bundled Japanese-capable font with matplotlib.

    Importing/calling ``japanize_matplotlib.japanize()`` registers its
    bundled IPAexGothic TrueType font with matplotlib's font manager and
    sets it as the active ``font.family`` (REQ-AIDS-046), independent of
    whatever fonts happen to be installed on the host. Only triggered once
    per process: charts with no non-ASCII title/xlabel/ylabel never pay
    this cost and matplotlib's default font behavior is unaffected until
    Japanese (or other non-ASCII) text first appears.
    """
    global _japanese_font_applied
    if _japanese_font_applied:
        return
    with warnings.catch_warnings():
        # japanize_matplotlib relies on distutils.version.LooseVersion,
        # which emits a harmless DeprecationWarning under modern setuptools.
        warnings.simplefilter("ignore", DeprecationWarning)
        import japanize_matplotlib  # noqa: F401 - import side effect registers the font
    _japanese_font_applied = True


# @id CODE-AIDS-007
# @implements REQ-AIDS-007
# @design DES-AIDS-009
def render_chart(
    df: pd.DataFrame,
    kind: str = "scatter",
    x: str | None = None,
    y: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> bytes:
    """Render ``df`` as ``kind`` chart and return PNG bytes.

    ``title``/``xlabel``/``ylabel`` containing non-ASCII characters (e.g.
    Japanese) are rendered using a bundled Japanese-capable font
    (REQ-AIDS-046) so they display as legible glyphs instead of matplotlib's
    default placeholder boxes, regardless of fonts installed on the host.
    """
    if kind not in _SUPPORTED_KINDS:
        raise ValueError(f"Unsupported chart kind: {kind!r}")

    if any(_contains_non_ascii(text) for text in (title, xlabel, ylabel)):
        _ensure_japanese_font()

    fig, ax = plt.subplots()
    try:
        if kind == "hist":
            df[x].plot(kind="hist", ax=ax)
        else:
            df.plot(kind=kind, x=x, y=y, ax=ax)
        if title is not None:
            ax.set_title(title)
        if xlabel is not None:
            ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)
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


# @id CODE-AIDS-035
# @implements REQ-AIDS-007 REQ-AIDS-040
# @design DES-AIDS-009 DES-AIDS-028
def record_chart(handle: ProjectHandle, code: str, png_bytes: bytes) -> int:
    """Persist a rendered chart as an executed code cell in the project notebook.

    Mirrors mcp_gateway.run_and_record's ergonomics for chart/image outputs so
    callers don't need to hand-roll enqueue_write boilerplate. Returns the
    stamped execution_count of the new cell.

    ``code`` is never executed against the live Jupyter kernel (REQ-AIDS-040):
    rendering happens locally via ``render_chart`` and ``code`` is stored only
    as a human-readable record of how the chart was produced. Callers must
    ensure ``code`` references only variables already established by a prior
    ``mcp_gateway.run_and_record`` call, so the notebook stays consistent if a
    human re-runs it top-to-bottom against the live kernel later.
    """
    stamped_count: dict[str, int] = {}

    def add_cell(nb):
        execution_count = next_execution_count(nb)
        stamped_count["value"] = execution_count
        cell = nbformat.v4.new_code_cell(code)
        cell["execution_count"] = execution_count
        output = build_image_output(png_bytes)
        output["execution_count"] = execution_count
        cell["outputs"] = [output]
        nb.cells.append(cell)

    enqueue_write(handle, add_cell)
    return stamped_count["value"]
