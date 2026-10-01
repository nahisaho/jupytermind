# AI Data Scientist — Jupyter MCP Copilot Agent Skill

[English README](README.md)

自然言語(日本語/英語)でJupyter上のデータ分析を行うGitHub Copilot Agent Skillです。
Jupyter MCP(Datalayer `jupyter-mcp-server`)経由でのみ分析コードを実行し、
推論によるInsightはすべて根拠となる実行済みセルとともにプロジェクトのnotebookに
記録されます。SDD(`musubix3`)とTDD(pytest)で開発されています。

## セットアップ

Python環境(仮想環境 + 依存パッケージ)はnpm経由で自動セットアップできます:

```sh
npm install
npx ai-data-scientist doctor
```

`npm install` 自体は依存パッケージを持たず、`postinstall` も使用していません
(npm v12以降、依存パッケージの install スクリプトはデフォルトで無効化され
`npm approve-scripts` が必要になるため)。代わりに `bin/ai-data-scientist.js`
が初回のCLI呼び出し時に `.venv` を作成し `pyproject.toml` の依存関係を
インストールします。2回目以降はキャッシュされ高速に起動します。

Python環境を手動でセットアップする場合:

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pytest
```

### PDF出力の前提条件

`report_export.export_report(..., report_format="pdf")` は nbconvert の
`PDFExporter` を使用し、システムの `xelatex` バイナリを呼び出します。これは
`pip`/`npm` ではインストールされないため、別途用意する必要があります:

```sh
# Debian/Ubuntu
sudo apt-get install texlive-xetex texlive-fonts-recommended

# macOS
brew install --cask mactex-no-gui
```

`xelatex` が `PATH` 上に無い場合、PDF出力はこのセクションを案内する
`RuntimeError` を送出します。PDF出力が不要な場合は `report_format="html"`
を使用してください。

## Skill

Skillの呼び出し手順は `.github/skills/ai-data-scientist/SKILL.md` を、
正式な要件セット(MVP + ML拡張)は
`.musubix/features/ai-data-scientist*/requirements.md` を参照してください。
