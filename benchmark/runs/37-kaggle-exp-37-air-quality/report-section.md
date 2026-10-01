## 実験37: Air Quality（Copilot CLIのモデル一覧取得タイムアウトによる起動失敗・分析未完了）

**課題**: 「Kaggleの大気質時系列データを使い、主要汚染物質の時間変化、季節性、気象条件との関連を調べてください。単位、欠測、観測地点を確認し、相関を排出源の因果効果と混同しない日本語の結論を示してください。」

**初回プロンプト（全文・原文）**: 以下は、データセットと問い、および共通制約からAIが自動生成した初回プロンプトです。人間が実験37の全文を個別に作成したものではありません。`initial-prompt.md` に保存された全文を掲載します。

> Kaggleの大気質時系列データを使い、主要汚染物質の時間変化、季節性、気象条件との関連を調べてください。単位、欠測、観測地点を確認し、相関を排出源の因果効果と混同しない日本語の結論を示してください。 Kaggle参照先: https://www.kaggle.com/datasets?search=air+quality+time+series。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。Kaggle APIで対応データを取得できない場合は、`/home/nahisaho/kaggle/experiments/white-paper.md`を確認してください。同じデータセットの公開CSVが同稿に明記されている場合だけ、そのURLへフォールバックしてください。対応するCSVを確認できない場合は、別データを推測で選ばず、取得失敗として記録してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-37-air-quality/notebooks/kaggle-v020-kaggle-exp-37-air-quality.ipynb としてください。run_idは `v020-exp-37` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。

**使用したJupytermindモジュール**: Notebookで直接import・呼び出したモジュール名、関数名、使用目的を確認できる記録はありません。指定先のNotebookが存在しないため、使用実績は確認不能です。初回指示にある `lifecycle.register_run` は実行・書込み・終了状態を記録するための要求、`notebook_audit` は最終監査の要求であり、実際に呼び出された関数としては数えません。その他のモジュールも、想定される分析手順から使用済みとは推測しません。

**初回指示**: 主要汚染物質の時間変化・季節性・気象条件との関連を、単位・欠測・観測地点を確認したうえで調べる依頼でした。相関から排出源の因果効果を断定しないことも求めています。データ取得はJupyter MCP実行セル内のKaggle Python SDKを使用し、取得元・ファイル名・取得日・SHA-256を記録する条件でした。Kaggle検索URLは候補探索の入口であり、特定のowner/dataset slugは指定されていません。フォールバックも、指定文書に同じデータセットの公開CSVが明記されている場合に限定されています。分析前提・データ定義・意味的異常・感度分析・図表監査・ライフサイクルの記録、AI自身による最大3回の追加依頼、全コードセルの再実行も要求されていますが、これらは実施結果ではなく初回の要求事項です。

**データ取得**: 指定証拠には、Kaggle認証・データセット検索・ファイル一覧取得・ダウンロードの実行記録がありません。取得したowner/dataset slug、ファイル名、取得日、SHA-256、行数・列数はいずれも確認できません。公開CSVへのフォールバック実施も確認できません。今回の停止はKaggle APIの取得失敗ではなく、データ取得を確認できる段階に達する前のCopilot CLI起動失敗です。Kaggle APIの認証状態、サービスの応答、対象データの取得可能性は評価していません。

**初回結果**: `initial.log` に記録されたのは、分析結果ではなく次の起動エラーです。

```text
Error: Failed to load models

Error: Model catalog request timed out after 30000ms

Copilot could not retrieve the list of available models.
```

ログ末尾には、Copilot CLI終了後の外部ランナーによる後処理が記録されています。

```text
[runner] stopping process group: Copilot CLI exited; cleaning descendant runtimes
```

`status.json` は初回終了コードを `initial_exit_code=1`、初回所要時間を `initial_seconds=48.0`、終了種別を `initial_termination="exited"` と記録しています。モデル一覧要求のタイムアウトはログ上の30,000 msであり、ランナーが記録した初回処理全体の48.0秒とは区別します。ベンチマーク全体の時間制限到達を意味する記録ではありません。

指定先にNotebookはなく、汚染物質の濃度・時系列傾向・季節差・気象との相関を示す数値、図表、根拠付きInsightは確認できません。「季節性がない」「気象との関連がない」という分析結果ではなく、問いへの回答を得られなかった状態です。

**AIが生成した追加依頼（原文・選定理由・結果）**: 確認できる追加依頼はありません。初回ログにAIが生成した追加依頼文・選定理由・追加分析結果はなく、反復依頼履歴を確認するNotebookも存在しません。指定された `followup.log` も存在せず、`status.json` の `followup_exit_code`、`followup_seconds`、`followup_termination` はすべて `null` です。したがって、追加依頼を実施したという証拠はありません。原文・理由・結果を補作せず、確認不能として扱います。これは「AIが価値ある追加分析はないと判断した」ことを示す記録でもありません。

**最終結論**: 実験37は、Copilot CLIが利用可能なモデル一覧を取得できず、起動段階で終了したため、分析未完了です。`analysis_complete=false`、`final_completion.ready=false` と、指定Notebookが存在しない現状は整合しています。大気質の時間変化、季節性、気象条件との関連について、実験に基づく結論は出せません。分析を実行していないため、相関と因果を区別した解釈の品質やJupytermind v0.2.0の分析性能を評価する結果にもなっていません。

**監査・再現性**: 証拠の確認範囲は `initial-prompt.md`、`initial.log`、`status.json` の実内容、および指定Notebook・`followup.log` の不存在です。節の書式・詳細度は参照文書に合わせていますが、別実験の結果を本実験の証拠には使用していません。

| 確認項目 | 指定証拠で確認できた状態 |
|---|---|
| 実験・実行識別子 | 実験37、`run_id=v020-exp-37` |
| 指定Notebook | `benchmark/projects/kaggle-v020-kaggle-exp-37-air-quality/notebooks/kaggle-v020-kaggle-exp-37-air-quality.ipynb`。実ファイルは存在しない |
| 初回実行 | 終了コード1、所要時間48.0秒、終了種別 `exited` |
| 初回・最終の成果物確認 | `initial_stability.exists=false`、`final_stability.exists=false`。安定性確認はいずれも `stable=false` |
| 初回・最終監査の記録 | `initial_audit`、`final_audit` の `exists=false`、`error="notebook_missing"` |
| 分析完了 | `analysis_complete=false`、`final_completion.ready=false` |
| 最終完了要件 | `final_completion.requirements` の8項目すべてが `false`。構造監査、最低実行セル数、図表出力、証拠付きInsight、反復履歴、モジュール使用記録、改善候補記録、Notebook監査呼び出しの要件充足は確認されていない |
| 追加確認 | 指定 `followup.log` は不存在。追加確認の終了コード・時間・終了種別は `null` |
| 状態記録の時刻 | `completed_at="2026-10-01T22:11:53.064301+00:00"`。このフィールドの存在を分析成功とは解釈しない |

Notebookがないため、全コードセルの上からの再実行、`notebook_audit` の呼び出し、`visual_audit=True` の図表監査、ライフサイクルの `completed` または `failed` 記録を確認できません。成果物不在による完了要件未充足と、実際に分析コードを実行して監査で不合格になった状態は区別します。データの取得元・ハッシュ・実行セル・計算結果がないため、分析の再現性は検証できません。

**図表**: 指定Notebookが存在せず、抽出元となるPNG出力を確認できません。したがって、本実験のPNGは `benchmark/figures` に保存しておらず、節内にも画像参照は設けていません。別実験の図や、今回新たに作成した図で分析結果を代替しません。

**失敗内容と責任範囲**: 直接確認できる失敗は、Copilot CLIのモデル一覧要求が30,000 msでタイムアウトしたことです。ログにはトークン設定の確認、再認証、認証状態の確認、再試行などの案内がありますが、これらは一般的な対処案であり、本実験の認証不備や具体的な根本原因を確定する証拠ではありません。ネットワーク、認証、サービス側のいずれに原因があるかは特定できません。外部ランナーについてはCLI終了後のプロセス群停止・後処理の記録があるだけで、ランナー自身の不具合を示す証拠はありません。Kaggle APIの失敗応答や、Jupytermindモジュールの実行エラーも記録されていません。

**Jupytermind改善候補**: 指定証拠からJupytermind固有の不具合・機能不足を裏づける候補はありません。Copilot CLIのモデル一覧取得失敗をJupytermindの問題に読み替えず、`issue-candidate.json` にはJSONの `null` を保存します。これは未実行のモジュールに問題がないことを保証する判定ではなく、この実験から再現手順・実際の挙動・受け入れ条件を持つJupytermind固有の候補を立てられないという意味です。

**残る限界**: 対象データが確定しておらず、観測地点・期間・測定単位・欠測の定義、時間間隔、汚染物質と気象変数の対応を評価できません。時系列の自己相関、季節性、地点差、欠測処理への感度、排出源や気象による交絡も検証していません。また、起動失敗の詳細原因、復旧・再試行の結果、追加依頼を生成しなかったAIの判断過程は指定証拠から確認できません。本実験から報告できるのは実行基盤で停止した事実であり、大気質に関する科学的な知見や、Jupytermindの分析能力に関する成否ではありません。
