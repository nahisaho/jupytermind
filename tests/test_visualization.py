"""Tests for visualization generation (REQ-AIDS-007)."""

import io
import struct
from pathlib import Path

import matplotlib.pyplot as plt
import nbformat
import pandas as pd

from ai_data_scientist.project_manager import enqueue_write, ensure_notebook, resolve_project
from ai_data_scientist.visualization import build_image_output, record_chart, render_chart


def _png_dimensions(png_bytes: bytes) -> tuple[int, int]:
    """Parse (width, height) in pixels from a PNG's IHDR chunk."""
    width, height = struct.unpack(">II", png_bytes[16:24])
    return width, height


# @id TEST-AIDS-007
# @verifies REQ-AIDS-007
def test_TEST_AIDS_007(tmp_path):
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})

    png_bytes = render_chart(df, kind="scatter", x="x", y="y")
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    output = build_image_output(png_bytes)
    assert output["output_type"] == "execute_result"
    assert "image/png" in output["data"]

    handle = resolve_project("viz-project", projects_root=tmp_path)
    ensure_notebook(handle)

    def add_cell(nb):
        import nbformat

        cell = nbformat.v4.new_code_cell("render_chart(...)")
        cell["outputs"] = [output]
        nb.cells.append(cell)

    enqueue_write(handle, add_cell)

    import nbformat

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    assert "image/png" in notebook.cells[0]["outputs"][0]["data"]


# @id TEST-AIDS-039
# @verifies REQ-AIDS-007
def test_TEST_AIDS_039_record_chart_persists_output_with_execution_count(tmp_path):
    from ai_data_scientist.visualization import record_chart

    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})
    png_bytes = render_chart(df, kind="scatter", x="x", y="y")

    handle = resolve_project("chart-record-project", projects_root=tmp_path)
    ensure_notebook(handle)

    execution_count = record_chart(
        handle, "render_chart(df, kind='scatter', x='x', y='y')", png_bytes
    )

    assert execution_count == 1
    notebook = nbformat.read(handle.notebook_path, as_version=4)
    cell = notebook.cells[0]
    assert cell["execution_count"] == 1
    assert "image/png" in cell["outputs"][0]["data"]
    assert cell["outputs"][0]["execution_count"] == 1


# @id TEST-AIDS-049
# @verifies REQ-AIDS-040
def test_TEST_AIDS_049_documents_kernel_consistency_contract():
    import inspect

    from ai_data_scientist import visualization

    doc = inspect.getdoc(visualization.record_chart) or ""
    assert "never executed against" in doc or "not executed against" in doc

    skill_path = (
        Path(__file__).resolve().parent.parent
        / ".github"
        / "skills"
        / "ai-data-scientist"
        / "SKILL.md"
    )
    skill_text = skill_path.read_text(encoding="utf-8")
    assert "never execute the stored code string against the live" in skill_text


# @id TEST-AIDS-064
# @verifies REQ-AIDS-046
def test_TEST_AIDS_064_ascii_title_labels_render_without_font_switch(monkeypatch):
    from ai_data_scientist import visualization

    monkeypatch.setattr(visualization, "_japanese_font_applied", False)
    original_family = list(plt.rcParams["font.family"])
    try:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})
        png_bytes = render_chart(
            df, kind="scatter", x="x", y="y", title="Growth", xlabel="X axis", ylabel="Y axis"
        )
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        assert plt.rcParams["font.family"] == original_family
        assert visualization._japanese_font_applied is False
    finally:
        plt.rcParams["font.family"] = original_family


# @id TEST-AIDS-065
# @verifies REQ-AIDS-046
def test_TEST_AIDS_065_japanese_title_uses_bundled_font(monkeypatch):
    from ai_data_scientist import visualization

    monkeypatch.setattr(visualization, "_japanese_font_applied", False)
    original_family = list(plt.rcParams["font.family"])
    try:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})

        png_bytes = render_chart(
            df, kind="scatter", x="x", y="y", title="売上推移", xlabel="月", ylabel="金額"
        )
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        assert plt.rcParams["font.family"] == ["IPAexGothic"]
        assert visualization._japanese_font_applied is True

        # Calling again with Japanese text must stay idempotent (no error,
        # font family unchanged on the second call).
        png_bytes_2 = render_chart(df, kind="scatter", x="x", y="y", title="第2四半期")
        assert png_bytes_2[:8] == b"\x89PNG\r\n\x1a\n"
        assert plt.rcParams["font.family"] == ["IPAexGothic"]
    finally:
        plt.rcParams["font.family"] = original_family


# @id TEST-AIDS-107
# @verifies REQ-AIDS-046
def test_TEST_AIDS_107_font_survives_global_rcparams_reset_between_calls(monkeypatch):
    """GitHub #32: if a caller resets matplotlib's global rcParams (e.g.
    plt.rcdefaults()) between render_chart calls, a later call requesting
    Japanese text must still render with the bundled Japanese font instead
    of silently reverting to a default font producing "tofu" boxes."""
    from ai_data_scientist import visualization

    monkeypatch.setattr(visualization, "_japanese_font_applied", False)
    original_family = list(plt.rcParams["font.family"])
    try:
        df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})

        png_bytes = render_chart(df, kind="scatter", x="x", y="y", title="第1四半期")
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        assert plt.rcParams["font.family"] == ["IPAexGothic"]

        # Simulate an external caller resetting matplotlib global state
        # (the already-imported japanize_matplotlib font registration is
        # unaffected, but font.family itself reverts to the default).
        plt.rcdefaults()
        assert plt.rcParams["font.family"] != ["IPAexGothic"]

        png_bytes_2 = render_chart(df, kind="scatter", x="x", y="y", title="第2四半期")
        assert png_bytes_2[:8] == b"\x89PNG\r\n\x1a\n"
        assert plt.rcParams["font.family"] == ["IPAexGothic"]
    finally:
        plt.rcParams["font.family"] = original_family


# @id TEST-AIDS-111
# @verifies REQ-AIDS-058
def test_TEST_AIDS_111_long_axis_labels_are_not_clipped(monkeypatch):
    """GitHub #31: a long title/axis-label/tick-label must be repositioned to
    fit entirely within the saved canvas, not clipped at the figure edge."""
    closed_figures = []
    original_close = plt.close

    def _capture_close(fig=None):
        if fig is not None:
            closed_figures.append(fig)
        # Defer the actual close so the test can still inspect the figure.

    monkeypatch.setattr(plt, "close", _capture_close)

    df = pd.DataFrame(
        {
            "a_very_long_category_name_for_the_x_axis": [1, 2, 3],
            "a_very_long_measurement_name_for_the_y_axis": [10, 400, 90],
        }
    )
    long_title = "An Extremely Long Chart Title That Would Normally Overflow The Figure Canvas"
    long_xlabel = "A Very Long X-Axis Label Describing The Independent Variable In Detail"
    long_ylabel = "A Very Long Y-Axis Label Describing The Dependent Variable In Great Detail"

    try:
        png_bytes = render_chart(
            df,
            kind="line",
            x="a_very_long_category_name_for_the_x_axis",
            y="a_very_long_measurement_name_for_the_y_axis",
            title=long_title,
            xlabel=long_xlabel,
            ylabel=long_ylabel,
        )
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(closed_figures) == 1
        fig = closed_figures[0]

        # Compare against the *actual saved* PNG canvas (which bbox_inches=
        # "tight" resizes to fit all content, per DES-AIDS-046), not the
        # figure's original, un-tightened nominal size — otherwise this
        # assertion would pass trivially even without the fix.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        dpi = fig.dpi
        pad_inches = 0.1  # matplotlib's savefig(bbox_inches="tight") default
        tight_bbox = fig.get_tightbbox(renderer)
        origin_x = (tight_bbox.x0 - pad_inches) * dpi
        origin_y = (tight_bbox.y0 - pad_inches) * dpi

        actual_width_px, actual_height_px = _png_dimensions(png_bytes)

        text_artists = [fig._suptitle] if fig._suptitle is not None else []
        for ax in fig.axes:
            text_artists.extend([ax.title, ax.xaxis.label, ax.yaxis.label])
            text_artists.extend(ax.get_xticklabels())
            text_artists.extend(ax.get_yticklabels())

        tolerance = 2.0  # pixels, for DPI/pad rounding
        for artist in text_artists:
            if not artist.get_text():
                continue
            bbox = artist.get_window_extent(renderer=renderer)
            local_x0 = bbox.x0 - origin_x
            local_y0 = bbox.y0 - origin_y
            local_x1 = bbox.x1 - origin_x
            local_y1 = bbox.y1 - origin_y
            assert local_x0 >= -tolerance, f"{artist.get_text()!r} clipped at left edge"
            assert local_y0 >= -tolerance, f"{artist.get_text()!r} clipped at bottom edge"
            assert local_x1 <= actual_width_px + tolerance, (
                f"{artist.get_text()!r} clipped at right edge: "
                f"{local_x1} vs saved width {actual_width_px}"
            )
            assert local_y1 <= actual_height_px + tolerance, (
                f"{artist.get_text()!r} clipped at top edge: "
                f"{local_y1} vs saved height {actual_height_px}"
            )
    finally:
        monkeypatch.setattr(plt, "close", original_close)
        for fig in closed_figures:
            original_close(fig)


# @id TEST-AIDS-113
# @verifies REQ-AIDS-060
def test_TEST_AIDS_113_render_chart_returns_rendered_chart_with_metadata():
    from ai_data_scientist.visualization import RenderedChart

    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})

    result = render_chart(df, kind="scatter", x="x", y="y", title="Growth", ylabel="Count")

    assert isinstance(result, RenderedChart)
    assert isinstance(result, bytes)
    assert result[:8] == b"\x89PNG\r\n\x1a\n"
    assert result.title == "Growth"
    assert result.xlabel == "x"  # pandas auto-generates the x-axis label
    assert result.ylabel == "Count"
    assert result.legend is False
    assert result.missing_glyphs == ()

    # Ordinary bytes operations (base64, equality, slicing) still work since
    # RenderedChart is-a bytes.
    import base64

    assert base64.b64encode(result)
    assert result == bytes(result)


# @id TEST-AIDS-114
# @verifies REQ-AIDS-060
def test_TEST_AIDS_114_render_chart_reports_legend_and_missing_glyphs():
    from ai_data_scientist.visualization import RenderedChart

    df = pd.DataFrame({"x": [1, 2, 3], "a": [1, 4, 9], "b": [2, 3, 5]})

    # Two y columns with x set implicitly draws a legend (pandas default).
    result = render_chart(df, kind="line", x="x", y=None)

    assert isinstance(result, RenderedChart)
    assert result.legend is True
    assert result.missing_glyphs == ()


# @id TEST-AIDS-115
# @verifies REQ-AIDS-061
def test_TEST_AIDS_115_record_chart_persists_chart_metadata(tmp_path):
    df = pd.DataFrame({"x": [1, 2, 3], "y": [1, 4, 9]})
    result = render_chart(df, kind="scatter", x="x", y="y", title="Growth")

    handle = resolve_project("chart-metadata-project", projects_root=tmp_path)
    ensure_notebook(handle)

    record_chart(handle, "render_chart(...)", result)

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    chart_metadata = notebook.cells[0]["metadata"]["chart"]
    assert chart_metadata["title"] == "Growth"
    assert chart_metadata["xlabel"] == "x"
    assert chart_metadata["ylabel"] == "y"
    assert chart_metadata["legend"] is False
    assert list(chart_metadata["missing_glyphs"]) == []

    # Plain bytes (not a render_chart result) must leave metadata["chart"]
    # unset, preserving notebook_audit existing "unaudited" finding.
    plain_png_bytes = bytes(result)
    assert type(plain_png_bytes) is bytes

    plain_handle = resolve_project("chart-metadata-plain-bytes-project", projects_root=tmp_path)
    ensure_notebook(plain_handle)
    record_chart(plain_handle, "render_chart(...)", plain_png_bytes)
    plain_notebook = nbformat.read(plain_handle.notebook_path, as_version=4)
    assert "chart" not in plain_notebook.cells[0]["metadata"]


# @id TEST-AIDS-116
# @verifies REQ-AIDS-061
def test_TEST_AIDS_116_record_chart_persists_legend_true(tmp_path):
    """A RenderedChart whose legend is True (distinct from TEST-AIDS-115's
    legend=False case) must have legend=True persisted into cell metadata."""
    df = pd.DataFrame({"x": [1, 2, 3], "a": [1, 4, 9], "b": [2, 3, 5]})
    result = render_chart(df, kind="line", x="x", y=None)
    assert result.legend is True

    handle = resolve_project("chart-metadata-legend-project", projects_root=tmp_path)
    ensure_notebook(handle)

    record_chart(handle, "render_chart(...)", result)

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    chart_metadata = notebook.cells[0]["metadata"]["chart"]
    assert chart_metadata["legend"] is True


# @id TEST-AIDS-127
# @verifies REQ-AIDS-064
def test_TEST_AIDS_127_tick_label_legend_only_japanese_uses_bundled_font(monkeypatch):
    """ASCII title/xlabel/ylabel, but a categorical column plotted as tick
    labels/legend entries contains Japanese text: the bundled font must still
    be applied, and no "missing glyph" warnings should occur (REQ-AIDS-064)."""
    from ai_data_scientist import visualization
    from ai_data_scientist.visualization import RenderedChart

    monkeypatch.setattr(visualization, "_japanese_font_applied", False)
    original_family = list(plt.rcParams["font.family"])
    try:
        df = pd.DataFrame({"category": ["東京", "大阪", "名古屋"], "value": [10, 20, 15]})

        result = render_chart(
            df, kind="bar", x="category", y="value", title="Sales", xlabel="City", ylabel="Count"
        )

        assert isinstance(result, RenderedChart)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        assert plt.rcParams["font.family"] == ["IPAexGothic"]
        assert visualization._japanese_font_applied is True
        assert result.missing_glyphs == ()
    finally:
        plt.rcParams["font.family"] = original_family


# @id TEST-AIDS-144
# @verifies REQ-AIDS-071
def test_TEST_AIDS_144_build_image_output_persists_output_level_chart_metadata():
    """GitHub #40: build_image_output should persist the rendered chart's
    metadata on the output itself, not only via record_chart's cell-level
    metadata, so a single image output is independently auditable."""
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})
    rendered = render_chart(df, kind="scatter", x="x", y="y", title="T", xlabel="X", ylabel="Y")

    output = build_image_output(rendered)

    assert output["metadata"]["chart"]["title"] == "T"
    assert output["metadata"]["chart"]["xlabel"] == "X"
    assert output["metadata"]["chart"]["ylabel"] == "Y"
    assert "legend" in output["metadata"]["chart"]
    assert "missing_glyphs" in output["metadata"]["chart"]


# @id TEST-AIDS-145
# @verifies REQ-AIDS-071
def test_TEST_AIDS_145_build_image_output_plain_bytes_has_no_chart_metadata():
    df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]})
    rendered = render_chart(df, kind="scatter", x="x", y="y")
    plain_bytes = bytes(rendered)

    output = build_image_output(plain_bytes)

    assert "chart" not in output.get("metadata", {})


# @id TEST-AIDS-195
# @verifies REQ-AIDS-085
def test_TEST_AIDS_195_render_chart_supports_box_barh_and_heatmap(monkeypatch):
    closed_figures = []
    original_close = plt.close

    def _capture_close(fig=None):
        if fig is not None:
            closed_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)
    try:
        box_df = pd.DataFrame({"group": ["A", "A", "B", "B"], "value": [1.0, 3.0, 2.0, 4.0]})
        box_result = render_chart(box_df, kind="box", x="group", y="value")
        assert box_result[:8] == b"\x89PNG\r\n\x1a\n"
        assert box_result.xlabel == "group"
        assert box_result.ylabel == "value"

        barh_df = pd.DataFrame(
            {
                "label": [
                    "A very long category label for alpha",
                    "An equally long category label for beta",
                ],
                "value": [10, 20],
            }
        )
        barh_result = render_chart(barh_df, kind="barh", x="label", y="value")
        assert barh_result[:8] == b"\x89PNG\r\n\x1a\n"
        assert isinstance(barh_result, bytes)

        heatmap_df = pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6], "z": [0, 1, 0]})
        heatmap_result = render_chart(heatmap_df, kind="heatmap", x="x", y="y")
        assert heatmap_result[:8] == b"\x89PNG\r\n\x1a\n"
        assert heatmap_result.legend is False

        heatmap_figure = closed_figures[-1]
        heatmap_array = heatmap_figure.axes[0].images[0].get_array()
        assert heatmap_array.shape == (2, 2)

        corr_df = heatmap_df[["x", "y"]].corr()
        matrix_result = render_chart(corr_df, kind="heatmap")
        assert matrix_result[:8] == b"\x89PNG\r\n\x1a\n"
        matrix_figure = closed_figures[-1]
        matrix_array = matrix_figure.axes[0].images[0].get_array()
        assert matrix_array.tolist() == corr_df.to_numpy().tolist()
    finally:
        monkeypatch.setattr(plt, "close", original_close)
        for fig in closed_figures:
            original_close(fig)


# @id TEST-AIDS-196
# @verifies REQ-AIDS-086
def test_TEST_AIDS_196_render_chart_scatter_hue_sets_legend_title(monkeypatch):
    closed_figures = []
    original_close = plt.close

    def _capture_close(fig=None):
        if fig is not None:
            closed_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)
    try:
        df = pd.DataFrame(
            {
                "x": [1, 2, 3, 4],
                "y": [10, 12, 8, 9],
                "group": ["A", "A", "B", "B"],
            }
        )

        result = render_chart(
            df,
            kind="scatter",
            x="x",
            y="y",
            hue="group",
            legend_title="Cluster",
        )

        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        assert result.legend is True
        assert result.legend_title == "Cluster"
        assert closed_figures[-1].axes[0].get_legend().get_title().get_text() == "Cluster"

        default_result = render_chart(df, kind="scatter", x="x", y="y", hue="group")
        assert default_result.legend is True
        assert default_result.legend_title == "group"
    finally:
        monkeypatch.setattr(plt, "close", original_close)
        for fig in closed_figures:
            original_close(fig)


# @id TEST-AIDS-197
# @verifies REQ-AIDS-086
def test_TEST_AIDS_197_render_chart_legend_title_overrides_existing_multiseries_legend(
    monkeypatch,
):
    closed_figures = []
    original_close = plt.close

    def _capture_close(fig=None):
        if fig is not None:
            closed_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)
    try:
        df = pd.DataFrame({"x": [1, 2, 3], "a": [1, 4, 9], "b": [2, 3, 5]})

        result = render_chart(df, kind="line", x="x", y=None, legend_title="Series")

        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        assert result.legend is True
        assert result.legend_title == "Series"
        assert closed_figures[-1].axes[0].get_legend().get_title().get_text() == "Series"
    finally:
        monkeypatch.setattr(plt, "close", original_close)
        for fig in closed_figures:
            original_close(fig)


# @id TEST-AIDS-198
# @verifies REQ-AIDS-087
def test_TEST_AIDS_198_render_chart_supports_symmetric_and_asymmetric_error_ranges(
    monkeypatch,
):
    closed_figures = []
    original_close = plt.close

    def _capture_close(fig=None):
        if fig is not None:
            closed_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)
    try:
        bar_df = pd.DataFrame({"x": ["A", "B"], "y": [10, 12], "err": [1.0, 1.5]})
        bar_result = render_chart(bar_df, kind="bar", x="x", y="y", yerr="err")
        assert bar_result[:8] == b"\x89PNG\r\n\x1a\n"
        assert any(
            collection.__class__.__name__ == "LineCollection"
            for collection in closed_figures[-1].axes[0].collections
        )

        barh_df = pd.DataFrame(
            {
                "x": ["A", "B"],
                "y": [10, 12],
                "low": [0.5, 0.75],
                "high": [1.0, 1.25],
            }
        )
        barh_result = render_chart(barh_df, kind="barh", x="x", y="y", xerr=("low", "high"))
        assert barh_result[:8] == b"\x89PNG\r\n\x1a\n"
        assert any(
            collection.__class__.__name__ == "LineCollection"
            for collection in closed_figures[-1].axes[0].collections
        )
    finally:
        monkeypatch.setattr(plt, "close", original_close)
        for fig in closed_figures:
            original_close(fig)


# @id TEST-AIDS-199
# @verifies REQ-AIDS-088
def test_TEST_AIDS_199_chart_metadata_from_figure_supports_auditable_external_figures(
    tmp_path,
):
    from ai_data_scientist.visualization import RenderedChart, chart_metadata_from_figure

    fig, ax = plt.subplots()
    try:
        ax.plot([1, 2, 3], [3, 5, 4], label="Series A")
        ax.set_title("Growth")
        ax.set_xlabel("Quarter")
        ax.set_ylabel("Revenue")
        ax.legend(title="Series")

        metadata = chart_metadata_from_figure(fig)
        assert metadata.title == "Growth"
        assert metadata.xlabel == "Quarter"
        assert metadata.ylabel == "Revenue"
        assert metadata.legend is True
        assert metadata.legend_title == "Series"
        assert metadata.missing_glyphs == ()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png")
        rendered = RenderedChart(buffer.getvalue(), metadata)

        handle = resolve_project("external-chart-metadata-project", projects_root=tmp_path)
        ensure_notebook(handle)
        record_chart(handle, "external matplotlib figure", rendered)

        notebook = nbformat.read(handle.notebook_path, as_version=4)
        chart_metadata = notebook.cells[0]["metadata"]["chart"]
        assert chart_metadata["title"] == "Growth"
        assert chart_metadata["xlabel"] == "Quarter"
        assert chart_metadata["ylabel"] == "Revenue"
        assert chart_metadata["legend"] is True
        assert chart_metadata["legend_title"] == "Series"
        assert chart_metadata["missing_glyphs"] == []
    finally:
        plt.close(fig)


# @id TEST-AIDS-200
# @verifies REQ-AIDS-086 REQ-AIDS-087
def test_TEST_AIDS_200_grouped_bar_chart_supports_hue_and_error_ranges(monkeypatch):
    closed_figures = []
    original_close = plt.close

    def _capture_close(fig=None):
        if fig is not None:
            closed_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)
    try:
        df = pd.DataFrame(
            {
                "category": ["A", "A", "B", "B"],
                "group": ["g1", "g2", "g1", "g2"],
                "mean": [1.0, 1.5, 2.0, 2.5],
                "err": [0.1, 0.2, 0.15, 0.25],
            }
        )

        result = render_chart(
            df,
            kind="bar",
            x="category",
            y="mean",
            hue="group",
            yerr="err",
            legend_title="Group",
        )

        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        assert result.legend is True
        assert result.legend_title == "Group"
        assert any(
            collection.__class__.__name__ == "LineCollection"
            for collection in closed_figures[-1].axes[0].collections
        )
    finally:
        monkeypatch.setattr(plt, "close", original_close)
        for fig in closed_figures:
            original_close(fig)


# @id TEST-AIDS-201
# @verifies REQ-AIDS-086 REQ-AIDS-087
def test_TEST_AIDS_201_grouped_bar_and_barh_preserve_nan_hue_series(monkeypatch):
    closed_figures = []
    original_close = plt.close

    def _capture_close(fig=None):
        if fig is not None:
            closed_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)
    try:
        df = pd.DataFrame(
            {
                "category": ["A", "A", "B", "B"],
                "group": ["g1", None, "g1", None],
                "mean": [1.0, 1.5, 2.0, 2.5],
                "err": [0.1, 0.2, 0.15, 0.25],
            }
        )

        for kind, xerr, yerr in (("bar", None, "err"), ("barh", "err", None)):
            result = render_chart(
                df,
                kind=kind,
                x="category",
                y="mean",
                hue="group",
                xerr=xerr,
                yerr=yerr,
                legend_title="Group",
            )

            assert result[:8] == b"\x89PNG\r\n\x1a\n"
            assert result.legend is True
            assert result.legend_title == "Group"
            labels = closed_figures[-1].axes[0].get_legend_handles_labels()[1]
            assert labels == ["g1", "NaN"]
            assert any(
                collection.__class__.__name__ == "LineCollection"
                for collection in closed_figures[-1].axes[0].collections
            )
    finally:
        monkeypatch.setattr(plt, "close", original_close)
        for fig in closed_figures:
            original_close(fig)


# @id TEST-AIDS-202
# @verifies REQ-AIDS-086 REQ-AIDS-087
def test_TEST_AIDS_202_grouped_bar_duplicate_x_hue_pairs_raise_value_error():
    df = pd.DataFrame(
        {
            "category": ["A", "A"],
            "group": ["g1", "g1"],
            "mean": [1.0, 1.5],
            "err": [0.1, 0.2],
        }
    )

    import pytest

    with pytest.raises(ValueError, match="unique per .*pair"):
        render_chart(df, kind="bar", x="category", y="mean", hue="group", yerr="err")
