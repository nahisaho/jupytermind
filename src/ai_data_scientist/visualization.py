"""Visualization generation.

Implements DES-AIDS-009 (REQ-AIDS-007): renders a requested chart to a PNG
image and packages it as an nbformat-compatible output MIME bundle.
"""

from __future__ import annotations

import base64
import io
import re
import warnings
from dataclasses import dataclass, field

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import pandas as pd

from ai_data_scientist.project_manager import ProjectHandle, enqueue_write, next_execution_count

_SUPPORTED_KINDS = ("scatter", "line", "bar", "hist")
_MISSING_GLYPH_RE = re.compile(r"Glyph (\d+) .* missing from (?:current )?font")

# @id CODE-AIDS-054
# @implements REQ-AIDS-046
# @design DES-AIDS-034
_japanese_font_applied = False
_JAPANESE_FONT_FAMILY = "IPAexGothic"


def _contains_non_ascii(text: str | None) -> bool:
    """True if ``text`` contains a character matplotlib's default font
    cannot render legibly (anything outside the printable ASCII range)."""
    return bool(text) and any(ord(ch) > 127 for ch in text)


def _ensure_japanese_font() -> None:
    """Register (once) and reassert (every call) the bundled Japanese font.

    Importing ``japanize_matplotlib`` registers its bundled IPAexGothic
    TrueType font with matplotlib's font manager — an expensive, idempotent
    side effect gated by ``_japanese_font_applied`` so it runs at most once
    per process. Setting ``font.family`` to the registered font name is
    cheap and, unlike the import, is *not* gated: it is reasserted on every
    call that needs it (GitHub #32). Without this, a caller resetting
    matplotlib's global ``rcParams`` between calls (e.g. ``plt.rcdefaults()``)
    would silently revert ``font.family`` to its default, and the previous
    once-per-process guard would then skip reapplying it, causing Japanese
    text to render as "tofu" boxes on later calls even though the font was
    already registered.
    """
    global _japanese_font_applied
    if not _japanese_font_applied:
        with warnings.catch_warnings():
            # japanize_matplotlib relies on distutils.version.LooseVersion,
            # which emits a harmless DeprecationWarning under modern setuptools.
            warnings.simplefilter("ignore", DeprecationWarning)
            import japanize_matplotlib  # noqa: F401 - import side effect registers the font
        _japanese_font_applied = True
    matplotlib.rcParams["font.family"] = _JAPANESE_FONT_FAMILY


# @id CODE-AIDS-084
# @implements REQ-AIDS-064
# @design DES-AIDS-052
_JAPANESE_CHAR_RE = re.compile(
    "["
    "\u3040-\u309f"  # Hiragana
    "\u30a0-\u30ff"  # Katakana
    "\u31f0-\u31ff"  # Katakana Phonetic Extensions
    "\uff65-\uff9f"  # Halfwidth Katakana
    "\u3000-\u303f"  # CJK Symbols and Punctuation
    "\u4e00-\u9fff"  # CJK Unified Ideographs
    "\u3400-\u4dbf"  # CJK Unified Ideographs Extension A
    "\uf900-\ufaff"  # CJK Compatibility Ideographs
    "]"
)


def _contains_japanese(text) -> bool:
    """True if ``str(text)`` contains a Japanese-derived character.

    Narrower than ``_contains_non_ascii``: only matches Hiragana, Katakana
    (including phonetic extensions and halfwidth forms), CJK symbols and
    punctuation, and CJK (Unified/Extension-A/Compatibility) ideographs, per
    REQ-AIDS-064's scoping to Japanese-derived plotted data/tick/legend text.
    Non-string, non-stringifiable values are treated as not containing
    Japanese text.
    """
    if text is None:
        return False
    try:
        value = str(text)
    except Exception:
        return False
    return bool(_JAPANESE_CHAR_RE.search(value))


def _plotted_data_contains_japanese(
    df: pd.DataFrame, kind: str, x: str | None, y: str | None
) -> bool:
    """True if any plotted value/index/legend-source/auto-axis-label text
    for this ``render_chart`` call contains Japanese characters (DES-AIDS-052).
    """
    candidates: list = []

    if kind == "hist":
        candidates.extend(df[x])
        candidates.append(df.index.name)
        candidates.extend(df.index)
        candidates.append(x)
    else:
        if x is not None:
            candidates.extend(df[x])
            candidates.append(x)
        else:
            candidates.append(df.index.name)
            candidates.extend(df.index)

        if y is not None:
            candidates.extend(df[y])
            candidates.append(y)
        else:
            implicit_columns = [column for column in df.columns if column != x]
            for column in implicit_columns:
                candidates.extend(df[column])
                candidates.append(column)

    return any(_contains_japanese(candidate) for candidate in candidates)


# @id CODE-AIDS-085
# @implements REQ-AIDS-060
# @design DES-AIDS-048
@dataclass(frozen=True)
class ChartMetadata:
    """Chart authoring metadata captured at render time (REQ-AIDS-060)."""

    title: str | None
    xlabel: str | None
    ylabel: str | None
    legend: bool
    missing_glyphs: tuple[str, ...] = field(default_factory=tuple)


class RenderedChart(bytes):
    """PNG bytes returned by ``render_chart``, carrying ``chart_metadata``.

    A real ``bytes`` subclass so every existing caller that treats the
    return value via ordinary ``bytes`` operations (``base64.b64encode``,
    equality, slicing, hashing) continues to work unmodified (REQ-AIDS-060).
    """

    chart_metadata: ChartMetadata

    def __new__(cls, data: bytes, chart_metadata: ChartMetadata) -> "RenderedChart":
        instance = super().__new__(cls, data)
        instance.chart_metadata = chart_metadata
        return instance

    @property
    def title(self) -> str | None:
        return self.chart_metadata.title

    @property
    def xlabel(self) -> str | None:
        return self.chart_metadata.xlabel

    @property
    def ylabel(self) -> str | None:
        return self.chart_metadata.ylabel

    @property
    def legend(self) -> bool:
        return self.chart_metadata.legend

    @property
    def missing_glyphs(self) -> tuple[str, ...]:
        return self.chart_metadata.missing_glyphs


# @id CODE-AIDS-007
# @implements REQ-AIDS-007 REQ-AIDS-058 REQ-AIDS-060 REQ-AIDS-064
# @design DES-AIDS-009 DES-AIDS-048 DES-AIDS-052
# CHANGE-004: returns RenderedChart (chart metadata) and widens the
# bundled-Japanese-font trigger; see the render_chart docstring for detail.
def render_chart(
    df: pd.DataFrame,
    kind: str = "scatter",
    x: str | None = None,
    y: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> RenderedChart:
    """Render ``df`` as ``kind`` chart and return a ``RenderedChart``.

    ``title``/``xlabel``/``ylabel`` containing non-ASCII characters (e.g.
    Japanese), or plotted data/tick labels/legend/pandas-auto-generated axis
    labels containing Japanese characters, are rendered using a bundled
    Japanese-capable font (REQ-AIDS-046, REQ-AIDS-064) so they display as
    legible glyphs instead of matplotlib default placeholder boxes,
    regardless of fonts installed on the host. The returned ``RenderedChart``
    is a ``bytes`` subclass carrying the actually-rendered title, axis
    labels, legend presence, and any missing-glyph warnings (REQ-AIDS-060),
    so every existing caller using it as plain PNG bytes continues to work
    unmodified.
    """
    if kind not in _SUPPORTED_KINDS:
        raise ValueError(f"Unsupported chart kind: {kind!r}")

    if any(_contains_non_ascii(text) for text in (title, xlabel, ylabel)) or (
        _plotted_data_contains_japanese(df, kind, x, y)
    ):
        _ensure_japanese_font()

    fig, ax = plt.subplots()
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
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
            # GitHub #31: reposition/pad title, axis labels, and tick labels
            # to fit within the saved canvas instead of being clipped.
            # Applied on every call (not gated by a label-length heuristic)
            # so behavior is deterministic. Runs after text is set
            # (tight_layout measures already-rendered text metrics) and
            # after font configuration above.
            try:
                fig.tight_layout()
            except Exception:
                # Some axes projections (e.g. 3D) raise from tight_layout();
                # constrained_layout is a safe fallback that still
                # repositions text to avoid clipping.
                fig.set_layout_engine("constrained")
            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", bbox_inches="tight")

        missing_glyphs: list[str] = []
        for captured_warning in captured:
            match = _MISSING_GLYPH_RE.search(str(captured_warning.message))
            if match:
                codepoint = match.group(1)
                if codepoint not in missing_glyphs:
                    missing_glyphs.append(codepoint)
            else:
                warnings.warn_explicit(
                    captured_warning.message,
                    captured_warning.category,
                    captured_warning.filename,
                    captured_warning.lineno,
                )

        metadata = ChartMetadata(
            title=ax.get_title() or None,
            xlabel=ax.get_xlabel() or None,
            ylabel=ax.get_ylabel() or None,
            legend=ax.get_legend() is not None,
            missing_glyphs=tuple(missing_glyphs),
        )
        return RenderedChart(buffer.getvalue(), chart_metadata=metadata)
    finally:
        plt.close(fig)


# @id CODE-AIDS-091
# @implements REQ-AIDS-071
# @design DES-AIDS-059
def _chart_metadata_dict(chart_metadata: ChartMetadata) -> dict:
    """Build the JSON-serializable metadata dict shared by
    ``build_image_output`` (output-level) and ``record_chart`` (cell-level)
    for a rendered chart's authoring metadata (DES-AIDS-059)."""
    return {
        "title": chart_metadata.title,
        "xlabel": chart_metadata.xlabel,
        "ylabel": chart_metadata.ylabel,
        "legend": chart_metadata.legend,
        "missing_glyphs": list(chart_metadata.missing_glyphs),
    }


# @id CODE-AIDS-034
# @implements REQ-AIDS-007 REQ-AIDS-071
# @design DES-AIDS-009 DES-AIDS-059
def build_image_output(png_bytes: bytes) -> nbformat.NotebookNode:
    """Wrap PNG bytes as an nbformat execute_result output with image/png data.

    When ``png_bytes`` is a ``RenderedChart`` (the result of
    ``render_chart``), its ``chart_metadata`` is additionally persisted into
    the output's own ``metadata["chart"]`` mapping (REQ-AIDS-071), so a
    single image output is independently auditable even outside
    ``record_chart``'s cell-level metadata. Plain ``bytes`` leave
    ``metadata`` empty, preserving prior behavior.
    """
    encoded = base64.b64encode(png_bytes).decode("ascii")
    metadata = {}
    if isinstance(png_bytes, RenderedChart):
        metadata["chart"] = _chart_metadata_dict(png_bytes.chart_metadata)
    return nbformat.v4.new_output(
        "execute_result",
        data={"image/png": encoded, "text/plain": "<matplotlib chart>"},
        metadata=metadata,
    )


# @id CODE-AIDS-035
# @implements REQ-AIDS-007 REQ-AIDS-040 REQ-AIDS-061
# @design DES-AIDS-009 DES-AIDS-028 DES-AIDS-049
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

    When ``png_bytes`` is a ``RenderedChart`` (the result of ``render_chart``),
    its ``chart_metadata`` is persisted into the new cell's
    ``metadata["chart"]`` mapping so ``audit_notebook(..., visual_audit=True)``
    can audit it without re-rendering (REQ-AIDS-061). Plain ``bytes`` (e.g.
    read from a file, not produced by ``render_chart``) leave
    ``metadata["chart"]`` unset, preserving the existing "unaudited" finding.
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
        if isinstance(png_bytes, RenderedChart):
            cell["metadata"]["chart"] = _chart_metadata_dict(png_bytes.chart_metadata)
        nb.cells.append(cell)

    enqueue_write(handle, add_cell)
    return stamped_count["value"]
