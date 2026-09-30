# AI Data Scientist — Jupyter MCP Copilot Agent Skill

自然言語(日本語/英語)でJupyter上のデータ分析を行うGitHub Copilot Agent Skillです。
Jupyter MCP(Datalayer `jupyter-mcp-server`)経由でのみ分析コードを実行し、
推論によるInsightはすべて根拠となる実行済みセルとともにプロジェクトのnotebookに
記録されます。SDD(`musubix3`)とTDD(pytest)で開発されています。

A GitHub Copilot Agent Skill that performs natural-language (Japanese/
English) data analysis over Jupyter via the Jupyter MCP (Datalayer
`jupyter-mcp-server`). Every reasoning-based insight is recorded in the
project notebook alongside the executed cell that provides its evidence.
Built with SDD (`musubix3`) and TDD (pytest).

## Setup / セットアップ

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

## Skill

See `.github/skills/ai-data-scientist/SKILL.md` for the skill's invocation
instructions and `.musubix/features/ai-data-scientist*/requirements.md` for
the authoritative requirement set (MVP + ML extension).
