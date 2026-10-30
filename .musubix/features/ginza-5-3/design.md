---
schemaVersion: 1
feature: ginza-5-3
---
# Design / GiNZA 5.3 対応設計

承認済み要求を依存宣言の更新と回帰検証で実現する。
解析処理や CLI のインターフェースは変更しない。
GiNZA を解析基盤とする既存判断 ADR-0006 を継続する。

## DES-GINZA53-001: プロジェクト依存宣言
Responsibilities: `pyproject.toml` の GiNZA / ja-ginza の下限を 5.3、spaCy を `>=3.8.16,<4` に更新する。`uv lock` で直接依存メタデータを更新し、宣言済みだが欠落している sympy とその必要依存をロックへ反映する。
Interfaces: `uv sync --frozen --extra dev`、`uv lock --check`、既存のパッケージインストール経路。
Constraints: 解決済みパッケージのバージョンを更新しない。ロック差分は対象 3 specifier と sympy の最小修復だけにする。テストでは既存の `get_dependency_specifier` と `packaging.requirements.Requirement` を再利用する。5.2 系と古い spaCy の拒否、5.3.0 と 3.8.16 の許容を確認する。依存定義そのものを正本とする。TOML は trace scanner の対象外のため、実際にその宣言をインストールする `bin/ai-data-scientist.js` の `ensureSetup` に追跡注釈を置く。バージョン制約の証拠はあくまで pyproject とロックの検査結果であり、このリンクだけでは証明しない。代替実装は作らない。
Requirements: REQ-GINZA53-001
ADRs: ADR-0006
Depends-On: none

## DES-GINZA53-002: 単体実行スクリプト
Responsibilities: `lint.py`、`terms.py`、`test_engine.py` の PEP 723 宣言を GiNZA / ja-ginza `>=5.3.0,<5.4` と spaCy `>=3.8.16,<4` に更新する。`NOTICE.md` の対象を 5.3.x に改める。
Interfaces: `.github/skills/japanese-prose/scripts/` の各スクリプトを `uv run --script` で実行する。lint / terms の既存オプションと JSON を保持する。
Constraints: スクリプトの解析ロジックを変更しない。メタデータのテストでは 3 ファイルを列挙し、標準ライブラリで依存文字列を読み、`Requirement` で 5.3.0 の許容と 5.2 / 5.4 の拒否を確認する。Python 3.10 にない `tomllib` には依存しない。プロジェクトと単体実行の依存範囲の違いは要求どおり維持する。`.github` 配下の Python も scanner の対象であることを CLI 実装で確認済み。追跡注釈は各スクリプトの依存メタデータ直前に置く。
Requirements: REQ-GINZA53-002
ADRs: ADR-0006
Depends-On: none

## DES-GINZA53-003: 解析互換性の検証
Responsibilities: `tests/test_japanese_nlp.py` で NLP の既存契約と 5.3 系の実行環境を検証する。文章診断の 8 テストと両フィクスチャの CLI 出力を検証する。
Interfaces: `analyze_japanese_text`、`JapaneseNLPResult`、`test_engine.py`、`lint.py`、`terms.py` の既存インターフェース。
Constraints: 新規の回帰テストでは、5.3 で検証しても他のバージョンが単体実行に選ばれる不整合を検出する。そのため各スクリプトの依存範囲が実行中の 5.3.0 と整合し、5.2 を拒否することも検査する。その後に実際のモデルで既存 NLP 契約を検証する。既存の比較テストは保持する。実装の追跡注釈は既存の `analyze_japanese_text` に追加する。文章診断の 8 テストと両フィクスチャの CLI JSON キー確認は pytest とは別のコマンド根拠として実行し、5.2 / 5.3 の件数・スコア・カテゴリを CHANGE-041 に記録する。モデル差分を理由に既存のテストを弱めない。
Requirements: REQ-GINZA53-003
ADRs: ADR-0006
Depends-On: DES-GINZA53-001, DES-GINZA53-002

## 検証手順

新規テストは既存の依存テストと NLP テストに追加する。
各要求に `TEST-GINZA53-*` と `@verifies` を付ける。
既存の `test` コマンドの pytest adapter をそのまま使用する。
CLI 実装で ID のハイフンをアンダースコアへ変換する既定選択を確認した。
関数名を `test_TEST_GINZA53_001` などとし、対象だけの Red / Green を記録する。
`tddArgs` は追加せず、全体実行の `args: []` も変更しない。
ロック再生成・差分確認・`uv lock --check` は別のコマンド根拠として記録する。
設定済みの format、test、performance コマンドと trace / graph ゲートを実行する。
形式モデルで証明する状態遷移はなく、依存バージョンは実行検証を根拠とする。

## 設計前の隔離検証

`uv run --no-project --with ginza==5.3.0 --with ja-ginza==5.3.0
--with spacy==3.8.16 python ...` で一時環境を構成した。
既存の文章診断 8 テストは 5.2 系と 5.3.0 の両方で成功した。
5.3.0 の `analyze_japanese_text` は実モデルと一致した。
返却例はトークン `今日 / は / 良い / 天気 / です / 。`、
品詞 `NOUN / ADP / ADJ / NOUN / AUX / PUNCT`。
対象 CLI のフィクスチャ比較用 JSON はセッション作業領域に保存した。
比較結果は CHANGE-041 に表とカテゴリ一覧で永続化した。
コマンドの形は `uv run --script <lint.py または terms.py> <fixture> --json`、
診断テストは `uv run --script <test_engine.py>` とする。

## 代替案

ロックファイルだけを更新する案は採用しない。既に 5.3.0 であり、
単体実行スクリプトの `<5.3` 制約を解消できないため。
解析アルゴリズムやモデル名の変更も不要であり、既存 API を維持する。
