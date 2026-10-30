# CHANGE-046: 追補検証の trace 正規化

## 目的と範囲

全体ゲート復旧の実環境検証で見つかった、追補検証の誤判定を修正する。
CLI が保存する trace と公開 API が返す trace は、配列の順序が異なる。
現在の比較処理はこの違いを意味内容の不一致として拒否する。
公開 API の正規化を使い、順序だけの違いと実際の内容変更を区別する。

Requirements: REQ-GATE-RECOVERY-003

元の Statement / Acceptance / Constraints は維持する。
CHANGE-045 の完了済み段階を再記録せず、新しい変更として修正根拠を残す。
追補の許可対象に本書を加え、本変更の全段階と Red / Green も照合する。
元の移送 manifest、receipt、再現 artifact、ledger の既存 payload は変更しない。
要求・設計の改訂承認前に実装や Red を始めない。

## 段階と検証

TEST-GATE-RECOVERY-003 に順序だけが異なる trace と内容が異なる trace の回帰ケースを加える。
実際の Red 後、テストファイルを固定したまま修正と Green を記録する。
新しい Green と現在の実装・テストの一致を追補で確認する。
CHANGE-045 の全段階、2 つの追加バッチ、元の Quality 履歴は保持する。
段階は impact / requirements / design / red / implementation / green / quality。
実環境の追補検証と全体 gate を実行し、承認待ちと準備完了を区別する。

## 着手時点の状態

直前の全体 gate は 865 テスト、644 TDD サイクル、756/756 テスト ID が合格した。
承認された履歴 waiver 61 件の記録後、change-history と change-completeness も合格した。
ただし追補検証は trace の比較で失敗しており、全体の準備完了は未確認である。
コミット・push・公開は行わない。
