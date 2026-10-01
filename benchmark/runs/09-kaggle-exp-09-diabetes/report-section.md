## 実験09: Pima Indians Diabetes（分析完了）

**課題**: 「KaggleのPima Indians Diabetesデータを分析し、糖尿病アウトカムと関連する特徴を調べてください。」

**初回プロンプト（全文・原文）**:

> KaggleのPima Indians Diabetesデータを分析し、糖尿病アウトカムと関連する特徴を調べてください。欠損や不自然な値の扱いは自分で判断して明記し、比較に適した図表を選んで、相関を因果と誤認しない日本語の結論を示してください。AI Data Scientist SkillとJupyter MCPで計画、実行コード、出力、根拠付きInsightを保存し、ノートブックの再実行も確認してください。 Kaggle参照先: https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。Kaggle APIで対応データを検索・取得できなかった場合に限り、`/home/nahisaho/kaggle/experiments/white-paper.md`に記載された旧実験の公開CSV `https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv` を取得して実験を継続してください。その場合はKaggle APIの失敗内容、フォールバックした理由、CSV URL、取得日時、SHA-256をNotebookに記録し、公開CSVとKaggle掲載版の完全な同一性は保証されないことを明記してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-09-diabetes/notebooks/kaggle-v020-kaggle-exp-09-diabetes.ipynb としてください。run_idは `v020-exp-09` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。

**使用したJupytermindモジュール**: 以下は、指定Notebookのコードセルで直接importされ、呼出しコードと対応する実行出力を確認できるAPIです。モジュール名はすべて `ai_data_scientist` 配下です。

| モジュール | 直接呼び出した関数・クラス・メソッド | 使用目的 |
|---|---|---|
| `project_manager` | `resolve_project`, `ensure_notebook`, `ensure_data_dir`, `enqueue_write` | 保存先とデータ配置先の解決・作成、最終監査前の根拠参照の直列書込み |
| `language_router` | `detect_language` | 日本語の出力言語判定 |
| `lifecycle` | `register_run`, `is_cancel_requested`, `mark_execution_start`, `mark_execution_end`, `mark_write_start`, `mark_write_end`, `mark_completed`, `get_run_status` | 実行登録、キャンセル確認、実行・書込みフェーズ、終了状態の記録 |
| `ingestion` | `SourceSpec`, `ingest` | CSV読込みと行数上限・切詰め有無の確認 |
| `cleaning` | `clean_dataset` | 重複除去と処理前後の行数確認 |
| `eda` | `explore` | 記述統計、型、非欠損件数、欠損率の確認 |
| `stats_analysis` | `correlation` | 各特徴と二値OutcomeのPearson相関（点双列相関）・p値・日本語解釈 |
| `visualization` | `render_chart`, `build_image_output` | Outcome別件数の棒グラフ、PNGのNotebook出力化 |
| `data_definition` | `build_manifest`, `DataDefinitionManifest.unresolved_fields` | 出典・変数定義・単位・不明項目の記録 |
| `analysis_assumptions` | `Assumption`, `AnalysisAssumptionManifest`, `check_manifest` | 分析スコープと前提の記録、結論に重要な未検証前提の警告 |
| `data_quality` | `detect_anomalies` | 範囲・許容カテゴリ・欠損に関する意味的な異常検査 |
| `sensitivity` | `SensitivityPlan`, `run_sensitivity` | 欠損処理・極端値処理、年齢の関数形・対象範囲による係数の安定性確認 |
| `notebook_audit` | `audit_notebook(visual_audit=True)` | 実行状態、エラー、根拠参照、図表の監査 |

Notebookのモジュール利用記録には、制御Notebookからの `insight_engine.extract_cited_value`・`record_insight` 利用も記載されています。ただし、指定Notebookでは `insight_engine` のimportだけで、これらの呼出しコードは確認できないため、上表の直接使用には含めません。同様に `data_definition.FieldValue` は利用記録にはありますが、指定コードセルでの呼出しは確認できません。`lifecycle.mark_failed` は例外ハンドラに定義されているだけで、正常終了経路の実利用には含めません。ブートストラップ、GLM、スプライン、VIF、Wilson区間はNumPy・SciPy・statsmodels・patsyによる処理で、Jupytermindの提供機能とは区別します。

**初回指示と今回の実行範囲**: 欠損・不自然な値の判断、比較方法と図表の選定、因果と相関の区別をAIに委ねました。一方、取得経路、出典・ハッシュ、manifest、感度分析、最大3回の反復、全セル再実行と監査は必須条件です。`initial.log` は「指定先には既存の分析ノートブックがあり、3回の追加分析まで記録されています」と報告しています。したがって、以下の初回結果・追加依頼は、指定Notebookに保持された分析履歴と今回の再実行出力として報告します。今回の初回CLIセッションで3依頼を新たに生成したとは扱いません。

**データ取得**: Notebookの `acquisition` セルはKaggle SDKで認証・検索・ファイル一覧取得・ダウンロードを実行しています。指定slug `uciml/pima-indians-diabetes-database` の `dataset_list_files` はHTTP 403、次の候補 `ahmedgamelwaly/pima-indians-diabetes` は対象の `diabetes.csv` が一覧に存在しないため `FileNotFoundError` でした。その後、実際の検索結果にある `harsh146/pima-indians-diabetes` から取得できています。

| 項目 | 最終採用データの記録 |
|---|---|
| 取得元 | `https://www.kaggle.com/datasets/harsh146/pima-indians-diabetes` |
| ファイル | `diabetes.csv` |
| 取得日時（UTC） | `2026-10-01T20:14:59.960109+00:00` |
| SHA-256 | `698c203a14aa31941d2251175330c9199f3ccdb31597abbba2a3e35416257a72` |
| データ形状 | 768行・9列 |
| Outcome | 0が500件、1が268件（34.9%） |

今回の取得出力は `source_kind="kaggle"`、`kaggle_failure=null`、`fallback_reason=null` で、最終分析はKaggleから新規取得したファイルを使用しています。認証情報は出力せず、API例外も型・段階・HTTP状態だけを記録しています。指定uciml版は取得できておらず、最終採用版との完全な同一性は未検証です。

これとは別に、Notebookの「初期取得履歴」には、以前の検索不足による `LookupError` と、その後の指定slug照会時の `HTTPError` を受け、Plotly公開CSVへ一時フォールバックした記録があります。URLは `https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv`、取得日時は `2026-10-01T18:32:53.214381+00:00` と `2026-10-01T18:33:15.873031+00:00`、ファイルは `diabetes.csv`、SHA-256はいずれも上記と同じです。この過去の取得はNotebook内の履歴記述を証拠とし、今回のログに実行詳細があるとは扱いません。同じハッシュは保存バイト列の一致を示すだけで、取得できなかったuciml版との同一性の証明ではありません。

**前処理・前提確認**: 元データの通常のNAと完全重複はともに0件でした。Glucose・BloodPressure・SkinThickness・Insulin・BMIのゼロは生理的に不自然な欠測符号と判断してNaNに変換し、妊娠回数とOutcomeのゼロは保持しました。変換件数はそれぞれ5・35・227・374・11件です。特にInsulinは48.7%、SkinThicknessは29.6%が欠損となり、列ごとの観測標本が大きく異なります。正の高値は誤入力と断定せず主解析に保持し、1・99パーセンタイルへのWinsor化は感度分析に限定しました。

データ定義manifestは取得URL・ハッシュ・行数を確認済みとし、母集団、変数定義・単位は推定、ライセンス・抽出方法・診断基準・測定時点は不明としています。分析前提manifestでは、ゼロを欠損とする判断、行の独立性、Outcomeの意味について、結論に重要な未検証前提の警告が3件残っています。意味的検査の範囲は診断閾値ではなく、ゼロなどのコード異常を検出する便宜的な範囲です。

![Outcome別のゼロ由来欠損率](figures/exp-09-missingness-by-outcome.png)

*ゼロを欠損へ変換した後のOutcome別欠損率。InsulinとSkinThicknessでは欠損が多く、観測値だけの比較を全標本へそのまま一般化できません。*

![Outcome別の観測件数](figures/exp-09-outcome-counts.png)

*Outcome=0は500件、Outcome=1は268件。陽性割合はこの標本の構成であり、一般集団の有病率を示すものではありません。*

**初回結果**: AIは観測値による群別分布、標準化平均差Hedges g、群別2,000回ブートストラップの95%区間、点双列相関と8特徴のBH補正を比較しました。Glucoseの中央値はOutcome=0で107、1で140、Hedges gは1.191625（95%区間1.018159–1.366606）、点双列相関は0.494650でした。BMIの中央値は30.1対34.3、Hedges gは0.690379、相関は0.313680です。Glucoseは比較した8特徴で最も明瞭な単変量関連を示しましたが、列ごとに観測数が異なるため順位は探索的です。

![Outcome別の8特徴の観測値分布](figures/exp-09-feature-distributions-by-outcome.png)

*各特徴の箱ひげ図と群別観測数。欠損は補完せずに比較し、正の極端値も表示しています。測定単位は未検証のため、図では元の数値尺度を使っています。*

![8特徴の標準化群間差と95%区間](figures/exp-09-standardized-feature-differences.png)

*Outcome=1から0を引いたHedges gと群別ブートストラップ95%区間。Glucoseの差が最も大きく、差の方向・不確実性を共通尺度で比較できます。*

調整分析は8特徴と5列の欠損指示変数を用いたロジスティック回帰です。主解析ではOutcomeを参照しない全体中央値補完を行い、観測値の標準偏差を共通の標準化基準にしました。

| 特徴 | 主解析の調整OR／観測値1SD | 95%信頼区間 |
|---|---:|---:|
| Glucose | 3.174604 | 2.506819–4.020279 |
| BMI | 1.943998 | 1.520736–2.485064 |
| DiabetesPedigreeFunction（家族歴指標と推定） | 1.382029 | 1.133036–1.685740 |
| Pregnancies | 1.520750 | 1.226827–1.885091 |
| Age | 1.153578 | 0.924243–1.439819 |

中央値補完／完全例と、高値保持／Winsor化を組み合わせた4仕様では、GlucoseのORは3.154560–3.217435、係数の最大相対変動は0.011601で `stable=True` でした。一方、BMIは係数が26.5%、家族歴指標は28.3%変動して `stable=False` です。正の方向が一貫することと、関連の大きさが安定していることを区別しました。`stable` の基準は係数の相対変動20%以内であり、OR自体の変動率や因果妥当性を意味しません。

**AIが生成した追加依頼1 — 完全例選択と共線性**

> 欠損処理によってBMIや年齢の調整関連が変わっています。完全例として残る人と除外される人のOutcome比率・主要特徴を比較し、欠損の少ない5特徴だけのモデルと全8特徴モデルを比べて、選択バイアスと共線性が結論を左右するか確認してください。

**選定理由**: BMIの係数が完全例処理で約26.5%変動し、年齢はさらに変動しました。全8特徴の完全例は392件と約半数になるため、標本選択とモデル調整の影響を分離する必要があると判断しています。

**結果・証拠**: `iteration-1` セルの出力では、完全例392件のOutcome=1割合は33.2%、除外376件は36.7%、年齢中央値は27対32でした。Fisher検定はp=0.325164ですが、非有意は欠損が無作為である証明ではありません。VIF最大は1.616142で、極端な共線性は確認されませんでした。欠損の少ない5特徴（Glucose・BMI・Age・Pregnancies・家族歴指標）のモデルでは、中央値補完768件／完全例752件でGlucoseのORは3.002663／2.996616、BMIは1.860849／1.833338と近い値でした。欠損の多い特徴をすべて含めた完全例解析の標本選択には注意が必要で、欠損機序と個人ID不在による独立性は未解決です。

**AIが生成した追加依頼2 — 非線形性と分布の歪み**

> 年齢は単変量では正の関連がある一方、調整後は不確実です。年齢とGlucoseの非線形性、およびInsulinなどの右裾の長い分布を考慮したモデルで主要な関連を再確認し、単変量の関連と調整後の関連を混同しない結論に更新してください。

**選定理由**: 反復1では極端な共線性は確認されなかった一方、完全例の年齢構成と調整後の直線係数には問題が残りました。年齢とOutcomeの関連形状、右裾の長い分布が解釈を左右する可能性を調べるための依頼です。

**結果・証拠**: `iteration-2` セルでは、年齢スプライン追加の探索的尤度比検定がLR=24.113894、追加自由度3、p≈2.36×10⁻⁵で、直線モデルより適合が改善しました。Glucose単独のスプライン追加はp=0.325376でした。年齢を非線形に扱うと妊娠回数のORは1.189143（95% CI 0.938686–1.506426）となり、「独立した正の関連がある」という単純な断定を取り下げています。

同じ年齢スプラインモデルでGlucoseのORは3.236985、BMIは1.850463、家族歴指標は1.367428で、95%区間はいずれも1を上回りました。Insulinと家族歴指標を `log1p` 変換したモデルでもGlucoseは3.048077、BMIは1.914501で正の関連が残りました。ただし、変換した特徴のORは変換後の1SDあたりで、元尺度のORと同一には扱いません。非線形モデルのAge・Glucoseも単一ORでは要約しません。事後的なモデル探索、単一補完、曲線の点ごとの信頼区間という限界が残ります。

![年齢スプラインによるモデル上のOutcome確率](figures/exp-09-age-spline-outcome-probability.png)

*他の観測特徴を平均値、欠損指示変数を0に固定した年齢21〜70のモデル曲線と点ごとの95%区間。年齢を変える介入効果ではなく、高齢端の下降を予防効果と解釈できません。*

![主解析の8特徴の調整オッズ比](figures/exp-09-adjusted-odds-ratios.png)

*中央値補完と欠損指示変数を用いた直線モデルの調整ORと95%区間。反復2のセルに出力されていますが、年齢スプラインモデルの係数図ではありません。妊娠回数の解釈は追加分析で更新されました。*

**AIが生成した追加依頼3 — 高齢端の標本数と年齢モデル感度**

> 年齢を非線形に扱うと妊娠回数の調整関連が弱まり、年齢曲線の高齢端では下降が見られます。年齢帯ごとの標本数とOutcome割合を確認し、スプライン自由度3〜5および60歳以下に限定した感度分析で、Glucose・BMI・家族歴指標・妊娠回数の結論が安定するか調べてください。高齢で糖尿病が予防されると解釈しないでください。

**選定理由**: 年齢スプラインで妊娠回数のORが約1.52から1.19へ弱まり、年齢曲線の高齢端にも下降が見られました。少数標本の形状を一般化しないよう、年齢帯ごとの観測数と関数形・対象範囲の感度を確認する最後の反復です。

**結果・証拠**: `iteration-3` セルの年齢帯別出力は次のとおりです。

| 年齢帯 | 件数 | Outcome=1件数 | Outcome=1割合 | Wilson 95%区間 |
|---|---:|---:|---:|---:|
| 21–29 | 396 | 84 | 21.2% | 17.5–25.5% |
| 30–39 | 165 | 76 | 46.1% | 38.6–53.7% |
| 40–49 | 118 | 65 | 55.1% | 46.1–63.8% |
| 50–59 | 57 | 34 | 59.6% | 46.7–71.4% |
| 60歳以上 | 32 | 9 | 28.1% | 15.6–45.4% |

60歳以上は32件と少なく、下降の機序は識別できません。全範囲768件／60歳以下741件と、スプライン自由度3・4・5の6仕様では、GlucoseのORは3.235987–3.339084、BMIは1.804528–1.860097、家族歴指標は1.342535–1.367428で、この比較ではすべて `stable=True` でした。妊娠回数は1.184657–1.240881で、各区間が1を含み、係数の最大相対変動0.245848から `stable=False` です。「60歳以上」の集計と「60歳以下」の感度分析は60歳を両方に含むため、互いに補集合ではありません。

![年齢帯別のOutcome割合と標本数](figures/exp-09-age-band-outcome-proportions.png)

*年齢帯別の観測割合とWilson 95%区間。高齢帯の少数標本と広い不確実性を示し、年齢曲線の高齢端を過大解釈しないための図です。*

**反復停止と追加確認ログ**: Notebookでは3回の上限に達したことに加え、主要な関連の方向とモデル依存の結論を分けられたため停止しています。診断定義・欠損機序・外的妥当性・未測定交絡は、同じCSVのモデル探索を増やしても解決できないと判断しました。今回の `followup.log` には既存セルの確認方針と、Notebookが安定し監査に合格したためランナーが停止した記録だけがあり、新しい追加依頼や追加分析結果は確認できません。既存3回の履歴とは区別し、4回目の依頼が行われたとは報告しません。

**最終結論**: この標本ではGlucoseが最も明瞭な正の関連を示し、BMIと家族歴指標にも調整・年齢形状の検討後に正の関連が残りました。ただし、BMIと家族歴指標の関連の大きさは欠損処理に依存します。妊娠回数の独立した関連の断定は年齢の非線形性を考慮すると維持できず、年齢の単変量関連も単調な独立効果とは解釈できません。Insulin・皮下厚・血圧は調整後の区間が1を含むため、「関連がない」とも「独立した危険因子」とも断定しません。**観察的・条件付き関連を示した分析であり、原因、将来発症、介入効果を示すものではありません。**

**監査・再現性**: Notebookの「再実行・引渡し監査記録」とmetadataには、新しいカーネルで全11コードセルを上からJupyter MCPで再実行し、取得SHA-256と主要数値が一致したことが記録されています。`final-summary` の出力では件数・陽性件数、Glucose/BMIの相関・係数、年齢スプラインの対数尤度などを照合し、一致を確認しています。群別ブートストラップのseedは `20261002` です。

最終セル実行中の自己監査は、監査セルがまだ終了していない旨の警告を1件出していますが、最終の保存済みNotebook監査は11コードセル中11実行済み、未実行・エラー・構造的指摘・`visual_findings` がすべて空です。7図、根拠manifest付きInsight 7件があり、`audit_ok=True` です。`v020-exp-09` は `completed`、実行中セル・保留書込み・ロックはすべて0、引渡し検証日時は `2026-10-01T20:17:15.689748+00:00` でした。

`status.json` の `analysis_complete=true` と `final_completion.ready=true` もNotebook内容と整合します。初回CLIは終了コード0・443.7秒で通常終了、追加確認は終了コード0・95.6秒ですが、終了理由は `artifact_complete_cutoff` であり、自然終了したとは扱いません。分析完了の判断はこれらの分析記録によるもので、文書化前の状態を表す `documentation_complete`・最上位の `semantic_complete`・`report_exit_code` は用いていません。ここでの再現性は保存済み実行出力・照合・監査記録の確認であり、本節の作成時に分析を新たに再実行したものではありません。

**失敗内容とJupytermind改善候補**: データ取得では指定uciml版の403と別候補の対象ファイル不在がありましたが、検索で得た別のKaggle公開版から取得して分析を完了しています。最終Notebookに実行エラーや未完了の分析セルはありません。

Notebookの「Jupytermind改善候補」には、過去の初回分析から保持された2候補があります。1つは `visualization.render_chart` の長いx目盛りと日本語軸ラベルが下端で切れた描画品質の不具合疑い、もう1つは、その画像に対する `notebook_audit.audit_notebook(visual_audit=True)` が `ok=True`・`visual_findings` 空となった可読性検出範囲の拡張候補です。横棒化と `bbox_inches='tight'` で回避し、今回の7図は修正後の出力です。**原問題の画像や別ファイルの初回監査ログは今回の指定証拠には含まれないため、現在も再現する不具合とは断定せず、Notebookに記録された過去の候補として保存します。** 最終自動監査の合格も、あらゆるラベル切れを検出できるという保証ではありません。

Kaggleの403・ファイル不在は取得サービス／データセット側、CLIからPythonのMCPClientを注入できない点はCLI接続上の制約、Filesystem MCPの許可ディレクトリやJupyter Contents APIの絶対パス制約は周辺ツール設定・API側の問題として区別します。検索先頭ページだけで不在と判断した点は分析担当側の探索不足です。Notebookには「ベンチマークランナーは未起動」という記述もありますが、提供された両ログには `[runner]` の停止記録があるため、その記述からランナー全体の不使用を結論づけません。停止と追加確認の打切りは外部実行制御の記録で、Jupytermind本体の障害とは扱いません。

**残る限界**: ゼロを欠損とみなす判断、欠損機序、独立性、Outcomeの診断定義と測定時間順序は未検証です。Glucoseとの強い関連にはラベル定義との近接性があり得ます。単一補完の通常CIは補完値の不確実性を含まず、完全例解析は標本選択を変えます。探索的なモデル比較と点ごとの曲線CI、高齢端の少数標本、測定誤差、未測定交絡、母集団・単位の推定、指定uciml版との未照合も残ります。独立参照データがないためデータセット間照合による検証は行わず、歪んだ分布に対する一律のz-score除外も適用しません。予測性能評価・機械学習モデル選択は目的外で、ROC-AUCや将来発症予測の成功をこの実験の成果には含めません。

**証拠と保存先**: 本節の分析上の証拠は、`benchmark/projects/kaggle-v020-kaggle-exp-09-diabetes/notebooks/kaggle-v020-kaggle-exp-09-diabetes.ipynb` と、`benchmark/runs/09-kaggle-exp-09-diabetes/` の `initial-prompt.md`・`initial.log`・`followup.log`・`status.json` に限ります。既存の白書は書式の参考のみで、旧版の数値や成功状態は転用していません。図は指定NotebookのPNG出力を変換せず抽出しました。改善候補の証拠範囲と受け入れ条件は同ディレクトリの `issue-candidate.json` に保存しています。
