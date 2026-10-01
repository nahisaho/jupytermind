## 実験48: COVID-19 Cases（Copilot CLI起動失敗・分析未実施）

**課題**: 「KaggleのCOVID-19国別または地域別時系列データを使い、症例・死亡の波と地域差を調べてください。報告遅延、検査体制、人口規模、定義変更を確認し、単純な国比較や政策の因果効果を断定しない日本語の分析を作成してください。」

**初回プロンプトの生成**: 初回プロンプトは、データセットと問い、および共通制約からAIが自動生成したものです。人間が実験48の全文を個別に作成したものではありません。以下は `initial-prompt.md` に保存された全文であり、指示された処理と実際に実行された処理は区別します。

**初回プロンプト（全文・原文）**:

> KaggleのCOVID-19国別または地域別時系列データを使い、症例・死亡の波と地域差を調べてください。報告遅延、検査体制、人口規模、定義変更を確認し、単純な国比較や政策の因果効果を断定しない日本語の分析を作成してください。 Kaggle参照先: https://www.kaggle.com/datasets?search=covid+19+cases+time+series。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。Kaggle APIで対応データを取得できない場合は、`/home/nahisaho/kaggle/experiments/white-paper.md`を確認してください。同じデータセットの公開CSVが同稿に明記されている場合だけ、そのURLへフォールバックしてください。対応するCSVを確認できない場合は、別データを推測で選ばず、取得失敗として記録してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-48-covid-cases/notebooks/kaggle-v020-kaggle-exp-48-covid-cases.ipynb としてください。run_idは `v020-exp-48` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。

**使用したJupytermindモジュール**: Notebookで直接import・呼び出したモジュール名、関数名、使用目的を確認できる記録はありません。指定Notebookが存在しないため、使用済みとして列挙できるモジュールはありません。プロンプトにある `lifecycle.register_run`、`notebook_audit`、`visual_audit=True` は実行要件であり、呼び出し実績ではありません。

**初回指示**: 症例と死亡の時間的な波、国・地域差を調べるとともに、報告遅延、検査体制、人口規模、定義変更による比較の限界を確認する依頼でした。分析手法や比較地域、追加分析の内容は事前指定せず、AIに判断を委ねています。取得元とハッシュの記録、manifest、異常検査、感度分析、図表監査、最大3回の自律追加依頼、全コードセルの再実行と監査も要求しています。ただし、以下の起動失敗により、これらを実施した証拠はありません。

### データ取得

Kaggle参照先はCOVID-19症例時系列データの**検索URL**であり、採用されたowner/dataset slugではありません。指定資料には、Kaggle SDKの認証・検索・ファイル一覧取得・ダウンロードの実行記録がありません。データセットの選定、取得ファイル名、取得日、SHA-256、行数、列構成、対象国・地域、対象期間はいずれも確認できません。

初回指示では、Kaggle APIで取得できない場合に限り、指定の既存稿に明記された同一データセットの公開CSVへフォールバックすることが許可されていました。しかし、その条件確認やフォールバックの実行を示す記録もありません。**本件はKaggle APIによる取得失敗を観測した実験ではなく、データ取得に到達した証拠のない起動失敗です。**

### 初回結果と失敗内容

**データ分析の初回結果は得られていません。** `initial.log` はCopilot CLIのモデル一覧取得段階で次のエラーを記録しています。

```text
Error: Failed to load models

Error: Model catalog request timed out after 30000ms

Copilot could not retrieve the list of available models.
```

`status.json` の初回実行記録は `initial_exit_code=1`、`initial_seconds=44.7`、`initial_termination="exited"` です。ログの30,000 msはモデルカタログ要求のタイムアウト値であり、44.7秒はランナーが記録した初回実行の所要時間です。分析時間やデータ取得時間を意味しません。

ログ末尾には次のランナー処理が記録されています。

```text
[runner] stopping process group: Copilot CLI exited; cleaning descendant runtimes
```

これはCLI終了後の子孫ランタイムのクリーンアップ記録であり、分析成功やJupytermindのライフサイクル完了を示すものではありません。症例数、死亡数、波の時期、地域差、統計量、Insight、図表を裏付ける出力はありません。

### AIが生成した追加依頼

**追加依頼の原文・選定理由・実行結果を確認できる記録はありません。** 指定された `followup.log` は存在せず、`status.json` の `followup_exit_code`、`followup_seconds`、`followup_termination` はいずれも `null` です。Notebook内の「反復依頼履歴」も確認できません。

したがって、追加依頼1〜3の文面や結果を補作しません。また、「AIが初回結果を評価して追加不要と判断した」「AIが追加分析を拒否した」とも解釈しません。初回分析が成立しておらず、追加依頼の生成・実行や不要判断を示す証拠がないためです。

### 最終結論

本実験は、**Copilot CLIのモデルカタログ取得タイムアウトにより起動段階で終了し、COVID-19の分析は未完了**です。判断根拠は、初回ログのエラー、指定Notebookの不在、`status.json` の `analysis_complete=false` と `final_completion.ready=false` です。

症例・死亡の波や地域差について、データに基づく結論はありません。「地域差がない」「政策効果がない」という分析結果でもありません。報告遅延、検査体制、人口規模、定義変更が結果へ与える影響も評価できていません。Jupytermind v0.2.0の分析能力、反復の有効性、図表やInsightの品質を、この実行から評価することはできません。

### 監査と再現性

| 項目 | 指定資料で確認できる状態 |
|---|---|
| 実験識別子 | 実験48、`run_id="v020-exp-48"` |
| 初回実行 | 終了コード1、所要44.7秒、終了区分 `exited` |
| 初回・最終の成果物確認 | `initial_stability`、`final_stability` とも `exists=false`、`stable=false` |
| 指定Notebook | `benchmark/projects/kaggle-v020-kaggle-exp-48-covid-cases/notebooks/kaggle-v020-kaggle-exp-48-covid-cases.ipynb` は存在しない |
| 追加確認ログ | `benchmark/runs/48-kaggle-exp-48-covid-cases/followup.log` は存在しない |
| 監査状態 | `initial_audit`、`final_audit`、`final_completion.audit` は `exists=false`、`error="notebook_missing"` |
| 最終完了判定 | `analysis_complete=false`、`final_completion.ready=false` |
| 完了要件 | `final_completion.requirements` の構造監査、実行済みセル、図表、証拠付きInsight、反復履歴、モジュール使用記録、改善候補記録、監査呼び出しの全8項目が `false` |
| セル再実行・監査呼び出し | 全コードセル再実行、`notebook_audit`、図表の視覚監査を実施した記録はない |
| ライフサイクル | `lifecycle.register_run`、実行・書込みフェーズ、`completed` または `failed` の記録を確認できない |
| データ来歴 | owner/dataset slug、取得ファイル、取得日、SHA-256を確認できない |
| 状態記録時刻 | `completed_at="2026-10-01T23:31:18.279567+00:00"`。状態記録の時刻であり、分析成功を意味しない |

完了要件の `false` は、今回の成果物不在のもとで要件を満たせていないことを表します。実際にNotebookを実行・監査して、8種類の分析不具合を検出したという意味ではありません。データファイルも実行済みNotebookも確認できないため、データ分析の再現性は検証できません。

**図表**: 指定Notebookが存在しないため、埋め込みPNGを抽出できません。`benchmark/figures` へ本実験の画像を新規保存しておらず、存在しない `figures/exp-48-...` への参照や代替図表は掲載しません。

本節の実験証拠は、指定された `initial-prompt.md`、`initial.log`、`status.json` の内容と、指定Notebook・`followup.log` の不在です。既存稿は節の書式・詳細度の参照にのみ用い、他実験の数値、データ取得履歴、監査結果を本実験の証拠にはしていません。

### Jupytermind改善候補と外部要因の切り分け

| 分類 | 観測内容と判断 |
|---|---|
| Copilot CLI | モデルカタログ要求が30,000 msでタイムアウトし、モデル一覧取得に失敗。今回直接観測された起動失敗である |
| 外部ベンチマークランナー | 終了コード1、成果物不在、完了要件未充足、CLI終了後のクリーンアップを記録。指定証拠だけではランナー固有の不具合を特定できない |
| Kaggle API | 呼び出し結果がなく、認証・通信・取得の成否は評価不能。Kaggle API障害とは判定しない |
| Jupytermind | Notebookでの直接import・呼び出しを確認できず、固有の不具合・機能不足を裏付ける再現証拠はない |

初回ログは認証確認や再試行などの一般的な対処案を示していますが、認証不備、ネットワーク障害、サービス側の状態のいずれが原因かは特定できません。ログに対処案があることを、原因が検証された証拠とは扱いません。

**Jupytermind改善候補はなし**とし、`benchmark/runs/48-kaggle-exp-48-covid-cases/issue-candidate.json` にはJSONの `null` を保存します。これはJupytermindに欠陥がないという証明ではなく、今回の指定証拠から登録可能な候補を特定できないという判断です。

### 残る限界

本実験から確認できるのは、分析開始前の外部CLI起動失敗と成果物不在までです。COVID-19データの品質、報告定義の整合性、人口当たり指標の妥当性、波の比較可能性、政策の因果効果については検証していません。追加確認ログがないため、復旧試行や追加実行の詳細も確認できません。

未確認の成功状態、データ件数、統計結果、図表、モジュール利用を推測せず、**「分析結果がないこと」と「分析で差が見つからなかったこと」を区別して報告する実験**です。
