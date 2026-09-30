"""Report export module.

Implements DES-AIDS-024 (REQ-AIDS-025, REQ-AIDS-033, ADR-0007): exports the
current project notebook to PDF, HTML, or slide form using a local
nbconvert-based conversion tool, without invoking any Jupyter MCP
execution call.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import nbformat
from nbconvert import HTMLExporter, PDFExporter, SlidesExporter

from ai_data_scientist.project_manager import ProjectHandle

_SUPPORTED_FORMATS = ("html", "pdf", "slides")
_EXPORTERS = {"html": HTMLExporter, "pdf": PDFExporter, "slides": SlidesExporter}
_EXTENSIONS = {"html": "html", "pdf": "pdf", "slides": "slides.html"}


@dataclass(frozen=True)
class ReportPath:
    path: Path
    format: str


# @id CODE-AIDS-025
# @implements REQ-AIDS-025
# @design DES-AIDS-024
# @id CODE-AIDS-033
# @implements REQ-AIDS-033
# @design DES-AIDS-024
def export_report(
    handle: ProjectHandle, report_format: str = "html", name: str | None = None
) -> ReportPath:
    """Export ``handle``'s notebook to ``report_format`` via nbconvert only.

    Reads the already-executed notebook and renders it with a local
    nbconvert exporter only; no Jupyter MCP client is invoked, satisfying
    REQ-AIDS-033's read-only, non-MCP export boundary.
    """
    if report_format not in _SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported report format: {report_format!r}")

    notebook = nbformat.read(handle.notebook_path, as_version=4)
    exporter = _EXPORTERS[report_format]()
    try:
        body, _resources = exporter.from_notebook_node(notebook)
    except OSError as exc:
        if report_format == "pdf" and "xelatex" in str(exc).lower():
            raise RuntimeError(
                "PDF export requires a system TeX/xelatex installation, which "
                "is not bundled with this package. See the 'PDF export "
                "prerequisites' section of README.md for install instructions, "
                "or use report_format='html' instead."
            ) from exc
        raise

    reports_dir = handle.root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_name = name or handle.name
    extension = _EXTENSIONS[report_format]
    report_path = reports_dir / f"{report_name}.{extension}"

    mode = "wb" if isinstance(body, bytes) else "w"
    encoding = None if isinstance(body, bytes) else "utf-8"
    with report_path.open(mode, encoding=encoding) as fh:
        fh.write(body)

    return ReportPath(path=report_path, format=report_format)
