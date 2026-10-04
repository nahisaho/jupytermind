"""Visualization generation.

Implements DES-AIDS-009 (REQ-AIDS-007): renders a requested chart to a PNG
image and packages it as an nbformat-compatible output MIME bundle.
"""

from __future__ import annotations

import base64
import io
import re
import secrets
import warnings
from dataclasses import dataclass, field
from typing import Self

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import pandas as pd

from ai_data_scientist.project_manager import ProjectHandle, enqueue_write, next_execution_count

_SUPPORTED_KINDS = ("scatter", "line", "bar", "barh", "box", "hist", "heatmap")
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
    except Exception:  # noqa: BLE001 - arbitrary user objects may raise from __str__
        return False
    return bool(_JAPANESE_CHAR_RE.search(value))


def _plotted_data_contains_japanese(
    df: pd.DataFrame,
    kind: str,
    x: str | None,
    y: str | None,
    hue: str | None = None,
    legend_title: str | None = None,
) -> bool:
    """True if any plotted value/index/legend-source/auto-axis-label text
    for this ``render_chart`` call contains Japanese characters (DES-AIDS-052).
    """
    candidates: list = [legend_title]

    def _add_column(column_name: str | None) -> None:
        if column_name is None:
            return
        candidates.append(column_name)
        if column_name in df.columns:
            candidates.extend(df[column_name])

    _add_column(hue)

    if kind == "hist" and x is not None:
        _add_column(x)
        candidates.append(df.index.name)
        candidates.extend(df.index)
    elif kind == "heatmap":
        if x is not None and y is not None:
            _add_column(x)
            _add_column(y)
        else:
            candidates.extend(df.columns)
            candidates.append(df.index.name)
            candidates.extend(df.index)
    elif kind == "box":
        _add_column(x)
        _add_column(y)
        if x is None and y is None:
            candidates.extend(df.columns)
    else:
        if x is not None:
            _add_column(x)
        else:
            candidates.append(df.index.name)
            candidates.extend(df.index)

        if y is not None:
            _add_column(y)
        else:
            implicit_columns = [column for column in df.columns if column not in {x, hue}]
            for column in implicit_columns:
                _add_column(column)

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
    legend_title: str | None = None
    missing_glyphs: tuple[str, ...] = field(default_factory=tuple)


class RenderedChart(bytes):
    """PNG bytes returned by ``render_chart``, carrying ``chart_metadata``.

    A real ``bytes`` subclass so every existing caller that treats the
    return value via ordinary ``bytes`` operations (``base64.b64encode``,
    equality, slicing, hashing) continues to work unmodified (REQ-AIDS-060).
    """

    chart_metadata: ChartMetadata

    def __new__(cls, data: bytes, chart_metadata: ChartMetadata) -> Self:
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
    def legend_title(self) -> str | None:
        return self.chart_metadata.legend_title

    @property
    def missing_glyphs(self) -> tuple[str, ...]:
        return self.chart_metadata.missing_glyphs


# @id CODE-AIDS-111
# @implements REQ-AIDS-088
# @design DES-AIDS-076
def chart_metadata_from_figure(
    fig, *, missing_glyphs: tuple[str, ...] | list[str] = ()
) -> ChartMetadata:
    """Build ``ChartMetadata`` from an existing matplotlib ``Figure``."""
    if not fig.axes:
        raise ValueError("Figure has no axes to inspect")
    ax = fig.axes[0]
    legend = ax.get_legend()
    legend_title = None
    if legend is not None:
        legend_title = legend.get_title().get_text() or None
    return ChartMetadata(
        title=ax.get_title() or None,
        xlabel=ax.get_xlabel() or None,
        ylabel=ax.get_ylabel() or None,
        legend=legend is not None,
        legend_title=legend_title,
        missing_glyphs=tuple(str(codepoint) for codepoint in missing_glyphs),
    )


def _apply_legend_title(ax, hue: str | None, legend_title: str | None) -> None:
    legend = ax.get_legend()
    if legend is None:
        return
    if legend_title is not None:
        legend.set_title(legend_title)
    elif hue is not None:
        legend.set_title(hue)


def _require_columns(df: pd.DataFrame, *columns: str | None) -> None:
    for column in columns:
        if column is not None and column not in df.columns:
            raise ValueError(f"Unknown column: {column!r}")


# @id CODE-AIDS-112
# @implements REQ-AIDS-087
# @design DES-AIDS-075
def _resolve_error_values(
    df: pd.DataFrame, spec: str | tuple[str, str] | list[str] | None
) -> list[float] | list[list[float]] | None:
    if spec is None:
        return None
    if isinstance(spec, str):
        _require_columns(df, spec)
        return df[spec].tolist()
    if isinstance(spec, (tuple, list)) and len(spec) == 2 and all(
        isinstance(column, str) for column in spec
    ):
        lower, upper = spec
        _require_columns(df, lower, upper)
        return [df[lower].tolist(), df[upper].tolist()]
    raise ValueError("Error ranges must be a column name or a two-column (lower, upper) pair")


def _group_label(value) -> str:
    return "NaN" if pd.isna(value) else str(value)


# @id CODE-AIDS-116
# @implements REQ-AIDS-086
# @design DES-AIDS-074
def _normalize_hue_for_pivot(series: pd.Series) -> tuple[pd.Series, str]:
    sentinel = f"__missing_hue__{secrets.token_hex(8)}"
    existing_values = {str(value) for value in series.dropna().tolist()}
    while sentinel in existing_values:
        sentinel = f"__missing_hue__{secrets.token_hex(8)}"
    normalized = series.astype("object").where(~series.isna(), sentinel)
    return normalized, sentinel


def _pivot_grouped_values(
    df: pd.DataFrame, *, x: str, hue: str, value: str
) -> pd.DataFrame:
    normalized_hue, sentinel = _normalize_hue_for_pivot(df[hue])
    order = list(dict.fromkeys(normalized_hue.tolist()))
    pivot_source = pd.DataFrame({x: df[x], "__hue__": normalized_hue, value: df[value]})
    duplicates = pivot_source.duplicated(subset=[x, "__hue__"], keep=False)
    if duplicates.any():
        raise ValueError(
            f"Grouped {value!r} data must be unique per ({x!r}, {hue!r}) pair; "
            "pre-aggregate duplicate rows before plotting."
        )
    pivot = pivot_source.pivot(index=x, columns="__hue__", values=value)
    pivot = pivot.reindex(columns=order)
    pivot = pivot.rename(columns={sentinel: "NaN"})
    return pivot


# @id CODE-AIDS-117
# @implements REQ-AIDS-087
# @design DES-AIDS-075
def _pivot_error_values(
    df: pd.DataFrame,
    *,
    x: str,
    hue: str,
    spec: str | tuple[str, str] | list[str] | None,
):
    if spec is None:
        return None
    if isinstance(spec, str):
        return _pivot_grouped_values(df, x=x, hue=hue, value=spec)
    if isinstance(spec, (tuple, list)) and len(spec) == 2:
        lower, upper = spec
        return [
            _pivot_grouped_values(df, x=x, hue=hue, value=lower),
            _pivot_grouped_values(df, x=x, hue=hue, value=upper),
        ]
    raise ValueError("Error ranges must be a column name or a two-column (lower, upper) pair")


# @id CODE-AIDS-113
# @implements REQ-AIDS-086
# @design DES-AIDS-074
def _plot_with_hue(
    df: pd.DataFrame,
    *,
    kind: str,
    x: str | None,
    y: str | None,
    hue: str,
    ax,
    xerr: list[float] | list[list[float]] | None,
    yerr: list[float] | list[list[float]] | None,
) -> None:
    _require_columns(df, hue)
    if kind == "scatter":
        _require_columns(df, x, y)
        for label, group in df.groupby(hue, sort=False, dropna=False):
            ax.errorbar(
                group[x],
                group[y],
                xerr=_resolve_error_values(group, xerr),
                yerr=_resolve_error_values(group, yerr),
                fmt="o",
                linestyle="none",
                label=_group_label(label),
            )
        ax.legend()
    elif kind == "line":
        _require_columns(df, y)
        if y is None:
            raise ValueError("Line charts with hue require a y column")
        for label, group in df.groupby(hue, sort=False, dropna=False):
            x_values = group[x] if x is not None else group.index
            ax.errorbar(
                x_values,
                group[y],
                xerr=_resolve_error_values(group, xerr),
                yerr=_resolve_error_values(group, yerr),
                fmt="-",
                label=_group_label(label),
            )
        ax.legend()
        if x is not None:
            ax.set_xlabel(x)
        if y is not None:
            ax.set_ylabel(y)
    elif kind == "hist":
        _require_columns(df, x)
        for label, group in df.groupby(hue, sort=False, dropna=False):
            ax.hist(group[x].dropna(), label=_group_label(label), alpha=0.7)
        ax.legend()
    elif kind in {"bar", "barh"}:
        _require_columns(df, x, y)
        pivot = _pivot_grouped_values(df, x=x, hue=hue, value=y)
        kwargs = {}
        if xerr is not None:
            kwargs["xerr"] = _pivot_error_values(df, x=x, hue=hue, spec=xerr)
        if yerr is not None:
            kwargs["yerr"] = _pivot_error_values(df, x=x, hue=hue, spec=yerr)
        pivot.plot(kind=kind, ax=ax, **kwargs)
    else:
        raise ValueError(f"hue is not supported for chart kind: {kind!r}")


# @id CODE-AIDS-114
# @implements REQ-AIDS-085
# @design DES-AIDS-073
def _plot_box_chart(df: pd.DataFrame, *, x: str | None, y: str | None, ax) -> None:
    if y is None:
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            raise ValueError("Box charts require at least one numeric column")
        values = [numeric[column].dropna().tolist() for column in numeric.columns]
        labels = [str(column) for column in numeric.columns]
    elif x is None:
        _require_columns(df, y)
        values = [df[y].dropna().tolist()]
        labels = [str(y)]
        ax.set_ylabel(y)
    else:
        _require_columns(df, x, y)
        values = []
        labels = []
        for label, group in df.groupby(x, sort=False, dropna=False):
            points = group[y].dropna().tolist()
            if not points:
                continue
            values.append(points)
            labels.append(_group_label(label))
        if not values:
            raise ValueError("Box charts require at least one non-empty group")
        ax.set_xlabel(x)
        ax.set_ylabel(y)

    ax.boxplot(values)
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)


# @id CODE-AIDS-115
# @implements REQ-AIDS-085
# @design DES-AIDS-073
def _plot_heatmap(df: pd.DataFrame, *, x: str | None, y: str | None, ax) -> None:
    if x is not None and y is not None:
        _require_columns(df, x, y)
        matrix = df[[x, y]].select_dtypes(include="number").corr()
    else:
        numeric = df.select_dtypes(include="number")
        if (
            not numeric.empty
            and numeric.shape[0] == numeric.shape[1]
            and list(map(str, numeric.index)) == list(map(str, numeric.columns))
        ):
            matrix = numeric
        else:
            matrix = numeric.corr()
    if matrix.empty:
        raise ValueError("Heatmap charts require numeric data")
    image = ax.imshow(matrix.to_numpy(), aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels([str(column) for column in matrix.columns])
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels([str(index) for index in matrix.index])
    fig = ax.figure
    fig.colorbar(image, ax=ax)


def _plot_with_existing_paths(
    df: pd.DataFrame,
    *,
    kind: str,
    x: str | None,
    y: str | None,
    ax,
    xerr: list[float] | list[list[float]] | None,
    yerr: list[float] | list[list[float]] | None,
) -> None:
    if kind == "hist":
        if xerr is not None or yerr is not None:
            raise ValueError("Histogram charts do not support error ranges")
        _require_columns(df, x)
        df[x].plot(kind="hist", ax=ax)
        return

    if kind == "scatter":
        if xerr is None and yerr is None:
            df.plot(kind="scatter", x=x, y=y, ax=ax)
            return
        _require_columns(df, x, y)
        ax.errorbar(df[x], df[y], xerr=xerr, yerr=yerr, fmt="o", linestyle="none")
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        return

    if kind == "line":
        if xerr is None and yerr is None:
            df.plot(kind="line", x=x, y=y, ax=ax)
            return
        if y is None:
            raise ValueError("Line charts require y when error ranges are requested")
        x_values = df[x] if x is not None else df.index
        ax.errorbar(x_values, df[y], xerr=xerr, yerr=yerr, fmt="-")
        if x is not None:
            ax.set_xlabel(x)
        ax.set_ylabel(y)
        return

    kwargs = {}
    if xerr is not None:
        kwargs["xerr"] = xerr
    if yerr is not None:
        kwargs["yerr"] = yerr
    df.plot(kind=kind, x=x, y=y, ax=ax, **kwargs)


# @id CODE-AIDS-007
# @implements REQ-AIDS-007 REQ-AIDS-058 REQ-AIDS-060 REQ-AIDS-064
# @design DES-AIDS-009 DES-AIDS-048 DES-AIDS-052
# @id CODE-AIDS-118
# @implements REQ-AIDS-085 REQ-AIDS-086 REQ-AIDS-087
# @design DES-AIDS-073 DES-AIDS-074 DES-AIDS-075
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
    hue: str | None = None,
    legend_title: str | None = None,
    xerr: str | tuple[str, str] | list[str] | None = None,
    yerr: str | tuple[str, str] | list[str] | None = None,
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
        _plotted_data_contains_japanese(df, kind, x, y, hue=hue, legend_title=legend_title)
    ):
        _ensure_japanese_font()

    fig, ax = plt.subplots()
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            resolved_xerr = _resolve_error_values(df, xerr)
            resolved_yerr = _resolve_error_values(df, yerr)
            if kind == "box":
                _plot_box_chart(df, x=x, y=y, ax=ax)
            elif kind == "heatmap":
                _plot_heatmap(df, x=x, y=y, ax=ax)
            elif hue is not None:
                _plot_with_hue(
                    df,
                    kind=kind,
                    x=x,
                    y=y,
                    hue=hue,
                    ax=ax,
                    xerr=xerr,
                    yerr=yerr,
                )
            else:
                _plot_with_existing_paths(
                    df,
                    kind=kind,
                    x=x,
                    y=y,
                    ax=ax,
                    xerr=resolved_xerr,
                    yerr=resolved_yerr,
                )
            _apply_legend_title(ax, hue=hue, legend_title=legend_title)
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
            except Exception:  # noqa: BLE001 - backend/projection-specific matplotlib failure
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

        metadata = chart_metadata_from_figure(fig, missing_glyphs=tuple(missing_glyphs))
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
        "legend_title": chart_metadata.legend_title,
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
