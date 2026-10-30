# CHANGE-045: 履歴 scope と移送後の追補検証

## 目的と範囲

CHANGE-042 と同じ全体ゲート復旧依頼に含まれる追補。
実際に確認した歴史的診断の範囲を扱う。
完了した移送記録は保持し、後続の入力変更と検証根拠を照合する。

Requirements: REQ-GATE-RECOVERY-002 REQ-GATE-RECOVERY-003

既存要求の Statement / Acceptance / Constraints は維持する。
補足する実行条件は現在の要求・設計で承認する。
正確な 61 scope 以外の候補、自己申告だけの完了、
未承認の入力変更を拒否する。独自のテスト実行器や SDD CLI は作らない。
元の再現対象 30 テスト、実装、コマンド、実行環境、policy は変更しない。

## 段階と検証

TEST-GATE-RECOVERY-002/003 に対象の回帰ケースを追加する。
要求・設計承認後、両方の実際の Red を記録し、同じテストを保って
最小の実装と Green を記録する。
段階は impact / requirements / design / red / implementation / green / quality。
移送 manifest と receipt は上書きせず、新しい追補を別に保存する。
作業元の環境 inventory は impact 前に採取し、内容 hash を監査記録に固定する。
準備判定は実ファイルから追補を検証し、自己申告の完了 report は拒否する。
候補の抽出や設計承認を waiver 操作の承認には使わない。
操作前に全 scope と理由を示し、nahisaho の明示的な承認を得る。

## 提案時点の状態

要求改訂は承認済みで、設計改訂を提案中である。
本変更の実装と Red / Green、個別の waiver 操作は未実施。
直前の全体 gate では 865 テストが成功し、TDD と実行コマンドは合格したが、
履歴 CHANGE、workflow、release 承認が未充足である。
全体ゲートの合格はまだ主張しない。コミット・push・公開は行わない。

## 初回実装後に確認した追補

初回の 2 件の Red / Green と全段階を記録した。
公開 API の戻り値の修正は REQ-GATE-RECOVERY-003 の追加バッチで検証した。
その後の全体 gate で 865 テストと全 643 TDD サイクルが合格した。
ただし初回の change Red / Green 間の補助関数の lint 修正が、
CHANGE_TEST_CHANGED_AFTER_RED を発生させた。担当 agent の手順上の不備として保持する。
再構成した両ファイルは元の native tests fingerprint と一致し、
test 関数の AST は同一、差分は辞書値取得の lint 修正 2 行だけと確認した。
再構成を当時の保存物とは扱わず、元の段階記録も変更しない。

本件の正確な 1 scope を扱う要求改訂は承認済みで、設計改訂を提案中である。
候補抽出と最終検証で根拠を再確認する拡張は、REQ-GATE-RECOVERY-002 の単独バッチで検証する。
最初の段階、REQ-003 バッチ、Quality 履歴は保持する。
テストファイル全体を Red から change Green まで固定する。
61 件の過去 scope と本件の操作は未承認・未実施であり、全体 gate の合格は未確認である。
