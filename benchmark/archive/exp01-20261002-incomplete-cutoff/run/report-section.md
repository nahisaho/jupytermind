## 実験01: Titanic（v0.2.0・データ取得まで確認、比較分析は未完了）

**課題**: 「KaggleのTitanicデータで、生存者と非生存者にどのような違いが見られるか調べてください。」

**初回プロンプト（全文・原文）**:

> KaggleのTitanicデータで、生存者と非生存者にどのような違いが見られるか調べてください。分析計画は自分で立て、適切な比較と図表を選び、判断根拠と限界を日本語で説明してください。AI Data Scientist SkillとJupyter MCPを使い、計画、実行コード、結果、根拠付きInsightをノートブックに記録し、最後に上から再実行できるか確認してください。 Kaggle参照先: https://www.kaggle.com/competitions/titanic。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。外部CSVミラーは使用しないでください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。APIで対応するデータが見つからない場合は外部ソースにフォールバックせず、その実験を停止して理由を報告してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-01-titanic/notebooks/kaggle-v020-kaggle-exp-01-titanic.ipynb としてください。run_idは `v020-exp-01` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。

**使用したJupytermindモジュール**: Notebookのコードセルにある直接importと関数呼出しを根拠に、次の使用を確認しました。計画文での言及や、importだけで関数を呼んでいないモジュールは使用実績に含めません。

| モジュール名 | 関数名・直接使用した型 | 使用目的と確認範囲 |
|---|---|---|
| `ai_data_scientist.project_manager`（別名`pm`） | `resolve_project`、`ensure_notebook`、`ensure_data_dir` | プロジェクト、Notebook、データ保存先を準備。設定セルの出力にNotebookの保存先が記録されています。 |
| `ai_data_scientist.language_router` | `detect_language` | 日本語指示の言語判定。出力は`ja`でした。 |
| `ai_data_scientist.lifecycle` | `register_run`、`get_run_status`、`is_cancel_requested`、`mark_execution_start`、`mark_execution_end`、`mark_completed` | 初回runの登録・状態表示、追加確認runの登録、取得セルを囲む`phase`によるキャンセル確認と実行フェーズ管理。`mark_completed`は追加確認の設定セルで初回runに対して呼ばれていますが、分析完了を裏付けるものではありません。 |
| `ai_data_scientist.ingestion` | `SourceSpec`、`ingest` | Kaggle SDKで保存した`train.csv`をCSVとして読み込み。出力は`DataFrame`、891行・12列で、コードには切り詰めがないことのassertがあります。 |

ライフサイクルの書込み開始・終了関数と失敗記録関数は`phase`の分岐等にありますが、書込みフェーズや失敗分岐の実行証拠はありません。Notebook内には比較・監査向けの追加importもありますが、その後の関数呼出しはありません。計画文に書かれた`project_manager.enqueue_write`や`mcp_gateway.run_and_record`も、直接の呼出し実績には含めません。

**初回指示**: 分析手法や追加依頼の内容は事前に指定せず、計画、比較対象、図表、判断根拠をAI自身が選ぶよう求めました。取得はKaggle SDKとJupyter MCPに限定し、出典・取得日時・SHA-256、ライフサイクル、データ定義・分析前提のmanifest、意味的異常検査、感度分析、図表監査、全コードセルの上からの再実行も要求しました。これらは依頼内容であり、実施済みの結果とは区別します。

Notebookの計画では、生存・非生存の人数と、性別、客室等級、年齢、運賃、同乗家族数、乗船港、客室情報の有無を比較する方針が示されました。カテゴリには分母付き生存率とWilson 95%区間、連続値には中央値・IQRと分布を使い、性別×等級の層別比較、調整ロジスティック回帰、欠損・外れ値・年齢区分の感度分析を行う予定でした。testや予測ラベルを混ぜない方針、因果推論ではないことも明記されています。ただし、これらの比較・検証を実行するコードは最終Notebookにありません。

**データ取得**: `initial.log`には、Kaggleの`rahulsah06/titanic`から`train.csv`を取得し、891人・12列であったという報告があります。最終Notebookの`acquisition`セルでは、`KaggleApi`の`authenticate`、`dataset_list(search='titanic', page=1)`、`dataset_list_files`、`dataset_download_file`を呼び、CSVを読み込んだ出力が残っています。

検索後、`heptapod/titanic`、`yasserh/titanic-dataset`、`brendan45774/test-file`、`azeembootwala/titanic`、`rahulsah06/titanic`のファイル一覧を確認しています。選定コードはファイル名が`train.csv`であるものを探し、`rahulsah06/titanic`の`gender_submission.csv`、`test.csv`、`train.csv`から`train.csv`を選びました。名前による選定は確認できますが、公式競技データとの同一性検証を行ったわけではありません。

| 項目 | 最終Notebookの取得セルに記録された値 |
|---|---|
| Kaggle参照先 | `https://www.kaggle.com/competitions/titanic` |
| owner/dataset slug | `rahulsah06/titanic` |
| 取得ファイル | `train.csv` |
| 取得日時（UTC） | `2026-10-01T15:26:05.341947+00:00` |
| ファイルサイズ | 61,194 bytes |
| SHA-256 | `7d118fef8b6ccf7f81111877bc388536f7b1e498a655e3d649d19aaa010e9f6f` |
| データ形状 | 891行・12列 |
| 列 | `PassengerId`、`Survived`、`Pclass`、`Name`、`Sex`、`Age`、`SibSp`、`Parch`、`Ticket`、`Fare`、`Cabin`、`Embarked` |

この取得日時は追加確認段階の記録です。初回取得時の日時・ハッシュを別途保存した出力は指定資料にないため、上表を初回取得時の値とは断定しません。先頭3行の表示では`Name`、`Ticket`、`Cabin`を除外しています。取得コードに外部CSVミラーへのフォールバックはなく、指定Notebook・両ログにAPIトークンの表示はありません。

**初回結果**: 確認できる成果は、分析計画、初期設定、データ取得です。`initial.log`の最後の分析者の発言は、取得済みデータを使って性別・等級などの比較と欠損・運賃の偏りを調べるという予告でした。生存・非生存の集計、生存率、属性別の差、信頼区間、回帰係数、感度分析の結果は記録されていません。したがって、生存者と非生存者の違いについて数値を伴う初回結論は得られていません。

**AIが生成した追加依頼1 — 未実施の比較分析と検証の補完**

Notebookの`followup-review-request1`セルには、次の依頼が「原文・実行前記録」として保存されています。

> 生存者と非生存者の違いにまだ答えられていないため、取得済みTitanic train.csvについて列の定義と確度、欠損・重複・意味的異常を記録してください。人数、性別、等級、年齢、運賃、同乗家族数、乗船港、客室情報有無を分母と不確実性付きで比較し、性別×等級の層別、調整ロジスティック回帰、欠損処理・運賃外れ値・年齢区分・同一券依存の感度を確認してください。可視化を保存し、結論を実行済み出力に結び付け、因果や全乗客への一般化は避けてください。

**選定理由**: AIは再評価時のNotebookについて、計画、初期設定、Kaggle取得の3セルだけで、比較結果、反復依頼、図、証拠manifest、完了監査が存在しないと記録しました。問いへの回答を妨げているのは既存結論の細かな不確実性ではなく、比較分析そのものの未実施でした。`followup.log`にも、未実施部分を明記し、追加依頼1回目で比較・定義・異常値・感度分析を行うという説明があります。

**結果・証拠・残る限界**: 依頼文の作成と選定理由は確認できますが、その依頼を実行する分析コードと出力はありません。最終Notebookは5セルで、追加確認の設定セルと依頼文のMarkdownが加わっていますが、比較分析のセルはありません。したがって、この追加依頼を「実施済み」とは扱いません。生存率差、交絡、欠損、外れ値、同一券依存はすべて未検証です。

**追加依頼2・3と反復終了の判断**: 指定Notebook・ログには追加依頼2・3の原文、選定理由、結果はありません。追加依頼1の実行結果を読んで反復不要と判断した記録もなく、最大3回の反復を終えたともいえません。後続依頼や終了理由は補作しません。

**図表**: Notebookの全出力に`image/png`は0件でした。`status.json`の初回・最終監査も`chart_cells: []`です。抽出対象のPNGがないため、`benchmark/figures`に保存する図表ファイルはなく、節内の画像参照・キャプションもありません。未実施の分析を補うための図や、存在しない`figures/exp-01-...`へのリンクは作成していません。

**最終結論**: Kaggle公開データの検索、取得、読み込みと出典記録までは確認できました。一方、本来の問いである「生存者と非生存者にどのような違いが見られるか」には、保存された実行結果だけでは回答できません。v0.2.0実験01は、分析と反復検証の完了を確認できない実験として評価します。別版・別実験のTitanicの生存率や回帰結果を、この実験の結果として転用していません。

**監査・再現性**: 外部の`status.json`に記録された初回・追加確認の状態は次のとおりです。これは監査状態ファイルの報告値であり、Notebook内で監査関数を実行した出力とは区別します。

| 項目 | 初回 | 追加確認後 |
|---|---|---|
| 所要時間 | 286.5秒 | 226.6秒 |
| exit code | 0 | 0 |
| 終了理由 | `artifact_complete_cutoff` | `artifact_complete_cutoff` |
| ファイル安定判定 | `stable: true`、13,700 bytes | `stable: true`、16,417 bytes |
| Notebook存在・形式 | `exists: true`、`nbformat_valid: true` | `exists: true`、`nbformat_valid: true` |
| コードセル数／実行済み数 | 2／2 | 3／3 |
| 未実行・エラーセル | いずれも空配列 | いずれも空配列 |
| 図表セル／Insightセル数 | 空配列／0 | 空配列／0 |
| 指摘／視覚的指摘 | `findings: []`／`visual_findings: []` | `findings: []`／`visual_findings: []` |
| 意味的完了判定 | `semantic_complete: true` | `semantic_complete: true` |

`status.json`全体も`semantic_complete: true`で、完了日時は`2026-10-01T15:27:36.210271+00:00`です。しかし、最終Notebookに残ったコードセルは`setup`、`followup-setup`、`acquisition`の3つだけで、実行番号は順に1、4、5でした。比較結果が存在しない以上、ファイルの安定や実行済みセルの無エラーだけでは、分析課題の完了を証明できません。コードセルがすべて実行済みであることと、必要な分析セルが作成・実行されたことは別の条件です。

Notebook内に`visual_audit=True`で監査を呼んだコードや監査結果はなく、図表・根拠付きInsight・データ定義manifest・分析前提manifestもありません。ライフサイクルは、初期設定の出力で`v020-exp-01`が`running`、実行・書込み・ロックの各カウンタが0と表示されています。追加確認の設定セルでは初回runに`mark_completed`を呼び、`v020-exp-01-followup`を登録していますが、追加確認runの最終`completed`／`failed`状態を出力した記録はありません。

全コードセルを上から再実行するという計画はありますが、カーネル再起動・全セル再実行のログや最終確認出力は指定資料にありません。実行番号1、4、5だけから再実行の成功・失敗は断定できません。CSVのSHA-256はNotebookの取得時出力として確認できる一方、今回の報告では指定外のCSVを使った独立検算や再取得はしていません。v0.2.0ベンチマークという位置づけは依頼に従っていますが、指定資料にはパッケージ版・コミット・依存関係の版一覧を確認できる実行出力がありません。

**失敗内容と原因の切り分け**: 初回・追加確認の両ログは、次の外部ランナーの記録で終わっています。

> [runner] stopping process group: Notebook remained stable and passed semantic audit

これと`artifact_complete_cutoff`から、外部ランナーがNotebookの安定と監査通過を理由にプロセスグループを停止したことは確認できます。比較結果がない段階で完了判定が記録された点は、分析成果物の内容と停止判定の不一致です。exit codeが0でも、分析者が必要な作業を終えて自然終了した証拠にはなりません。ランナーの実装や判定条件は指定資料にないため、停止判定の内部原因や修正箇所までは特定できません。

| 区分 | 確認できる事実と帰属の限界 |
|---|---|
| 外部ランナー | 両段階で停止記録があり、`status.json`は比較結果なしでも意味的完了と判定。停止・完了判定の問題として切り分けます。 |
| Copilot CLI | 分析者は未実施部分を認識し、分析を続ける意図と追加依頼を記録。CLI固有のエラーや内部障害を示す記録はなく、比較分析の欠落をCLIの不具合とは断定できません。 |
| Kaggle API | 検索、ファイル一覧、取得、CSV読み込みの出力あり。API失敗や認証失敗による停止は記録されていません。 |
| Jupytermind本体 | 直接呼出しのある準備・取得処理にエラー出力なし。監査関連モジュールのimportはありますが監査関数の直接呼出し・出力はなく、外部状態ファイルの判定を本体の不具合と結び付ける証拠はありません。 |

この資料だけで再現手順と期待・実際の挙動を特定できるJupytermind本体の改善候補はありません。外部ランナーの停止問題を本体の課題として登録せず、`benchmark/runs/01-kaggle-exp-01-titanic/issue-candidate.json`にはJSONの`null`を保存しました。これは本体に問題がないことの証明ではなく、今回の証拠範囲では帰属できないという判断です。

**残る限界**: 未実施の比較・感度分析を推測で補えないため、性別、等級、年齢、運賃などと生存の関連の大きさや不確実性は評価できません。欠損率、重複件数、異常値数、ID範囲も実行出力に集計がありません。公式競技ファイルとのバイト同一性、取得データの全件の意味的妥当性、観測の独立性も未検証です。

Notebookの計画では、観測された学習用部分標本であること、家族・同一券による依存、標本選択、運賃の測定単位、年齢欠損を注意点として挙げています。これらは分析上の注意として妥当な検討対象ですが、この実験で検査・調整済みとはいえません。また、コードと出力の保存だけでは実際のJupyter MCP呼出し経路やカーネル再起動まで独立に検証できません。証拠は指定されたNotebook、`initial-prompt.md`、`initial.log`、`followup.log`、`status.json`に限定し、既存の白書は節の書式・詳細度の参考にのみ使用しました。
