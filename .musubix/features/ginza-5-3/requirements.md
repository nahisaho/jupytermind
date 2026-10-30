---
schemaVersion: 1
feature: ginza-5-3
---
# Requirements / GiNZA 5.3 対応要求

GiNZA 5.3 に依存宣言をそろえ、既存の日本語解析を検証する。
新機能追加、公開操作、無関係な依存パッケージの更新は対象外とする。
ユーザーが許可した既存のロック不整合の最小修復も含める。
既存の REQ-AIDS-023 の API と出力契約は変更しない。

## REQ-GINZA53-001: プロジェクト依存関係
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: システムはプロジェクトの依存宣言とロックファイルで GiNZA 5.3 を使用しなければならない。
Acceptance: `pyproject.toml` が `ginza>=5.3`、`ja-ginza>=5.3`、`spacy>=3.8.16,<4` を宣言する。`uv lock` で再生成した `uv.lock` の差分は、この 3 パッケージの直接依存メタデータの specifier と、宣言済みだが未ロックの `sympy>=1.12` およびその必要依存を反映する最小修復に限定する。GiNZA と ja-ginza は 5.3.0、spaCy は既存の 3.8.16 を保持し、`uv lock --check` が成功する。Python のサポート下限は既存の 3.10 を保持し、既存の解決済みパッケージのバージョンを変更しない。

## REQ-GINZA53-002: 単体実行スクリプトの依存関係
Priority: must
Type: non-functional
Pattern: ubiquitous
Statement: システムは日本語文章診断の単体実行スクリプトで GiNZA 5.3 系を使用しなければならない。
Acceptance: `.github/skills/japanese-prose/scripts/` の `lint.py`、`terms.py`、`test_engine.py` の PEP 723 メタデータが、すべて `ginza>=5.3.0,<5.4`、`ja-ginza>=5.3.0,<5.4`、`spacy>=3.8.16,<4` を宣言する。各スクリプトを `uv run --script` で実行して依存解決と起動が成功する。`NOTICE.md` の対象バージョンを 5.3.x に更新する。
Constraints: 単体実行スクリプトは検証済みの 5.3 系に制限する。プロジェクト側は既存の下限制約の方針を継続し、`uv.lock` で検証対象の解決済みバージョンを固定する。

## REQ-GINZA53-003: 既存の日本語解析との互換性
Priority: must
Type: functional
Pattern: event-driven
Statement: GiNZA 5.3 環境で日本語解析を実行するとき、システムは既存の解析 API と文章診断の出力契約を維持しなければならない。
Acceptance: `tests/test_japanese_nlp.py` が成功し、`analyze_japanese_text("今日は良い天気です。", operation="tokenize")` のトークンと品詞が `spacy.load("ja_ginza")` の出力と一致し、既存の `JapaneseNLPResult` を返す。`uv run --script .github/skills/japanese-prose/scripts/test_engine.py` の既存 8 テストが GiNZA / ja-ginza 5.3.0 で成功する。`lint.py` と `terms.py` をそれぞれ `uv run --script` と `--json` で `scripts/fixtures/natural.md` と `scripts/fixtures/unnatural.md` に対して実行する。lint のトップレベルキーは `file, engine, model, genre, mode, score, finding_count, findings`、terms は `file, engine, term_count, terms` を保持する。キー欠落や既存テストの失敗を不合格とする。診断件数、数値、分割の旧モデルとの完全一致は要求しない。5.2 系と 5.3 系のフィクスチャ診断件数・スコア・カテゴリの比較を CHANGE-041 の検証結果に記録する。プロジェクトの全 pytest テストも成功する。
