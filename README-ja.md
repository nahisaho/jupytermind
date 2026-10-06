# Jupytermind：AI Scientist Skill Suite — Jupyter MCP Copilot Agent Skills

[English README](README.md)

自然言語(日本語/英語)でJupyter上の科学技術計算を行うGitHub Copilot Agent Skill群です。
Jupyter MCP(Datalayer `jupyter-mcp-server`)経由でのみ分析コードを実行し、
推論によるInsightはすべて根拠となる実行済みセルとともにプロジェクトのnotebookに
記録されます。SDD(`musubix3`)とTDD(pytest)で開発されています。

## 収録スキル

| スキル | 概要 |
| --- | --- |
| `ai-data-scientist` | Jupyter上でのデータの読み込み・クレンジング・探索・分析・可視化・Insight抽出(MVP + ML拡張)。 |
| `ai-chemistry-scientist` | ケモインフォマティクス: 分子記述子計算、ADMETヒューリスティックスクリーニング、QSARモデリング、類似性検索、ドッキングスコア、薬物らしさ・構造アラートスクリーニング、分子式・質量計算、SMILES標準化・フォーマット変換。 |
| `ai-genomics-scientist` | ゲノミクス: 配列特徴量解析、バリアント効果ヒューリスティック注釈、スプライス部位強度スコアリング、遺伝子セットエンリッチメント解析、配列アラインメント。 |
| `ai-materials-scientist` | 材料科学シミュレーション: フェーズフィールド法、分子動力学、古典/速度論的モンテカルロ、結晶塑性、簡易FEMソルバ、簡易2元系CALPHAD状態図。 |
| `ai-structural-biology-scientist` | 構造生物学: 二次構造・疎水性/埋没度ヒューリスティック、タンパク質間ドッキングスコア、RMSDによる構造類似性、残基コンタクトマップ。 |
| `ai-scientist` | 研究プロジェクト全体の伴走: 計画・文献レビュー・実験設計・データ分析・論文執筆・査読・再現性確認・発表。 |
| `tech-writer` | README・設計書/ADR・APIリファレンス・PR説明・リリースノート・マニュアル・コードコメントの構成と推敲を支援。 |
| `japanese-prose` | GiNZAベースの診断(kotonoha)による日本語文章品質向上。 |
| `presentation-planner` | PPTXの構成・デザイン方針の立案(ファイル自体の生成は行わない)。 |
| `sdd-*`(`sdd-change`、`sdd-requirements`、`sdd-design`、`sdd-implementation`、`sdd-quality`、`sdd-traceability`、`sdd-knowledge`、`sdd-formal-codegraph`、`sdd-issue-report`) | 上記すべてのスキルを開発・進化させるための仕様駆動開発(SDD)ワークフロー(`musubix3`)。 |

各スキルの詳細な起動手順・起動フレーズは `.github/skills/<スキル名>/SKILL.md`
を参照してください。

## セットアップ

npmレジストリから直接インストールできます(このリポジトリをcloneする必要は
ありません):

```sh
npm install jupytermind
npx ai-data-scientist doctor
```

または、このリポジトリをローカルにcloneしている場合:

```sh
npm install
npx ai-data-scientist doctor
```

いずれの場合もPython環境(仮想環境 + 依存パッケージ)はCLIの初回呼び出し時に
自動セットアップされます。

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

## Skills

各スキルの呼び出し手順は `.github/skills/<スキル名>/SKILL.md` を、
正式な要件セットは `.musubix/features/<feature-slug>/requirements.md` を
参照してください。

## ライセンス

MITライセンス — [LICENSE](LICENSE) を参照してください。

## 変更履歴

リリースノートは [CHANGELOG.md](CHANGELOG.md) を参照してください。
