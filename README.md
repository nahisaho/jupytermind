# AI Data Scientist — Jupyter MCP Copilot Agent Skill

[日本語 README](README-ja.md)

A GitHub Copilot Agent Skill that performs natural-language (Japanese/
English) data analysis over Jupyter via the Jupyter MCP (Datalayer
`jupyter-mcp-server`). Every reasoning-based insight is recorded in the
project notebook alongside the executed cell that provides its evidence.
Built with SDD (`musubix3`) and TDD (pytest).

## Setup

The Python environment (virtualenv + dependencies) can be set up
automatically via npm:

```sh
npm install
npx ai-data-scientist doctor
```

`npm install` itself has no dependencies and does not use `postinstall`
(since npm v12, install scripts of dependencies are disabled by default
and require `npm approve-scripts`). Instead, `bin/ai-data-scientist.js`
creates a `.venv` and installs the dependencies from `pyproject.toml` on
first CLI invocation. Subsequent invocations are cached and start fast.

To set up the Python environment manually:

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pytest
```

### PDF export prerequisites

`report_export.export_report(..., report_format="pdf")` uses nbconvert's
`PDFExporter`, which shells out to a system `xelatex` binary. This is **not**
installed by `pip`/`npm` and must be provided separately, e.g.:

```sh
# Debian/Ubuntu
sudo apt-get install texlive-xetex texlive-fonts-recommended

# macOS
brew install --cask mactex-no-gui
```

If `xelatex` is not on `PATH`, PDF export raises a `RuntimeError` pointing
back to this section; use `report_format="html"` if you do not need PDF
output.

## Skill

See `.github/skills/ai-data-scientist/SKILL.md` for the skill's invocation
instructions and `.musubix/features/ai-data-scientist*/requirements.md` for
the authoritative requirement set (MVP + ML extension).
