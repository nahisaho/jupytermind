# Jupytermind：AI Scientist Skill Suite — Jupyter MCP Copilot Agent Skills

[日本語 README](README-ja.md)

A collection of GitHub Copilot Agent Skills for natural-language (Japanese/
English) scientific computing over Jupyter via the Jupyter MCP (Datalayer
`jupyter-mcp-server`). Every reasoning-based insight is recorded in the
project notebook alongside the executed cell that provides its evidence.
Built with SDD (`musubix3`) and TDD (pytest).

## Skills included

| Skill | Scope |
| --- | --- |
| `ai-data-scientist` | Load, clean, explore, analyze, visualize, and draw insights from datasets via Jupyter (MVP + ML extension). |
| `ai-chemistry-scientist` | Cheminformatics: molecular descriptors, ADMET heuristic screening, QSAR modeling, similarity search, docking-score heuristics, drug-likeness/structural-alert screening, formula/mass calculation, SMILES standardization and format conversion. |
| `ai-genomics-scientist` | Computational genomics: sequence feature analysis, variant-effect heuristic annotation, splice-site strength scoring, gene-set enrichment analysis, pairwise sequence alignment. |
| `ai-materials-scientist` | Materials-science simulation: phase-field microstructure evolution, molecular dynamics, classical/kinetic Monte Carlo, crystal plasticity, a simplified FEM solver, and a simplified binary CALPHAD phase diagram. |
| `ai-structural-biology-scientist` | Structural biology: secondary-structure and hydrophobicity/burial heuristics, protein-protein docking-score heuristics, RMSD-based structural similarity, residue contact-map heuristics. |
| `ai-scientist` | End-to-end single-project research guidance: planning, literature review, experimental design, data analysis, manuscript writing, peer review, reproducibility checks, and presentation. |
| `tech-writer` | Structures and polishes technical documents: READMEs, design docs/ADRs, API references, PR descriptions, release notes, user manuals, code comments. |
| `japanese-prose` | Improves Japanese prose quality using GiNZA-based diagnostics (kotonoha). |
| `presentation-planner` | Plans PPTX content structure and design handoff (does not generate the file itself). |
| `sdd-*` (`sdd-change`, `sdd-requirements`, `sdd-design`, `sdd-implementation`, `sdd-quality`, `sdd-traceability`, `sdd-knowledge`, `sdd-formal-codegraph`, `sdd-issue-report`) | The Specification-Driven-Development workflow (`musubix3`) used to build and evolve every skill above. |

See each skill's `.github/skills/<name>/SKILL.md` for its full invocation
instructions and trigger phrases.

## Setup

Install the skill from the npm registry (no need to clone this repo):

```sh
npm install jupytermind
npx ai-data-scientist doctor
```

Or, for a local checkout of this repo:

```sh
npm install
npx ai-data-scientist doctor
```

The Python environment (virtualenv + dependencies) is set up automatically
on first CLI invocation in both cases.

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

## Skills

See `.github/skills/<skill-name>/SKILL.md` for each skill's invocation
instructions and `.musubix/features/<feature-slug>/requirements.md` for its
authoritative requirement set.

## License

MIT License — see [LICENSE](LICENSE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes.
