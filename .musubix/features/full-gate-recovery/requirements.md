---
schemaVersion: 1
feature: full-gate-recovery
---
# 全体ゲート復旧の要求

## 目的と確認済みの方針

既存の機能契約と品質条件を維持したまま、全体ゲートを通す。
nahisaho は、実在する修正前の Git 版を隔離環境で再現し、
現在の修正版で新たに Red / Green を記録する方式を承認した。
再現結果は現在の実行根拠であり、当時の開発順序や実行を証明しない。

新しい規範要求は次の 3 件。既存の機能要求は変更せず、
後述の対象について欠落・失効した検証根拠を修復する。
復旧作業には、出所の確認、waiver 候補の抽出、準備状況の判定を行う
小さな検証用関数を用いる。独自のテスト実行器や SDD CLI は作らない。

## REQ-GATE-RECOVERY-001: Git 由来を確認できる隔離再現
Priority: must
Type: non-functional
Pattern: event-driven

Statement: 過去の TDD を再検証するとき、システムは実在する過去の Git commit と対象ファイルの内容を照合し、現在の修正版と区別できる出所を保存しなければならない。

Acceptance: 検証用関数は、参照する commit を完全な commit ID に解決し、現在の HEAD より前の祖先であることを確認する。選択した各ファイルについて、過去版と現在版それぞれの SHA-256 を返す。過去版に対象実装がまだ存在しない場合は、Git tree で不在を確認し、存在フラグ false と hash null を記録する。空ファイルとは区別する。存在しない commit、祖先ではない commit、リポジトリ外へのパス、テスト・SDD 根拠を実装の代わりに差し替える指定、変更差分のない再現指定を明示的に拒否する。実行には隔離したコピーを用い、テストと設定済みコマンドは同一に保つ。実在する過去版の失敗と現在版の成功を記録する。各 Red / Green について commit ID、差し替え対象、テストの同一性、コマンド、実行結果、CLI 生成記録と構造化レポートの hash を保存する。過去版で対象テストの失敗が観測できなければ有効な Red と扱わない。

Constraints: 作業元の未コミット変更を保持する。テスト、外部依存、コマンドとその実行環境を Red / Green 間で変更しない。架空の過去版、意図的に壊した実装、外部依存の欠落、テスト未選択を Red の代わりに使わない。新規モジュールが過去の Git tree にまだ存在しない場合と、外部ライブラリの未インストールは区別する。証拠は musubix3 が生成した追記型記録として保存し、既存サイクル・hash chain・順序ログを削除または手編集しない。隔離環境の生成物を取り込む前に、元の記録が保持され、対象テストと復元後の実装が作業元と一致することを確認する。

生成物の取り込みは、CLI が生成したファイルの内容を一切変えないコピーに限定する。
既存記録への手動追記・JSON の結合・hash の再計算は行わない。
コピー前に、作業元の入力と証拠が隔離コピー作成時から変わっていないこと、
生成後の chain / 順序ログが元の全レコードを同じ順序の prefix として持つこと、
既存サイクルが保持されていることを確認する。
同時書き込みを排除した状態で実行し、コピー前後の各ファイルの hash と
chain head / sequence を保存する。これは CLI の import 機能ではなく、
監査可能な生成 artifact の移送として設計・実装する。
途中停止や不一致があれば取り込み未完了とし、gate の成功を報告しない。
復旧は保存した CLI 生成物との一致を確認できる場合だけ行い、
別の書き手による更新があれば上書きしない。

再現不能な静的チェックに対する例外は、TEST-AISCI-024 の最新サイクル
`1a91db34-ed68-4b5a-b225-a7cbe99cd316` だけに限定する。
このテストは要求書とテスト注釈だけを読み、許可対象の実装を差し替えても
Red を再現できない。失敗を作るために要求書やテストを書き換えない。
同じ REQ-AISCI-024 を直接検証する TEST-AISCI-035 について、
既存サイクル `0d264714-5c38-498a-9dbc-2b4f4f358849` を根拠とする。
archive されていない有効な Red / Green と現在の宣言 fingerprint の一致を確認する。
両テストを現在版で実行し、成功した結果を保存する。
これらの根拠、対象 cycle ID、退役の理由を示し、
nahisaho の明示的な承認を得た後だけ正規の `tdd archive` を行う。
例外の承認は今回の要求・設計への承認と区別して記録する。

archive は作業元の固定点を取る前に行う。
実行直前に TEST-AISCI-024 の最新 cycle ID が上記の対象と一致することを確認する。
一致しなければ停止する。
古い未完了サイクル `e8ff006d-e17a-4a43-8f22-63eb4f6901c6` は退役させない。
元の全サイクルと phase の payload、既存 chain / 順序ログの prefix を保持する。
差分は対象の archive marker 1 件、正規 CLI の chain 追記 1 件、
順序ログ追記 1 件だけに限定する。
native 検証で対象の退役と別テストの有効性を再確認する。
テスト自体は削除せず、最終ゲートでも実行する。
archive を新しい Red / Green や失敗再現の成功と呼ばない。
他のサイクルの archive、void、必須チェックの緩和にはこの例外を用いない。
条件を一つでも満たさない場合は archive を行わず停止する。
本改訂提案時点では、この TEST-AISCI-024 の退役は個別承認後に正規 CLI で
実施済みである。上記は実施時の条件として保持し、再実施の条件にはしない。
退役済みの結果と承認・実行記録をそのまま保持する。

既存フォールバックを確認する TEST-AIDS-340 にも、次の限定例外を設ける。
対象は作業元の未完了サイクル
`d338d2a4-d6db-45e0-b711-2266228eb5bb` だけとする。
祖先に対象がなければ現在位置の projects を使う動作は修正前から存在し、
実在する修正前の Git 版でも同じテストが成功した。
この結果を有効な Red と扱わず、失敗を作るために実装やテストを壊さない。
同じ REQ-AIDS-093 の祖先探索を直接検証する TEST-AIDS-331 の
既存サイクル `33a2818f-da5d-4bbb-b714-08f6bc146cf8` を維持する。
その cycle が archive されておらず、有効な Red / Green を持ち、
現在の宣言 fingerprint と保存済み Green が一致することを確認する。
TEST-AIDS-331 / 340 を現在版で実行し、両方の成功と入力の hash を保存する。
対象 cycle ID、元の phase と chain / 順序ログの hash、代替根拠、
退役の理由を示し、nahisaho の個別承認後だけ正規の `tdd archive` を行う。
要求・設計への承認や、TEST-AISCI-024 の個別承認で代用しない。

archive は新しい作業元の固定点を取る前に行う。
実行直前に TEST-AIDS-340 の最新 cycle ID が上記と一致しなければ停止する。
元の全サイクルと phase の payload、既存 chain / 順序ログの prefix を保持する。
この操作の差分は対象の archive marker 1 件、正規 CLI の chain 追記 1 件、
順序ログ追記 1 件だけに限定する。
差分の基準は実行直前の作業元とし、実施済みの TEST-AISCI-024 の退役と
その後の記録を含めて保持する。
native 検証で対象の退役と TEST-AIDS-331 の有効性を再確認する。
REQ-AIDS-093 の未検証診断や、対象以外の新しい不整合が出れば停止する。
TEST-AIDS-340 は削除せず、最終ゲートでも実行する。
退役を新しい Red / Green や失敗再現の成功と呼ばない。
他のサイクルの archive、void、必須チェックの緩和にはこの例外を用いない。
TEST-AISCI-024 の承認済み退役と既存の全記録を保持し、同じ退役を繰り返さない。
条件を一つでも満たさない場合は archive を行わず停止する。

今回停止した隔離コピーとその実行記録は監査用に保持し、取り込まない。
要求・設計の改訂と個別承認付き操作の後に、新しい固定点で隔離コピーを作る。
その入力に基づいて残る Git 再現を最初から行う。
古いコピーの成功記録を新しい固定点へ結合したり、失敗した対象だけを
取り込み対象から外したりして、入力の一致確認を回避しない。
この TEST-AIDS-340 の退役も本追補の提案時点で個別承認・実施・検証済みである。
上記の実施条件と全記録を保持し、再実施しない。
その後の新しい固定点で 30 組の Red / Green を記録し、
17 要求・13 batch の native 検証と全固定入力の一致を確認して移送を完了した。
以前の停止したコピーの記録は取り込んでいない。

## REQ-GATE-RECOVERY-002: 診断と一致する waiver 候補
Priority: must
Type: non-functional
Pattern: event-driven

Statement: 過去の段階記録の欠落を修復するとき、システムは実際に報告された診断から CLI が許容する正確な waiver scope だけを候補として提示しなければならない。

Acceptance: 検証用関数は gate の構造化診断から change ID、診断 code、必要な requirement ID または detail を抽出し、重複を除いた候補を返す。stale な waiver は対応する根本診断が現在も存在する場合だけ候補とする。解消済み診断、scope が欠けた診断、未対応 code を承認可能な候補として返さない。記録欠落、段階欠落、要求単位の TDD 順序根拠の欠落を区別する。実際の waiver 記録前には、対象 scope と理由を列挙して nahisaho の明示的な承認を得る。

Constraints: 検証用関数は証拠を書き換えない。waiver は過去の記録不備に限定し、現行の失敗テスト、stale な TDD、未検証の要求、コマンド未実行を合格に変えるためには用いない。仕様一覧の不一致は waiver で隠さず、実在する要求と履歴を確認して文書を訂正する。

候補を扱う code は、実際に確認した musubix3 0.1.22 の
`CHANGE_RECORD_MISSING`、`CHANGE_PHASE_MISSING`、`CHANGE_RED_UNPROVEN`、
`CHANGE_GREEN_UNPROVEN`、`CHANGE_COMPLETENESS_TDD`、
`CHANGE_ORDER_MIGRATION_REQUIRED` に限定する。
それぞれ CLI が求める change 単位、detail 単位、requirement 単位の
selector を維持する。順序移行の code は
`CHANGE-021` の `detail=requirement:REQ-ACHEM-100` だけを対象とし、
requirement selector への読み替えや別の detail を拒否する。
別の code が必要になれば設計と承認を更新する。
CHANGE-001 の既存 waiver は根本診断が残る場合だけ更新候補とし、
CHANGE-019 の同じ要求の診断は現在報告されている場合だけ新規候補とする。
既存 waiver の直接編集や、解消済み診断への再記録は行わない。

追加の履歴候補は CHANGE-003/011/014/015/021/039/040 に限定する。
新しい TDD が有効でも、過去の CHANGE 内の順序欠落を証明したとは扱わない。
今回確認した正確な対象は次の 61 scope とする。
表の各 requirement と code の組合せをそれぞれ独立した scope として扱う。

| change | code | selector | scope 数 |
|---|---|---|---|
| CHANGE-001/019 | CHANGE_RED_UNPROVEN / CHANGE_GREEN_UNPROVEN / CHANGE_COMPLETENESS_TDD | 各 REQ-AISCI-004/017/024 | 18 |
| CHANGE-020 | CHANGE_PHASE_MISSING | 各 detail=phase:red / phase:implementation / phase:green / phase:quality | 4 |
| CHANGE-020 | CHANGE_COMPLETENESS_TDD | requirement=REQ-AISCI-023 | 1 |
| CHANGE-022/023/024/025/027/028 | CHANGE_RECORD_MISSING | selector なし | 6 |
| CHANGE-026 | CHANGE_PHASE_MISSING | 各 detail=phase:red / phase:implementation / phase:green / phase:quality | 4 |
| CHANGE-026 | CHANGE_COMPLETENESS_TDD | requirement=REQ-AIDS-044 | 1 |
| CHANGE-003 | CHANGE_COMPLETENESS_TDD | 各 REQ-AIMS-002/003/004/010/040 | 5 |
| CHANGE-011 | CHANGE_RED_UNPROVEN / CHANGE_GREEN_UNPROVEN / CHANGE_COMPLETENESS_TDD | requirement=REQ-AIDS-082 | 3 |
| CHANGE-014 | CHANGE_RED_UNPROVEN / CHANGE_GREEN_UNPROVEN / CHANGE_COMPLETENESS_TDD | requirement=REQ-AIDS-056 | 3 |
| CHANGE-015 | CHANGE_RED_UNPROVEN / CHANGE_GREEN_UNPROVEN / CHANGE_COMPLETENESS_TDD | 各 REQ-AIDS-021/082 | 6 |
| CHANGE-021 | CHANGE_RED_UNPROVEN / CHANGE_GREEN_UNPROVEN / CHANGE_COMPLETENESS_TDD | requirement=REQ-ACHEM-100 | 3 |
| CHANGE-021 | CHANGE_ORDER_MIGRATION_REQUIRED | detail=requirement:REQ-ACHEM-100 | 1 |
| CHANGE-039/040 | CHANGE_RED_UNPROVEN / CHANGE_GREEN_UNPROVEN / CHANGE_COMPLETENESS_TDD | requirement=REQ-AIDS-110 | 6 |

候補を抽出する code は、この 61 scope と次に記す 1 件の限定例外だけを承認可能と扱う。
scope が一致しても、実行直前に同じ根本診断が存在しなければ記録しない。
この明記された例外以外の範囲追加や、現在の失敗を履歴不足へ読み替える操作は拒否する。
要求・設計への承認と waiver 操作の承認は区別し、
実際の記録には全 scope と理由を示した nahisaho の明示的な承認を要求する。

同一セッションの記録不整合について、次の 1 scope だけを別枠で候補にできる。
`changeId=CHANGE-045`、
`code=CHANGE_TEST_CHANGED_AFTER_RED`、
`detail=REQ-GATE-RECOVERY-002,REQ-GATE-RECOVERY-003` とし、
requirement selector は付けない。61 件の過去 scope は変更しない。
この 1 件だけを、上記の 6 code と過去の記録不備に限定する規則への追加例外とする。
候補を抽出するときも、次の根拠条件を満たすことを確認する。
これは担当 agent が初回 change Red / Green の間にテスト補助関数の lint 修正を行った不備である。
当時の記録、診断、元の実行結果は保持し、整合していたとは主張しない。

根拠は保護 evidence の外に JSON として保存する。
実際の `apply_patch` 記録と作業元の Ruff を使って、初回テストファイルを再構成した。
本番で呼び出し側が独立して固定する根拠 JSON の SHA-256 は
`245e074ddcab3c8193bc03fe756d262ad92459948c5ebe56b0338599aa8cc18b` とする。
根拠自身が示す期待 hash は信用しない。単体 fixture でも呼び出し側が別に hash を固定する。
候補抽出と操作承認の前に、再構成した両ファイルを照合する。
Red / Green それぞれの byte 列から計算した native tests fingerprint は、
変更不能な元の change 段階記録と一致しなければならない。
全 test 関数の AST が同一で、差分が補助関数の辞書値取得の lint 修正だけであることも確認する。
再構成した artifact は当時の保存物ではなく、native TDD の実行根拠の代用にはしない。
後続の API 修正に対する実際の Red / Green バッチ、有効な現在の TDD、
現在の全体テスト成功も必要とする。scope や根拠が欠ければ候補を実行しない。
最終の追補検証でも同じ根拠を読み、hash、元の段階 fingerprint、AST と差分を再確認する。
この例外は失敗テスト、stale な TDD、未検証要求、未実行コマンドを除外する許可ではない。
要求・設計の承認を操作の承認に流用せず、この 1 scope の実行承認を別に得る。

CHANGE-026 は文書の最小限の事実訂正と追記で対処する。
元の提案内容を歴史的経緯として残し、現在割り当てられた要求 ID と
実際の chronology scope を区別する。文書の訂正を実装済みという証明には使わない。
CHANGE 文書は訂正対象だが、保護された changes / order / TDD 証拠の
手編集は対象に含めない。

## REQ-GATE-RECOVERY-003: 根拠に沿った準備状況の判定
Priority: must
Type: non-functional
Pattern: unwanted-behavior

Statement: もし必須チェックの失敗、欠落、未実行またはリリース承認待ちがあるならば、システムは全体ゲートの準備完了を報告してはならない。

Acceptance: 検証用関数は、確認対象として明示された必須チェックがすべて一意に存在し pass の場合だけ、非承認チェックの合格を報告する。欠落、重複、fail、skipped、未知の status、矛盾した全体 status を合格と扱わない。承認だけが不足する候補状態と最終準備完了を区別する。最終確認では設定済みの全コマンドを省略せず実行する。required な非承認チェックがすべて pass になった後にだけ、release の artifact 一覧・hash・残余リスクを提示して承認を求める。承認記録後の gate と status で ready が true であることを確認する。

Constraints: `.musubix/policy-baseline.json`、憲章、必須チェック、閾値、テスト選択を弱めない。既存の GiNZA 5.3 更新と検証を保持する。実装と文章のレビューには Claude Sonnet 5.5 を使用する。コミット・push・パッケージ公開は本変更に含めない。

完了した移送の manifest と receipt は当時の入力・生成物の証明として保持する。
本追補の要求・設計と候補抽出の修正を移送完了後に行う場合、
元の manifest の入力 hash を現在値へ書き換えて承認を流用しない。
移送完了時の全記録が現在も prefix として残ることを確認する。
変更 path の before / after hash、現在の要求・設計承認、
実際の変更段階と Red / Green、その保持検証を別の追補 manifest に結び付ける。
追補 manifest と検証結果は新しいファイルに保存し、元の記録を上書きしない。
手動で変更できる入力は本追補の要求・設計・ADR・CHANGE 文書、
`scripts/gate_recovery.py` と `tests/test_gate_recovery.py` に限定する。
正規 CLI が生成する変更段階・TDD・順序ログ、承認・waiver・品質の
追記型記録は別の許可対象とし、移送完了時の prefix と既存 payload を保持する。
追補の段階と Red / Green は新しい change ID に結び付け、
テストは Red / Green 間で同一、実装は各段階の実際の before / after hash と照合する。
現在の実装・テストは、それぞれ Green 時点の最終 hash と一致しなければならない。
現在の要求・設計は、それぞれ承認された最終 hash と一致しなければならない。
後から変更された場合は追補を無効とし、再検証と必要な再承認を要求する。
native が再生成する trace は意味内容を再検証し、固定入力から黙って除外しない。
元の再現対象 30 テストとその実装、コマンド、実行環境、policy の変更は許可しない。
比較基準には元の移送 manifest の入力 hash と、
移送済みの再現 provenance にあるテスト・実装・コマンド・環境の hash を用いる。
元の環境 inventory、Python と lock で固定した依存の一致も確認する。
隔離環境と作業元で異なる絶対 path は環境の変更と混同せず、
一致を確認できない環境を暗黙に受理しない。
比較と追補の判定は決定的な検証用関数で行い、
許可外の差分、最終 hash の不一致、記録の改変、環境の不一致をテストする。
許可範囲外の差分、未承認の入力、移送済み記録や監査 artifact の改変、
追補の根拠不足があれば候補と ready を false にする。
追補後も設定済みの全体チェックと現在の入力に対する release 承認を必要とする。
この追補を、停止したコピーの取り込みや履歴の merge に使わない。

### 実環境で確認した trace 比較の修正

CLI が保存する trace と公開 API が返す trace は、配列の順序が異なる場合がある。
検証処理は公開 `api.canonicalSort` を使い、順序だけの違いを内容の不一致として拒否しない。
独自の並べ替えで代用せず、この API を利用できなければ検証を失敗とする。
対象は node / edge / 診断の配列順序と fingerprint の key 順序で、重複要素は削除しない。
除外する値は trace 最上位の generatedAt だけとする。
node、edge、診断、fingerprint の追加・削除・内容変更と、内部の generatedAt の変更は拒否する。
正規化は比較用メモリ内で行い、保存済みの trace を書き換えて一致を作らない。
順序だけが異なるケースの受理、内容変更の拒否、検証前後の保存済み trace の hash 一致を回帰テストで確認する。

この修正は CHANGE-046 / REQ-GATE-RECOVERY-003 として記録する。
手動入力の許可対象に `.musubix/changes/CHANGE-046.md` だけを追加し、
他の入力範囲、元の移送記録、実行環境、policy は維持する。
既存の手動入力の許可範囲は広げず、本修正のために CHANGE-045 の文書や完了済み段階を変更しない。
REQ-GATE-RECOVERY-003 の Statement / Acceptance / Constraints は維持する。
追補は CHANGE-045 の全段階と追加バッチに加え、CHANGE-046 の実際の Red / Green を照合する。
CHANGE-046 には REQ-GATE-RECOVERY-003 だけを列挙し、
impact / requirements / design / red / implementation / green / quality の全段階を正規に記録する。
各要求の検証には native の単調増加する order が最も新しい対応サイクルを使う。
change 番号や時刻では選ばず、未完了の新しい Red があれば追補を拒否する。
各サイクルのテストは Red / Green 間で固定し、要求単位の test fingerprint を現在値と照合する。
共有する実装・テストファイルの現在値は、この 2 変更で order が最後の完了済み Green と照合する。
以前のサイクルのファイル全体 hash が、後続修正後のファイル全体 hash と等しいとは主張しない。
元の段階を上書きしたり、後続の修正を古い Green の証拠として扱ったりしない。
これらの根拠が欠ける場合は追補を拒否し、非承認チェックの合格を主張しない。

## 既存要求の再検証範囲

現在の診断に基づく初期対象は次のとおり。
新たな診断は原因を確認し、承認済みの同じ方針に含まれるか判定する。
範囲または証拠の意味が変わる場合は設計と承認を更新する。

| 区分 | 対象 |
|---|---|
| stale な 27 テスト | TEST-AIDS-017/021/022/034/096/097/098/099/112/204/205/206/207/208/209/213/214/291/415/416、TEST-AIMS-002/949/950/980/981、TEST-AISCI-024/035 |
| TDD 未充足の 8 要求 | REQ-AIMS-040、REQ-AISCI-025、REQ-RELGATE-001/002/003/004/005、REQ-TECHWRITER-001 |
| 不完全サイクルのあるテスト | TEST-AIMS-002/040、TEST-ACHEM-972、TEST-AIDS-340 |
| 段階記録が欠落 | CHANGE-022/023/024/025/027/028 |
| 部分的な段階記録 | CHANGE-020、CHANGE-026 |
| 要求単位の古い waiver と履歴不足 | CHANGE-001/019 の REQ-AISCI-004/017/024 |
| 文書と記録の不一致 | CHANGE-026 の Requirements 欄 |

材料系の再検証では、古いサイクルの誤った要求対応を流用しない。
現在の `@verifies` に従い、TEST-AIMS-949/950 は REQ-AIMS-004、
TEST-AIMS-980 は REQ-AIMS-010、TEST-AIMS-981 は REQ-AIMS-003 に対応付ける。
TEST-AIMS-002 だけを REQ-AIMS-002 の再検証対象とする。
TEST-AISCI-024 は上記の限定例外で扱い、Git 由来の再現対象から外す。
TEST-AIDS-340 も上記の別の限定例外で扱い、Git 由来の再現対象から外す。
REQ-AIDS-093 は TEST-AIDS-331 の既存の直接検証を維持し、
CHANGE-043 の新しい Git 再現バッチから外す。
初期対象の TEST-AISCI-035 は、承認済みの宣言範囲の修復で
既存 Green と一致したため、新しい再現サイクルを作らない。

TEST-AIDS-417/418 の承認済み移行と、CHANGE-003 の追記型 Quality 更新は保持する。
旧 REQ-RELGATE の「永久に修復不能」「workflow は現在セッションで合格不能」
という説明は現行 CLI の確認結果と異なる。歴史的記述として扱い、
新たな除外条件や準備完了の根拠には使わない。

## 完了条件と停止条件

最終的な完了条件は、実行した全体 gate の required チェックの合格と
同じ入力に対する `status.gate.ready == true`。
必要な人間の承認は省略しない。
Git 履歴から対象の失敗を再現できない、CLI が正規の記録を拒否する、
または入力を同一に復元できない場合は、残る対象と理由を示して停止する。
ただし、TEST-AISCI-024 と TEST-AIDS-340 の指定した各 1 サイクルだけは、
それぞれ上記の全条件と個別承認を満たす場合に限り、
別テストの根拠を維持した正規 archive で扱う。
不足する根拠を成功扱いにして完了しない。
