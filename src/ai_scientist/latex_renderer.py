"""LaTeX rendering for tech-writer Markdown output."""

from __future__ import annotations

from pathlib import Path


def _escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in text)


# @id CODE-AISCI-022
# @implements REQ-AISCI-022
# @design DES-AISCI-018
def render_latex(markdown_path: Path) -> str:
    """Render a small LaTeX document while preserving section order/content."""
    body_lines: list[str] = []
    for raw_line in markdown_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            body_lines.append("")
        elif line.startswith("# "):
            body_lines.append(f"\\section{{{_escape_latex(line[2:])}}}")
        elif line.startswith("## "):
            body_lines.append(f"\\subsection{{{_escape_latex(line[3:])}}}")
        else:
            body_lines.append(_escape_latex(line))
    content = "\n".join(body_lines).strip()
    return f"\\documentclass{{article}}\n\\begin{{document}}\n{content}\n\\end{{document}}\n"
