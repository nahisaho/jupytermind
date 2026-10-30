# CHANGE-043: 既存要求の現在の再検証バッチ

## 位置付け

CHANGE-042 と同じ「全体ゲートを通す」依頼に含まれる検証根拠の修復。
新しい機能仕様を作らず、既存契約の証拠不備を修復する。
規範要求の Statement / Acceptance は変更しない。
当時の開発順序や当時の実行を復元したとは主張しない。

Requirements: REQ-ACHEM-100 REQ-AIDS-021 REQ-AIDS-056 REQ-AIDS-082 REQ-AIDS-110 REQ-AIMS-002 REQ-AIMS-003 REQ-AIMS-004 REQ-AIMS-010 REQ-AIMS-040 REQ-AISCI-025 REQ-RELGATE-001 REQ-RELGATE-002 REQ-RELGATE-003 REQ-RELGATE-004 REQ-RELGATE-005 REQ-TECHWRITER-001

上記は既存要求の再検証対象であり、新規または変更された機能契約の一覧ではない。
新規の復旧要求は CHANGE-042 の REQ-GATE-RECOVERY-001/002/003。
今回の要求・設計承認を用い、以前の承認を流用しない。
REQ-AIDS-082 は TEST-AIDS-021 の既存ラベル検証を正しく対応付ける対象。
REQ-AIDS-021 は別の TEST-AIDS-215 で本来の重要度計算を検証する。
材料系の TEST-AIMS-949/950 は REQ-AIMS-004、
TEST-AIMS-980 は REQ-AIMS-010、TEST-AIMS-981 は REQ-AIMS-003 に対応付ける。
古い cycle の誤った REQ-AIMS-002 対応を流用しない。
Git 再現の対象サイクルには archive / void を使わない。
REQ-AISCI-024 は既存の TEST-AISCI-035 で直接検証されている。
TEST-AISCI-024 の古い静的チェックの退役は、固定点前の個別承認付き操作とし、
この Git 再現バッチの新しい Red / Green には数えない。
同様に REQ-AIDS-093 は TEST-AIDS-331 の既存の直接検証を維持する。
TEST-AIDS-340 は既存フォールバックを検証し、修正前でも成功した。
指定 1 サイクルの退役は、固定点前に別途個別承認を得る操作とする。
この要求・テストは本バッチの Git 再現対象から外し、
残る 17 要求・30 テストを 13 batch で再現する。

## 実行契約

`.musubix/features/full-gate-recovery/design.md` の初期対象表に従う。
隔離環境の過去入力と現在入力を使い、現在の正規 CLI 操作として
impact / requirements / design / Red / implementation / Green / quality を記録する。
段階を後から過去の時刻へ置き換えない。
すべての実装・テストを作業元と一致する現在版へ戻した後だけ生成物を移送する。
予想外の失敗や不一致があれば停止する。

## 状態

以下の段落は TEST-AISCI-024 の例外を含む設計改訂を提案した時点の状態。
要求改訂は承認済み。設計改訂を提案中。
現在のバッチに対する段階記録・Red / Green は未実行。
実験用 CHANGE-9998 / 9999 の生成物は本番に移送しない。
コミット・push・公開は行わない。

TEST-AIDS-340 の追加例外を提案する現在、以前の設計と
TEST-AISCI-024 の個別操作は承認・実施済みである。
本番の隔離コピーでは 18 要求の impact / requirements / design と、
説明可能性・感度分析の 14 組の Red / Green を記録した。
続く TEST-AIDS-340 は修正前でも成功し、無効な Red を記録して停止した。
この隔離コピーは監査用に保持し、成功した部分も取り込まない。
作業元にはこの隔離実行の段階記録や TDD を移送していない。
現在は追加例外の要求改訂が承認済みで、設計改訂を提案中である。
設計改訂と別の個別操作の承認後、新しい固定点で全対象を再現する。

履歴 scope の追補を提案する現在、指定した TEST-AIDS-340 の退役は
個別承認後に実施し、全記録の保持を確認した。
新しい固定点の CHANGE-043-run-003 では 17 要求・30 テスト・13 batch の
正規の全段階と Red / Green を完了し、native TDD 検証が合格した。
全固定入力の byte 列と既存 prefix を照合し、
3 ledger と 301 個の監査 artifact を排他的に移送した。
旧コピーの成功部分や無効な試行は監査用に残し、取り込んでいない。
この完了記録は後続修正のために改変せず、CHANGE-045 の追補とは区別する。
現在の TDD は全 640 サイクルで合格しているが、全体 gate はまだ未完了である。
