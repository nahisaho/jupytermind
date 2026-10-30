---
schemaVersion: 1
feature: full-gate-recovery
---
# 全体ゲート復旧の設計

要求の承認 hash は
`79ef228d119fa272a41e65a865499a4d1a5207acbb0d6f06c97a0f07268aeb48`。
機能の受け入れ条件や品質ポリシーは変更しない。
保護された証拠の生成には既存の musubix3 0.1.22 を用いる。
検証用関数を `scripts/gate_recovery.py` に追加する。
保護 artifact の移送だけを行う Node 境界を
`scripts/gate_recovery_transport.mjs` に置く。テスト実行器や SDD CLI は作らない。

## DES-GATE-RECOVERY-001: 出所と追記型記録の検証

Responsibilities: 再現の出所と Red / Green の同一条件を検証する。隔離環境との混同と証拠の巻き戻しを拒否し、正規 writer lock 内で CLI artifact を移送・復旧する。
Interfaces: Python の `audit_replay_sources(root, revision, paths) -> dict` は完全な commit ID、HEAD、各 path の存在状態と SHA-256 を返す。`validate_replay_artifacts(base, incoming) -> dict` は prefix と head / sequence を確認する。`build_replay_provenance(red, green) -> dict` は後述の出所レコードを検証する。Node の `planTransport(input) -> manifest`、`applyTransport(manifestPath) -> report`、`recoverTransport(manifestPath) -> report` は後述の固定 manifest と状態規則に従う。
Constraints: commit は HEAD より前の祖先でなければならない。path は root 内の通常ファイルに限定し、外部を指す symlink、絶対パス、親への移動、tests / .musubix / .git / .venv を拒否する。対象は src / scripts / bin、package.json、skill の SKILL.md / manifest.json に限定する。過去版の不在は Git tree で確認し、空ファイルと区別する。全ファイルが不変なら再現指定を拒否する。既存の order / TDD chain の全レコードは同じ順序の prefix として残し、既存サイクルと既存 phase の payload を保持する。不正な入力は例外と診断で明示する。
Requirements: REQ-GATE-RECOVERY-001
ADRs: ADR-0127
Depends-On: none

## DES-GATE-RECOVERY-002: 限定した履歴 waiver の候補抽出

Responsibilities: 実際の構造化診断から許可対象の scope を抽出し、承認可能な候補と人手で調査すべき診断を区別する。
Interfaces: `plan_historical_waivers(gate_report, chronology_context=None) -> dict` は `candidates`、`blocked`、`resolved_stale` を返す。候補の各要素は code / changeId と必要な requirementId または detail を持つ。chronology_context は後述の 1 件にだけ必要な、実ファイルと独立した期待値を指定する context とする。
Constraints: 過去の code と selector は承認済み要求の 6 種類・正確な 61 scope に限定し、欠落を補完しない。追加は後述の CHANGE-045 の 1 scope だけとし、根拠未検証なら blocked とする。順序移行の code は CHANGE-021 の detail=requirement:REQ-ACHEM-100 だけを受理する。候補は現在の error 診断に限定し、両チェックから出る重複を除く。CHANGE_WAIVER_STALE のメッセージだけから記録対象を生成せず、同じ scope の根本診断と照合する。CHANGE_REQUIREMENTS_MISMATCH や許可外 scope は blocked として返す。候補抽出は副作用を持たない。実際の記録は一覧・理由の人間の承認後に、正規の `change waiver record` で行う。
Requirements: REQ-GATE-RECOVERY-002
ADRs: ADR-0127
Depends-On: none

## DES-GATE-RECOVERY-003: 準備状況の判定

Responsibilities: 承認待ちの候補状態と最終準備完了を区別し、欠落や矛盾を合格と扱わない。
Interfaces: `assess_recovery_readiness(gate_report, expected_checks, approval_report, transport_context) -> dict` は `candidate`、`ready`、`blockers` を返す。入力は実際の gate、`approval validate` と移送の実ファイルを指定する context を用いる。`validate_recovery_followup(root, original_manifest, original_receipt, followup, expected_original, chronology_context=None) -> dict` は後述の追補を読み取り専用で検証する。manifest / receipt / followup は実ファイルの path とし、expected_original は独立して固定した transaction ID と manifest hash を持つ。必要な場合は同じ context に chronology_context を加える。assess はこの検証を自身で呼び、成功 report の dict を自己申告する入力は受理しない。
Constraints: expected_checks は空でない一意の名前集合とし、approval を含める。全 expected check と、入力で required=true の全 check を確認する。check 名の重複、未定義 status、必要な check の欠落、全体 status との矛盾を blocker にする。移送の未完了・欠落・現在入力との不一致も blocker とする。候補には requirements / design の現在の承認を要求し、release 承認だけの不足を ready と区別する。ready は gate が pass で、必要な全 check と全承認段階が合格の場合だけ true。実際の最終判断では、さらに同じ入力の `status.gate.ready` を確認する。
Requirements: REQ-GATE-RECOVERY-003
ADRs: ADR-0127
Depends-On: DES-GATE-RECOVERY-001, DES-GATE-RECOVERY-002

`transport_context` は `root`、実ファイルを指す `original_manifest` /
`original_receipt` / `followup`、呼び出し側で固定した `expected_original` を持つ。
assess はこの値を検証用関数へ渡す。
期待する識別子と hash を followup ファイル自身から読み取って代用しない。

## 実行契約と証拠バッチ

CHANGE-042 は上記 3 関数群を通常の Red / Green で実装する。
テストは `tests/test_gate_recovery.py` に置く。
各要求に TEST-GATE-RECOVERY-001 / 002 / 003 を対応付ける。
関数内で実装を import し、未実装時にも対象テストの失敗を観測できるようにする。

既存要求の再検証は CHANGE-043 として区別する。
これは同じユーザー依頼に含まれる証拠の修復バッチであり、
既存要求の Statement / Acceptance を変更しない。
既存の承認を流用せず、今回承認された要求・設計一式を用いる。
段階記録には、実在する過去入力を現在版へ戻す操作を記す。
記録順序は現在の monotonic order とし、歴史的経緯と区別する。

### 失効した宣言範囲の整理

次の 6 テストは、現在の関数末尾までの SHA-256 が保存済み Green と一致した。
関数自体ではなく、後から加わった未注釈の helper が宣言範囲に入っていた。

TEST-AIDS-017、TEST-AIDS-022、TEST-AIDS-034、
TEST-AIDS-112、TEST-AIDS-204、TEST-AISCI-035。

副作用を持たない helper の定義を最初のテスト注釈より前へ移す。
テストの関数名、decorator、assert、入力、helper の実装は変更しない。
全関数の AST と収集結果を比較し、既存の Green fingerprint と
現在の CLI が再計算する fingerprint の一致を確認する。
記録する AST は関数名で対応付けた decorator・引数・本体とし、
位置情報と module 内の helper 配置順だけを比較対象から除く。
各 6 ID の native fingerprint と保存済み Green hash の一致を個別に保存する。
既存テストの node ID 集合と 862 件という収集数は維持する。
新規復旧テストはこの既存集合とは別に数える。
これは既存の有効な根拠の入力を復元する操作であり、新しい TDD 実行とは呼ばない。
他のテストに新たな stale が生じた場合は、そのまま合格とせず調査する。

### 静的チェックの古いサイクルに対する限定例外

この TEST-AISCI-024 の退役は、以前の要求・設計承認と別の個別承認後に
正規 CLI で実施済みである。以下はその実施条件として保持し、再実施しない。
承認・実行記録と退役済みの結果を維持する。

TEST-AISCI-024 は要求書とテスト注釈だけを読む。
実装の過去版だけでは失敗を再現できないため、Git 再現の対象から外す。
テストは残し、最終ゲートでも実行する。
退役対象は次の既存サイクルだけとする。

| 用途 | テスト | cycle ID |
|---|---|---|
| 個別承認後の archive 対象 | TEST-AISCI-024 | `1a91db34-ed68-4b5a-b225-a7cbe99cd316` |
| 変更しない古い未完了記録 | TEST-AISCI-024 | `e8ff006d-e17a-4a43-8f22-63eb4f6901c6` |
| 同じ REQ-AISCI-024 の直接検証 | TEST-AISCI-035 | `0d264714-5c38-498a-9dbc-2b4f4f358849` |

TEST-AISCI-035 は上記の宣言範囲の修復で既存 Green と一致した。
新しい再現サイクルは作らない。
作業元の固定点を取る前に、以下を確認する。

1. 直接検証の cycle が archive されておらず、有効な Red / Green を持つことを native 検証で確認する。現在の宣言 fingerprint と保存済み Green を照合する。
2. TEST-AISCI-024 / 035 を現在版で実行し、両方の成功と実行入力の hash を保存する。古いサイクルを現在の実行と呼ばない。
3. 退役対象の cycle ID、元の phase と chain / 順序ログの hash、代替根拠、理由を提示し、nahisaho の個別承認を得る。要求・設計への承認で代用しない。
4. 実行直前に TEST-AISCI-024 の最新 cycle ID が退役対象と一致することを確認する。一致しなければ停止する。
5. 正規の `tdd archive TEST-AISCI-024 --approver nahisaho --reason <承認された理由> --confirm` を実行する。保護 JSON の手編集や独自 writer は使わない。
6. 元の全サイクルと phase の payload、chain / 順序ログの prefix を照合する。差分は対象の archive marker 1 件、native chain 追記 1 件、順序ログ追記 1 件だけとする。
7. native 検証で退役対象と直接検証の cycle を再確認する。REQ-AISCI-024 の未検証診断や、対象以外の新しい不整合が出れば停止する。

この操作を新しい Red / Green や失敗再現の成功と呼ばない。
他のサイクルの archive、void、現行テストの失敗の除外には使わない。
個別承認や前提の確認が不足していれば実行しない。
実行後の証拠を隔離再現の base とし、移送中に archive marker を追加しない。
したがって、既存サイクルの完全な prefix を照合する移送関数は変更しない。

### 既存フォールバックの未完了サイクルに対する限定例外

TEST-AIDS-340 は、祖先に対象がなければ現在位置の projects を使う動作を確認する。
実在する修正前の Git 版でも成功し、既存の動作を保つテストだった。
隔離再現で観測した成功を Red と扱わず、Git 再現の対象から外す。
テストは残し、最終ゲートでも実行する。
対象と代替の直接検証は次の既存サイクルだけとする。

| 用途 | テスト | cycle ID |
|---|---|---|
| 個別承認後の archive 対象 | TEST-AIDS-340 | `d338d2a4-d6db-45e0-b711-2266228eb5bb` |
| 同じ REQ-AIDS-093 の祖先探索の直接検証 | TEST-AIDS-331 | `33a2818f-da5d-4bbb-b714-08f6bc146cf8` |

要求・設計の改訂承認後、新しい固定点を取る前に作業元で以下を行う。

1. TEST-AIDS-331 の上記 cycle が archive されておらず、有効な Red / Green を持つことを native 検証で確認する。現在の宣言 fingerprint と保存済み Green を照合する。
2. TEST-AIDS-331 / 340 を現在版で実行し、両方の成功と入力の hash を保存する。古い cycle を現在の実行と呼ばない。
3. 対象 cycle ID、元の phase と chain / 順序ログの hash、代替根拠、理由を提示し、nahisaho の個別承認を得る。要求・設計への承認や TEST-AISCI-024 の個別承認で代用しない。
4. 実行直前に TEST-AIDS-340 の最新 cycle ID が上記と一致することを確認する。一致しなければ停止する。
5. 正規の `tdd archive TEST-AIDS-340 --approver nahisaho --reason <承認された理由> --confirm` を実行する。保護 JSON の手編集や独自 writer は使わない。
6. 実行直前の作業元を基準に、全サイクルと phase の payload、chain / 順序ログの prefix を照合する。差分は対象の archive marker 1 件、native chain 追記 1 件、順序ログ追記 1 件だけとする。実施済みの TEST-AISCI-024 の退役と、その後の記録も保持する。
7. native 検証で対象の退役と TEST-AIDS-331 の有効性を再確認する。REQ-AIDS-093 の未検証診断や、対象以外の新しい不整合が出れば停止する。

この操作を新しい Red / Green や失敗再現の成功と呼ばない。
他のサイクルの archive、void、現行の失敗の除外には使わない。
個別承認や前提の確認が不足していれば実行しない。
新しい固定点は実行後の記録を含めて取り、移送中に archive marker を追加しない。
既存の出所検証・移送関数の実装と interface は変更しない。

停止した隔離コピーでは説明可能性と感度分析の 14 組が成功したが、
TEST-AIDS-340 では有効な Red を観測できなかった。
このコピー、無効な試行、成功した記録は監査用に保持し、取り込まない。
古い固定点の記録と新しい記録を結合したり、失敗した対象だけを
取り込み対象から外したりして、入力の一致確認を回避しない。
改訂承認と個別操作の完了後に新しい隔離コピーを作り、
残る 17 要求・30 テストを 13 batch として最初から再現する。
REQ-AIDS-093 は TEST-AIDS-331 の既存の直接検証を維持するが、
CHANGE-043 の新しい Git 再現バッチには含めない。

### 再現の初期対象

| 要求 | 対象テスト | 過去版を探す実装・条件 |
|---|---|---|
| REQ-AIDS-021 / REQ-AIDS-082 | TEST-AIDS-215 / TEST-AIDS-021 | `fad1e16b42c2e1999a3bca67162f8034ce8a2ef2` の `explainability.py`。多クラス係数の集約と importance_kind の導入前 |
| REQ-AIDS-056 | TEST-AIDS-096/097/098/099/205/206/207/208/209/213/214/291 | `dedef0d^` の `sensitivity.py`。既存の export を保ち、target_claim の修正前を再現 |
| REQ-AIDS-110 | TEST-AIDS-415/416 | missing_data_analysis の追加前。内部実装の不在を明示 |
| REQ-AIMS-002 | TEST-AIMS-002 | materials-scientist 導入前。dispatch の不在を明示 |
| REQ-AIMS-003 | TEST-AIMS-981 | validation の導入前。内部実装の不在を明示 |
| REQ-AIMS-004 | TEST-AIMS-949/950 | evidence の導入前。内部実装の不在を明示 |
| REQ-AIMS-010 | TEST-AIMS-980 | phase_field / dispatch / manifest の導入前。phase-field の登録がない状態を明示 |
| REQ-AIMS-040 | TEST-AIMS-040 | kinetic_monte_carlo の導入前 |
| REQ-AISCI-025 | TEST-AISCI-048 | `73b5302^` の npm 同梱漏れ。npm_packaging の実在版も照合 |
| REQ-RELGATE-001/002/003/005 | TEST-RELGATE-001/002/003/005 | `07cde17^` の governance 実装の導入前 |
| REQ-RELGATE-004 | TEST-RELGATE-101 | `07cde17^` の pass-rate 実装の導入前 |
| REQ-TECHWRITER-001 | TEST-TECHWRITER-001 | `35dbdc5^` の SKILL.md と packaging guard |
| REQ-ACHEM-100 | TEST-ACHEM-972 | salt standardization の実在する導入・修正前 |

省略表記の test / requirement ID は CHANGE-043 の全 ID 一覧と、
実行時の manifest で完全な ID に展開する。
すべての revision は実行前に完全な commit ID に固定する。
存在しない親、collection error、別の新機能の欠落による incidental failure、
外部依存の欠落、選択数 0 は有効な Red と扱わない。
期待する対象契約の失敗と確認できなければ、その対象の実行を停止する。
表は未実行の成功を約束するものではない。
材料系の要求対応には、古い誤った cycle の requirement ID ではなく、
現在の `@verifies` を用いる。既存の機能契約は変更しない。

説明可能性は既存要求 REQ-AIDS-082 も再検証バッチの対象とする。
TEST-AIDS-021 は既に importance_kind も assert している。
REQ-AIDS-021 を残したまま REQ-AIDS-082 の trace 注釈を追加する。
テスト本体は変えない。TEST-AIDS-021 のラベル不足による Red は
REQ-AIDS-082 に対応付け、古い ranking 自体の失敗とは主張しない。
注釈追加も宣言 fingerprint を変えるため、同テストは新しい Red / Green の対象とする。
既存の stale を無変更と扱う修復ではない。
REQ-AIDS-021 の検証には TEST-AIDS-215 を使う。
実際に多クラス重要度の計算が失敗することを確認する。
2 要求を同じ実装の batch とし、実装を復元する前に両 Red を記録する。
Git 再現の対象サイクルには archive / void を使わない。
TEST-AISCI-024 と TEST-AIDS-340 の指定した各 1 サイクルの退役は、
Git 再現とは別の操作とし、それぞれ前述の限定例外と個別承認に従う。

governance / pass-rate / packaging-guard のテストは、
実装の import を各テスト内へ移す。assert と関数名は維持する。
対象は `tests/test_release_gate_governance.py`、
`tests/test_measure_pytest_pass_rate.py`、
`tests/test_tech_writer_skill_packaging.py`。
これらの対象には既存 TDD サイクルがないため、追加の失効は生じない。
依存を遅延 import する変更も、今回の設計承認後に行う。

### 隔離環境と段階の順序

作業元の現在のファイルと証拠を固定してコピーする。
別の `.venv` を同じ Python 3.12.13 と `uv.lock` から復元する。
作業元の editable install を使わず、conftest による
コピー内の src import と各 module の出所を確認する。
依存・コマンド・環境は Red / Green の間で固定する。

CHANGE-043 は次の実際の操作に沿って記録する。
設計承認後、作業元の実装前に、同じ shape を使う隔離 canary を完了させる。
canary は説明可能性の 2 テストを用い、正規の全段階、Red / Green、
別の使い捨てコピーへの移送、native 再検証まで実行する。
その結果は本番に移送しない。
CLI が段階やコピー後の記録を拒否すれば、本番には進まない。

本番の固定点を取る前に、作業元で要求・設計の承認を記録する。
CHANGE-042 の実装と正規 Red / Green、その段階記録も完了する。
6 テストの helper 移動、遅延 import、説明可能性の注釈を反映する。
CHANGE-026 の事実訂正も固定点より前に行う。
TEST-AISCI-024 の個別承認と限定した archive は実施済みとして保持する。
TEST-AIDS-340 の別の個別承認と限定した archive を、この時点で完了させる。
この後の changes.json を移送元の base とする。
CHANGE-042 の最終 quality 更新は、復旧後の全体チェックに基づく追記として区別する。
固定点から移送完了までは作業元の source・文書・証拠を更新しない。
変更があれば取り込みを中止し、新しい固定点からコピーと再現実行を作り直す。
古い実行結果は監査用に保持するが、merge や手動の rebase で救済しない。

1. 隔離環境で、古い要求・設計・テストの入力を Git tree から復元して impact を記録する。
2. 承認済みの現在の要求を復元し、requirements を記録する。
3. 承認済みの現在の設計を復元し、design を記録する。
4. 現在の固定テストを配置する。要求単位の batch で実際に `tdd red` を実行し、change の red も記録する。
5. batch の実装を作業元の現在版へ復元し、change の implementation を記録する。
6. 同じテスト・コマンドで `tdd green` を実行し、change の green を記録する。
7. 全 batch の Green 後、品質のチェックポイントを記録する。

Git の実データを使うのは入力の出所を保証するためであり、
混合した隔離コピーを当時の完全な worktree と主張しない。
各 path と revision の対応、テスト配置時点、実際の失敗理由を保存する。
この操作のためだけに架空の要求・設計差分や空の実装修正を作らない。
CLI が正規の段階を拒否した場合は停止し、記録を直接補修しない。

`build_replay_provenance` は完全 commit ID を batch ごとに保存する。
path ごとに過去・現在 hash と存在状態を記す。
テスト ID / hash、コマンド文字列 / hash、環境 fingerprint も保存する。
実行結果に加え、CLI 記録と構造化レポートの path / hash を残す。
Red / Green の test / command / environment が異なれば拒否する。
過去版の出所と実行時の実装 hash が一致しない場合も拒否する。
Green では作業元の現在版との一致を要求する。

### 生成物の移送と排他

作業元では証拠を増やさず、固定した order / TDD / changes / waivers と
入力の hash を保持する。隔離環境からの移送時に全項目を再照合する。
作業元が進んでいれば、古いコピーで上書きしない。
この凍結は上記の固定点から移送完了までの期間だけに適用する。
waiver の承認と正規の記録は移送後に作業元で行い、gate を再実行する。

同じ公開 musubix3 パッケージの `withEvidenceWriterLock` を使い、
作業元の正規 writer lock を保持してから再照合する。
Node 境界が lock の取得から全 rename と検証の終了までを実行する。
Python は Node process を起動し、非ゼロ終了を失敗として扱う。
Node は実際に使った musubix3 0.1.22 の entry を明示的に受け取り、
その package 内で公開 `musubix3/analysis` export を解決する。
package version と entry の hash を記録し、別版の暗黙選択は認めない。
新しい npm 依存や独自 lock は追加しない。
独自形式の lock を正規 lock の代わりに置かない。
操作は CLI が生成した byte 列の移送だけとし、JSON を結合しない。
order / TDD chain の元の prefix と既存 payload を確認する。
全ての元ファイル・生成物の hash、head、sequence を保存する。

同じ filesystem 上の temporary file に生成物を置き、書き込みと flush 後に
対象ごとに rename する。複数ファイル全体が atomic とは主張しない。
途中停止を判定する manifest と両側の元 artifact を保持する。
未完了状態では成功を報告しない。復旧時は現在値が transaction の
既知の before / after hash のどちらかと一致することを要求する。
未知の値や新しい書き手の更新があれば、復旧を自動続行しない。
その後に正規 CLI で構造・TDD・change を再検証する。

移送 manifest には `schemaVersion`、`transactionId`、`state` が必須。
`root` / `incomingRoot` は canonical な path とし、`nativeModule` も必須とする。
`inputFiles`、`files`、`before` / `after`、`completedPaths` を必ず含める。
`inputFiles` は固定した作業元入力の path / hash、
`files` は各 artifact の path / beforeSha256 / afterSha256、
`before` / `after` は order / TDD の head と sequence を持つ。
不在の before は null とし、空ファイルと区別する。
対象は order.json / tdd.json / changes.json と、
実行で新規生成した native レポートに限定する。
既存レポートの変更、承認・waiver・policy・source の移送は拒否する。
全 path を canonical root 内に限定し、symlink と path traversal を拒否する。

`planTransport` は読むだけで保存対象を確定する。
manifest は保護 artifact の外側に保存する。
`applyTransport` は `planned -> applying -> completed` と進む。
lock 内で全 before hash と現在入力、全 incoming hash を再確認する。
rename ごとに進捗を保存する。rename と進捗保存の間の停止も、
実ファイルの before / after hash で判定する。
`recoverTransport` は既知の before / after だけを受理して残りを完了する。
既に全 after と一致する実行は、変更せず完了を確認する。
未知の値、入力変更、lock 競合は blocked とし、上書きしない。
未完了 manifest が残る間は候補・ready を false とする。
完了後は全 after と入力の一致を検証した transport report を返す。

transport report は完了時点の記録であり、証拠ファイルの永久固定ではない。
完了後の native waiver / quality / approval / gate / status の記録は許可する。
準備状況の判定時には、完了時の order / TDD の全レコードが
同じ順序の prefix として現在も残り、changes の全段階記録が保持されることを確認する。
後続の記録は対応する正規 CLI の生成物と照合し、切り詰めや payload の変更は拒否する。
固定入力は実装・テスト・コマンド設定・policy・要求・設計を対象とし、
追記される evidence は prefix 検証で別扱いする。
completed manifest 自体は blocker ではない。
未完了 transaction、prefix 不一致、未承認の固定入力の変化があれば候補と ready を false にする。
移送完了後の今回の追補だけは、次の別の検証をすべて満たす場合に受理する。
元の移送 manifest と完了 receipt は変更しない。

### 移送完了後の履歴 scope 追補

CHANGE-043-run-003 は 30 組の正規 Red / Green と全段階を完了し、
3 ledger と 301 個の新しい監査 artifact の移送を完了した。
元の transaction ID は `eb35a3ac-839f-4783-aeed-063babe00de0`、
完了 manifest の SHA-256 は
`27b45b95e4694fe29ee325c368d8c6a1fa9f081bf693222b5e8d81876e561992`。
この完了記録を、後続の入力変更を許すために書き換えない。
旧コピーからの再取り込み、JSON の merge、hash の付け替えも行わない。

追補の実装は CHANGE-045 とし、REQ-GATE-RECOVERY-002/003 に対応付ける。
新しい機能要求は作らず、候補の範囲と準備判定の根拠を厳密化する。
TEST-GATE-RECOVERY-002/003 に最小の回帰ケースを追加し、
改訂設計の承認後に両方の正規 Red を記録する。
同じテストを保って候補抽出と追補検証を実装し、両方の Green を記録する。
段階記録は CHANGE-045 の全 2 要求を用い、当時の記録とは主張しない。

`validate_recovery_followup` は次を確認し、不一致を例外で明示する。
例外がある状態では候補・ready を報告しない。

1. 呼び出し側で独立して固定した expected_original と、実ファイルの内容 hash・transaction ID・完了 receipt を照合する。本番では上記の完了時の値を用い、単体テストでは fixture の完了時の値を固定する。追補自身が示す期待値では代用しない。元の独立コピーを読み、全移送 artifact の after hash を照合する。現在の監査 artifact の byte 列も照合する。
2. 元の独立コピーと現在の ledger を比較し、移送完了時の全 cycle・phase・chain・順序ログと変更段階の保持を確認する。既存 Quality の更新は保持された qualityHistory と照合する。追加分の chain と hash link、および native TDD / change / trace validator の結果を確認する。これらの整合性検証を、記録した process の独立した身元証明とは主張しない。
3. 元の inputFiles と現在値を比較する。手動で変えられるのは `.musubix/features/full-gate-recovery/requirements.md`、同じ feature の `design.md`、`.musubix/decisions/ADR-0127.md`、CHANGE-042/043/045/046 の文書、`scripts/gate_recovery.py`、`tests/test_gate_recovery.py` だけとする。この分類の追加・変更 path を before / after hash 付きで追補に列挙し、未記載・重複・範囲外を拒否する。
4. 残る変更は下記の native 追記型と派生 trace に分類し、手動入力の許可とは区別する。native の派生 trace は `buildTrace(root, false)` と projection の意味内容に照らして確認する。比較には公開 `api.canonicalSort` を使い、trace 最上位の generatedAt だけを除外する。保存済み byte 列は書き換えない。詳細は後述の CHANGE-046 に従う。
5. 現在の要求・設計 hash と正規の承認、CHANGE-045/046 の段階、対象 Red / Green、現在の実装・テスト hash を照合する。各サイクルのテストは Red / Green 間で同一とし、現在値には native order が最後の完了済み Green を使う。共有ファイルの対応と後続の未完了 Red は、後述の CHANGE-046 の規則で検証する。後からの変更は追補を無効にする。
6. 移送済みの 30 組の provenance と元の manifest を比較基準とする。再現対象の実装・テスト、コマンド設定、lock、policy が現在も同じことを確認する。隔離環境の inventory と現在の Python・lock 依存を照合する。絶対 path の差は比較対象から除くが、未検証の依存差分は受理しない。

| 変更の分類 | 対象 | 検証 |
|---|---|---|
| 手動入力 | 上記の要求・設計・ADR・CHANGE-042/043/045/046・検証関数・テストの各 path | 追補の完全な before / after 一覧、現在の承認、実際の Red / Green |
| native の追記型記録 | `.musubix/evidence/{tdd,order,changes}.json`、承認、change / workflow waiver、品質・workflow・formal・performance・model-correspondence の記録 | 元の全 record / payload / prefix 保持と native validator。承認・品質の現在 snapshot は保存済みの元 snapshot と区別し、正規の検証結果を照合する |
| 派生 trace | `.musubix/trace.json`、`.musubix/features/*/trace.json` | native の再計算と意味内容の一致、生成された byte 列の保存 |

どの分類にも入らない差分は拒否する。
新しい監査出力は元の移送 artifact と別の path に保存する。
元の監査 artifact の変更・上書きは許可しない。

実環境の事前確認では、Python 3.12.13 と共有する 196 package の版が一致した。
作業元だけにある pip 26.2.2 は、移送前から存在する bootstrap tool であり、
lock に含まれる分析・テスト依存ではない。この既知の差だけを明記して受理する。
pip を含む作業元の inventory を CHANGE-045 の impact 前に採取する。
その内容 hash を impact 時の監査 artifact と追補 manifest に結び付け、
Red 前の固定点として扱う。現在値との差は拒否する。
環境変数の生の値や secret は保存せず、既存の環境 fingerprint と必要な公開情報を用いる。

追補 manifest は `schemaVersion: 1` と `changeId: CHANGE-045` を持つ。
元の transaction ID / manifest hash と許可された `inputChanges` を保存する。
現在の要求・設計承認 hash と、実際の phase / report の path・hash も必要とする。
Green 時点の実装・テスト hash と、impact 前の環境 inventory の hash を結び付ける。
保護 evidence の外に新規保存し、元の manifest / receipt を上書きしない。
検証用関数には CODE-GATE-RECOVERY-007 を割り当て、
REQ-GATE-RECOVERY-003 / DES-GATE-RECOVERY-003 に対応付ける。
成功 report は `state=completed`、`inputsVerified=true`、
`prefixVerified=true`、`followupVerified=true` と検証した各 manifest hash を持つ。
この値は実ファイルを照合した結果からだけ返し、入力の自己申告を信用しない。

TEST-GATE-RECOVERY-002 は追加された履歴 scope の受理と、
同じ code でも許可外の change / requirement / detail を拒否することを確認する。
準備判定では正常な追補と、最終 hash の不一致や記録・監査物の改変を区別する。
TEST-GATE-RECOVERY-003 で未承認・範囲外差分と依存差分も検査する。
同テストでは実ファイルの context を渡さず、
`followupVerified=true` と自己申告する report も拒否する。
今回の 61 scope の根本診断を再確認し、個別の操作承認後にだけ waiver を追記する。
消えた診断は記録しない。workflow の宣言照合はこの履歴 waiver と区別する。

### CHANGE-046: 実環境の trace 比較の修正

CLI の trace は node ID と edge の from / to / relation を基準に整列される。
公開 `buildTrace(root, false)` は同じ内容を探索順で返すため、配列の直接比較では不一致になる。
比較する両方の graph に、固定した native module の公開 `api.canonicalSort` を適用する。
適用前に最上位の key が schemaVersion / generatedAt / nodes / edges / diagnostics / fingerprints と一致することを確認する。
canonicalSort が未知の field を落として変更を隠さないよう、欠落や追加を拒否する。
node / edge / 診断の配列順序と fingerprint の key 順序だけを正規化する。
重複要素は削除せず、node / edge / 診断 / fingerprint の追加・削除・内容変更を拒否する。
同じ sort key の要素は native が保つ順序で比較し、独自の tie-breaker は追加しない。
重複 ID など native trace check が拒否する graph は、正規化によって受理しない。
最上位の generatedAt だけを除外し、内部の同名 field は除外しない。
API が欠ける場合は検証を失敗とし、独自の並べ替えに切り替えない。
feature projection も同じ規則で比較し、保存済み trace の byte 列は変えない。

REQ-GATE-RECOVERY-003 の修正を新しい CHANGE-046 で記録する。
完了済みの CHANGE-045 の段階とバッチは更新しない。
手動入力の許可には `.musubix/changes/CHANGE-046.md` だけを追加する。
追補 manifest の `correctionArtifacts` は、CHANGE-046 の
impact / requirements / design / red / implementation / green / quality ごとの path / hash を持つ。
各 snapshot の対象 change ID、正確な requirementIds と phase payload を現在の正規 ledger に照合する。
CHANGE-046 の要求集合は REQ-GATE-RECOVERY-003 だけとし、欠落や追加を拒否する。
CHANGE-045 の元の `phaseArtifacts` と `batchArtifacts` も、これまでどおり保持・検証する。

最終 Green は、両 change の完了済み Green と CHANGE-045 のバッチ Green の中から
native order が最も大きいものを選ぶ。時刻や change 番号では選ばない。
共有する実装・テストファイルは、その Green の正規 snapshot と現在の hash を照合する。
実装は requirementImplementations の path / hash と一致することを確認する。
テストファイル全体は、公開 snapshot で計算する現在の tests fingerprint と
最終 Green の tests fingerprint を照合する。追補の greenFiles との自己照合だけでは受理しない。
各要求のサイクルは、各 change の design 後に開始し、
対応する change またはバッチの Green 前に完了したものから native order で選ぶ。
後続の未完了 Red があれば拒否し、古い Green に切り替えない。
Red / Green の test fingerprint の一致、現在の要求単位の test fingerprint、
保存済み両 report の hash と outcome も照合する。
新しいサイクルの根拠を古い段階へ付け替えない。
元の環境 baseline は CHANGE-045 impact 前の保存物を引き続き使い、現在値との差は拒否する。

TEST-GATE-RECOVERY-003 の Node 境界 fixture は、公開 native canonicalSort を使う。
CLI と readonly API の実際の順序差を再現し、順序だけなら受理する。
内容変更、重複の追加、内部の generatedAt 変更は拒否し、
最上位の未知の field も拒否する。重複のケースには byte 列が等しい要素を使う。
検証前後の保存済み trace の hash が同じことも確認する。
同テストで correctionArtifacts の欠落と payload 改変も拒否する。
これらの fixture は単体検証に限定し、履歴の再実行の証拠とは扱わない。
設計承認後に新しい Red を記録し、test ファイルを固定したまま最小修正と Green を記録する。
最後に実環境の追補検証と全体 gate を実行する。release 承認は別に必要とする。

### CHANGE-045 の記録不整合 1 件の追補

初回の change Red / Green 間に、担当 agent がテスト補助関数の lint 修正を行った。
対応する TDD の Red / Green では各 test 関数が同一だったが、
change のファイル単位の照合では不整合が生じた。この元記録は保持する。
追加する scope は CHANGE-045 / CHANGE_TEST_CHANGED_AFTER_RED /
detail=REQ-GATE-RECOVERY-002,REQ-GATE-RECOVERY-003 だけで、requirement selector は付けない。
61 件の過去 scope とは別の例外とし、実行には別途 nahisaho の明示的な操作承認を要する。

chronology_context は `root`、`proof`、`expected_sha256`、`native_module` を持つ。
proof は保護 evidence の外にある JSON の実 path、
expected_sha256 は呼び出し側が独立して固定した値とする。
本番の期待値は要求で承認した
`245e074ddcab3c8193bc03fe756d262ad92459948c5ebe56b0338599aa8cc18b`。
native_module は `{packagePath, version, entry, sha256}` を持つ。
呼び出し側は元の移送で固定した値を独立して指定する。
packagePath から解決した公開 analysis module の entry / version と、
entry の実ファイル hash を import 直前と直後に照合する。不一致なら検証を止める。
最終検証では root と native_module の全 field が、検証済みの元 manifest と一致しなければならない。
単体 fixture では各期待値を呼び出し側で別に固定し、本番の記録とは主張しない。

根拠 JSON と、そこから参照する再構成 Red / Green ファイルの SHA-256 を実ファイルで照合する。
再構成は実際の apply_patch 記録と作業元の Ruff を使ったもので、当時の保存物とは扱わない。
公開 `buildTrace(root, false)` と `snapshot` で全 test path の現在の snapshot を得る。
対象の `tests/test_gate_recovery.py` だけを各再構成ファイルの hash に置き換えて
読み取り専用のメモリ上で fingerprint を計算する。証拠や実ファイルは置き換えない。
結果は元の CHANGE-045 の Red / Green の tests fingerprint と両方とも一致しなければならない。
全 test 関数の AST を再計算し、同一性を確認する。
全ファイル差分は、次の old / new 各 2 行の置換 1 回だけに限定する。
old の byte 列が Red ファイル内にちょうど 1 回存在し、それだけを置換した結果が
Green ファイル全体の byte 列と一致しなければならない。
それ以外の字句、行末、末尾 byte の違いも拒否する。

```python
    for name in manual:
        (root / name).write_bytes(b"new " + manual[name])
```

```python
    for name, value in manual.items():
        (root / name).write_bytes(b"new " + value)
```

JSON 内の boolean や、差分だという自己申告は判定根拠にしない。

根本診断と正確な scope があっても、context がなければこの 1 件は blocked とする。
指定した根拠が不正なら例外を明示し、候補を返さない。
最終の追補 manifest にも `chronologyProof` として同じ path / hash を結び付け、
別に渡した chronology_context の期待値で再検証する。waiver 後もこの確認を省かない。
他の code、change、detail や requirement selector の追加を許さない。

この拡張には TEST-GATE-RECOVERY-002 の回帰ケースを使う。
未検証の例外を拒否する既存動作を維持し、根拠を検証した同 scope の受理で正規 Red を得る。
Red が未対応 keyword の TypeError だけにならないよう、テストは signature を照合する。
旧 API には元の 1 引数を、新 API には chronology_context も渡し、
検証した scope が候補にないという assertion の失敗を確認する。
この旧 API との照合は回帰テスト内だけに置く。製品 code に fallback は設けない。
文書承認後に、未使用の REQ-GATE-RECOVERY-002 単独バッチで実装と Green を記録する。
テストファイル全体を change Red から change Green まで固定し、lint 修正も間に挟まない。
全 2 要求の最初の段階と既存の REQ-003 修正バッチは保持する。
最終 Green は完了した最新バッチを含み、共有する実装 path と現在値の一致を確認する。
後続バッチの全 phase / report を追補に結び付け、Quality は元 payload を履歴に残して更新する。
native workflow は compatible mode の診断 severity、approval は approved status を照合する。
実際の戻り値にない valid field を使わず、strict 検証や process の独立認証も主張しない。

native `evidence merge` も隔離したコピーで試した。
現在の CHANGE-005 の歴史的順序を構造検証が拒否するため、
この根拠の移送には使わない。これは通常 gate が認める waiver と
merge の構造的前提の差であり、merge の成功や CLI import を主張しない。

## 履歴文書と最終確認

CHANGE-026 は当初の proposal と実際の ledger scope を区別する追記を行う。
現在 REQ-AIDS-053 は chart readability、cross-process の実要求は
REQ-AIDS-093 であり、古い提案番号を実装済みの証拠として再利用しない。
Requirements 欄は記録済みの REQ-AIDS-044 と照合する欄として最小訂正する。
元の提案内容と「REQ-AIDS-044 の規範変更ではない」という経緯は残す。

非承認の必須チェックが全て pass になるまで release 承認を求めない。
actual gate と approval report から候補状態を評価し、レビュー後に
release manifest の全 path / hash / 残余リスクを提示する。
人間の承認後、正規 CLI でその hash だけを記録し、gate / status を再実行する。
基準・閾値を下げず、失敗・欠落・未実行を合格と扱わない。

## 状態と検証

状態は `planned -> approved -> isolated -> red -> green -> verified -> promoted`。
TEST-AISCI-024 と TEST-AIDS-340 の退役はそれぞれ固定点前の別操作とし、
`archive-pending -> archive-approved -> archived -> verified` と進む。
TEST-AISCI-024 の検証済み退役は再実施せず保持する。
対象 ID の変化や前提の欠落は blocked とし、隔離再現へ進まない。
すべての batch の成功後に `candidate -> release-approved -> ready` へ進む。
source / test / command / chain の不一致、writer の競合、予想外の失敗は
`blocked` に遷移する。blocked から ready への直接遷移はない。

単体テストでは Git 参照・path・差分の受理/拒否、prefix の改変、
waiver の全 selector regime と重複、check の欠落/重複/status、
各承認段階の組合せを検査する。状態遷移の全辺と拒否辺を列挙する。
TEST-GATE-RECOVERY-001 は Python の出所検証と Node 移送の両方を担当する。
temp root 上で最初の rename 後の停止、rename 後・進捗保存前の停止、
競合 writer、未知 hash、未完了入力、完了済み再実行を検査する。
Node subprocess も既存 pytest から実行し、新しいテスト runner は追加しない。
TEST-GATE-RECOVERY-003 は未完了 transport を ready としないことも検査する。
完了後の正規追記を受理し、chain の巻き戻しや既存 payload の改変を拒否するケースも含める。
型検査器の追加は行わず、既存の pytest / Ruff / native SDD checks を使う。
実装後は範囲を限定した Claude Sonnet 5.5 レビューと全体 gate で確認する。
