## 実験10: Students Performance in Exams（Notebook分析・再実行済み／外部追加確認未完了）

**課題**: 「KaggleのStudents Performanceデータで、試験成績の差に結びつく要因を調べてください。」

**初回プロンプト（全文・原文）**:

> KaggleのStudents Performanceデータで、試験成績の差に結びつく要因を調べてください。分析計画、比較方法、図表は自分で決め、交絡や自己選択の可能性を含む限界を日本語で説明してください。AI Data Scientist SkillとJupyter MCPを使い、コード・結果・根拠付きInsightをノートブックに記録し、再実行可能か検証してください。 Kaggle参照先: https://www.kaggle.com/datasets/spscientist/students-performance-in-exams。インストール済みkaggle Python SDKを使い、NotebookのJupyter MCP実行セル内で`KaggleApi().authenticate()`、`dataset_list(search=...)`、`dataset_list_files(...)`、必要に応じて`dataset_download_file(...)`を呼び出し、Kaggle上の対応する公開データを検索・取得してください。owner/dataset slug、取得ファイル名、取得日、ファイルSHA-256をNotebookに記録してください。APIトークンをセル出力・Notebook・ログへ表示しないでください。分析・API取得コードの実行はJupyter MCPだけを使い、端末コマンド、subprocess、外部スクリプト起動、作業エージェントへの委譲は行わないでください。Kaggle APIで対応データを検索・取得できなかった場合に限り、`/home/nahisaho/kaggle/experiments/white-paper.md`に記載された旧実験の公開CSV `https://raw.githubusercontent.com/rashida048/Datasets/master/StudentsPerformance.csv` を取得して実験を継続してください。その場合はKaggle APIの失敗内容、フォールバックした理由、CSV URL、取得日時、SHA-256をNotebookに記録し、公開CSVとKaggle掲載版の完全な同一性は保証されないことを明記してください。保存先は benchmark/projects/kaggle-v020-kaggle-exp-10-students/notebooks/kaggle-v020-kaggle-exp-10-students.ipynb としてください。run_idは `v020-exp-10` です。長時間処理の開始前にlifecycle.register_runを呼び、実行・書込みフェーズを記録し、終了時にcompletedまたはfailedを記録してください。データ定義manifest、分析前提manifest、意味的な異常検査、妥当な範囲の感度分析を使い、適用できない機能は理由を記録してください。図表はvisual_audit=Trueで監査してください。Notebookには「使用したJupytermindモジュール」節を設け、直接import・呼び出したモジュール名、関数名、使用目的を記録してください。間接利用は使用済みに含めないでください。Jupytermindの不具合または機能不足が疑われた場合は「Jupytermind改善候補」節を設け、分類、再現条件、期待する挙動、実際の挙動、影響、回避策、関係するセルとログを記録してください。Copilot CLI、Kaggle API、ベンチマークランナーに固有の問題とは切り分け、候補がなければ「なし」と記録してください。初回分析後、自分で結果を読み直し、結論に実質的な影響を与える未解決点があれば自然言語の追加依頼文を作成し、Notebookの「反復依頼履歴」に原文のまま記録して実行してください。価値ある追加分析がなくなるまで最大3回繰り返し、各反復の選定理由・結果・証拠・残る限界を報告してください。最後に全コードセルを上から再実行し、notebook_auditとライフサイクル状態を記録してください。

**使用したJupytermindモジュール**: Notebookのコードセルで直接import・呼び出しを確認できた `ai_data_scientist` のサブモジュールを示します。クラス・メソッドはその旨を併記し、間接利用や別Notebookだけの呼び出しは含めません。

| モジュール | 関数・クラス・メソッド | 使用目的 |
|---|---|---|
| `project_manager` | `resolve_project`, `ensure_data_dir`, `ProjectHandle`（クラス）, `ensure_notebook`, `enqueue_write` | 保存先の解決、データディレクトリと証拠検証Notebookの作成、証拠セル・Insight・metadataの直列書込み |
| `language_router` | `detect_language` | 日本語の指示であることの判定 |
| `lifecycle` | `register_run`, `is_cancel_requested`, `mark_execution_start`, `mark_execution_end`, `mark_write_start`, `mark_write_end`, `mark_completed`, `wait_for_quiescence`, `get_run_status` | run登録、取消確認、実行・書込みフェーズと完了・静止状態の記録 |
| `ingestion` | `SourceSpec`（クラス）, `ingest` | 取得CSVの読込み、行数上限と切詰め有無の確認 |
| `cleaning` | `clean_dataset` | `drop_na`による欠損除去の影響確認。欠損がないため行数は不変 |
| `eda` | `explore` | 型、欠損、カテゴリ件数、数値要約の確認 |
| `stats_analysis` | `correlation` | 読解と作文のPearson相関の計算 |
| `visualization` | `render_chart`, `build_image_output` | 準備講座区分別の棒グラフ生成、3図のPNGを画像MIME出力として表示 |
| `data_definition` | `FieldValue`（クラス）, `build_manifest`, `unresolved_fields`（manifestメソッド） | 出典・変数定義・変換と、確認済み／推測／不明の区別 |
| `analysis_assumptions` | `Assumption`, `AnalysisAssumptionManifest`（クラス）, `check_manifest` | 独立性、合成指標、一般化・因果解釈に関する分析前提と警告の記録 |
| `data_quality` | `detect_anomalies` | 得点範囲、許容カテゴリ、非欠損条件の意味的検査 |
| `sensitivity` | `SensitivityPlan`（クラス）, `run_sensitivity` | 準備講座・昼食区分について各8仕様の推定値と安定性を比較 |
| `insight_engine` | `extract_cited_value`, `record_insight` | 実出力から引用値を抽出し、根拠manifest付きInsightを登録 |
| `notebook_audit` | `audit_notebook` | コード実行状態、根拠リンク、`visual_audit=True`の図表監査 |

Welch比較、OLS・HC3、中央値回帰、Holm補正、部分R²の交絡シナリオはSciPy・statsmodels等とNotebook内の分析コードによる処理です。科目別・層別の区間図はMatplotlibで描画しており、すべてをJupytermindの統計・描画機能が実施したとは扱いません。`mcp_gateway.run_and_record` はPython MCPClientオブジェクトがないため未使用と記録されています。独立した参照データがないため、`data_quality.validate_anomalies` と `dataset_validation.compare_datasets` も適用していません。

**初回指示**: 手法を指定せず、成績差に結びつく要因の比較、交絡・自己選択を含む限界、日本語での根拠付き説明を求めました。Kaggle APIによる取得を優先し、失敗時に限る公開CSVへのフォールバック、来歴・SHA-256、manifest、意味検査、感度分析、図表監査、最大3回の自律的追加依頼、全セル再実行、ライフサイクル記録を要求しています。

AIの計画は、数学・読解・作文の等重み平均を主指標、科目別得点を補助指標とするものでした。初回は5属性の件数・平均・標準偏差を確認し、準備講座、昼食、genderの3比較にWelch平均差・95%区間・標準化差・Holm補正を適用しました。続いて準備講座、昼食、gender、保護者学歴、ethnicityの5要因をカテゴリとして同時投入し、OLSと異分散に対応するHC3標準誤差で調整しました。保護者学歴を一律の線形順序尺度とはしていません。

**データ取得**: Notebookの取得セルには、Kaggle SDKの認証、検索、ファイル一覧取得、必要時のダウンロードが実装され、実出力には指定slugの検索結果と `StudentsPerformance.csv` の一覧・来歴が残っています。

| 項目 | Notebookに記録された内容 |
|---|---|
| 取得元 | Kaggle API、`spscientist/students-performance-in-exams` |
| ファイル | `StudentsPerformance.csv` |
| 取得日時 | `2026-10-01T18:40:25.330816+00:00`（UTC） |
| SHA-256 | `ade5869dba8b2d3e2b96379359fb2f61cb0308e8394d9b1ba37e174cfe3bee69` |
| データ規模 | 1,000行・8列。行上限10,000に対する切詰めなし |
| 品質検査 | 欠損セル0、完全一致重複行0、数値変換失敗0、設定したスキーマでの意味的異常0 |
| フォールバック | 使用なし。Kaggle API失敗は記録されていない |

数学の0点は1件ですが、設定した0〜100の範囲内として保持しています。範囲内であることは測定の正確さの保証ではありません。認証情報は非表示とされ、指定証拠ファイルにトークンそのものは記録されていません。再実行ではCSVのハッシュが既存来歴と一致した場合にキャッシュを使う構造であり、各再実行でファイルを新規ダウンロードしたことまでは意味しません。

**初回結果**: 準備講座完了者は358人、未完了者は642人で、3科目平均はそれぞれ72.669、65.039でした。昼食standardは645人、free/reducedは355人で、平均は70.837、62.199でした。femaleは518人、maleは482人で、平均は69.569、65.837でした。

| 比較（3科目平均） | 未調整差 | 未調整95%区間 | 5要因調整差 | 調整95% HC3区間 |
|---|---:|---:|---:|---:|
| 準備講座 completed − none | +7.631 | 5.888〜9.373 | +7.639 | 6.027〜9.250 |
| 昼食 standard − free/reduced | +8.638 | 6.819〜10.457 | +8.775 | 7.099〜10.452 |
| gender female − male | +3.732 | 1.980〜5.485 | +3.724 | 2.167〜5.281 |

未調整の標準化差は順に0.553、0.633、0.264で、3比較のHolm補正後p値は `8.85×10⁻¹⁷`、`4.75×10⁻¹⁹`、`3.19×10⁻⁵` でした。調整モデルでは切片以外の12係数を別にHolm補正しています。保護者学歴master's degree − high schoolの調整差は+9.265（95%区間5.683〜12.846）でしたが、master's degreeは59人であり、学歴介入の効果ではありません。ethnicityはgroup Cを基準にgroup Dで+2.740、group Eで+4.543の関連があり、Holm補正後p値は0.0283、0.00341でした。group A、group Bの区間は0を含みます。匿名化されたカテゴリの定義は不明で、集団の本質的な能力差という説明はできません。

モデルのR²は0.242263で、収録5要因だけでは得点変動の多くを説明できません。読解と作文の相関は0.954598と強く、3科目平均は独立した3測定の平均ではなく、言語科目を二重に重み付けする面があります。相関出力の `p=0` は極小値の数値表現であり、確率が厳密に0であるという意味ではありません。初回ログも、調整後に関連は残るが因果効果ではないと述べ、平均が科目別差を隠さないかを次の確認点にしています。

![準備講座区分別の未調整3科目平均](figures/exp-10-students-preparation-unadjusted-mean.png)

*準備講座完了者と未完了者の3科目平均。NotebookのPNG出力から抽出した未調整比較であり、受講の因果効果や不確実性を表す図ではありません。*

**AIが生成した追加依頼1 — 科目別の方向と多重比較**

> 3科目平均の差だけでは科目ごとの方向が隠れる可能性があります。数学・読解・作文それぞれについて準備講座、昼食区分、genderの調整差と95%信頼区間を算出し、多重比較を補正して、平均指標による結論を修正すべきか確認してください。

**選定理由**: 初回のgender平均差は科目の構成による可能性があり、結論の方向に直結するとAIが判断しました。原文と理由はNotebookの「反復依頼履歴：第1回」に記録されています。

**結果**: 各科目と平均に同じ5要因モデルを適用し、3要因×4指標の12係数でHolm補正しました。

| 科目 | 準備講座 completed − none | 昼食 standard − free/reduced | gender female − male |
|---|---:|---:|---:|
| 数学 | +5.495（3.786〜7.204） | +10.877（9.114〜12.640） | −4.995（−6.637〜−3.354） |
| 読解 | +7.362（5.687〜9.037） | +7.246（5.510〜8.982） | +7.071（5.458〜8.684） |
| 作文 | +10.059（8.461〜11.656） | +8.203（6.534〜9.871） | +9.096（7.540〜10.653） |

括弧は各係数の95% HC3区間で、同時信頼区間ではありません。準備講座・昼食は全科目で正の関連ですが、genderは数学で負、読解・作文で正となりました。各科目の3比較はHolm補正後もp<0.05です。AIは平均のみのgender解釈を採用しないと結論を修正しました。ただし、科目間の測定尺度や未観測の事前学力は不明であり、この12係数内の補正は探索的な分析選択全体を保証するものではありません。

![科目別の準備講座・昼食・genderの調整差と区間](figures/exp-10-students-subject-adjusted-differences.png)

*同じ5要因を調整した科目別差と3科目平均の95% HC3区間。genderの方向が数学と読解・作文で逆転し、平均だけでは差の構造を捉えられないことを示します。*

**AIが生成した追加依頼2 — 自己選択と層別の異質性**

> 準備講座の完了者は自己選択された集団です。受講割合を観測属性別に比較し、昼食区分×genderの4層で調整済み成績差と人数を確認してください。準備講座との交互作用も検定し、全員に同じ差があるという結論が妥当か評価してください。

**選定理由**: 科目別でも準備講座の差は正でしたが、自己選択や属性による差の異質性が未解決だったためです。Notebookの「反復依頼履歴：第2回」に原文と理由があります。

**結果**: 準備講座の完了割合は昼食free/reducedで36.9%、standardで35.2%、femaleで35.5%、maleで36.1%でした。一方、保護者学歴のhigh schoolでは28.6%、some high schoolでは43.0%で、観測属性による構成差もあります。これらは完了状況の割合であり、受講開始からの完了率ではありません。4層内では保護者学歴とethnicityを調整しました。

| 昼食区分／gender | 完了者／未完了者 | 準備講座の調整差 | 95% HC3区間 |
|---|---:|---:|---:|
| free/reduced／female | 70／119 | +9.875 | 5.659〜14.092 |
| free/reduced／male | 61／105 | +5.610 | 1.243〜9.976 |
| standard／female | 114／215 | +6.342 | 3.679〜9.006 |
| standard／male | 113／203 | +8.527 | 5.551〜11.503 |

全層で正の差が残り、4比較のHolm補正後もp<0.05でした。全体モデルの準備講座×昼食の交互作用は−0.873（p=0.615）、準備講座×genderは+0.106（p=0.948）で、2検定のHolm補正後p値はともに1.000でした。差の異質性を支持する証拠は弱いものの、全員に同じ差があることの証明ではありません。層別は観測した2属性に限られ、事前学力や意欲による自己選択、少数層、探索的検定という限界が残りました。

![昼食区分とgenderで層別した準備講座の調整差](figures/exp-10-students-preparation-lunch-gender-strata.png)

*昼食区分×genderの4層における準備講座完了者−未完了者の3科目平均差と95% HC3区間。ラベルの人数は完了者数＋未完了者数で、層内では保護者学歴とethnicityを調整しています。*

**AIが生成した追加依頼3 — 仕様依存と未測定交絡への感度**

> 層別でも準備講座の正の関連が残りましたが、モデル仕様や影響の強い行に依存していないか、OLSと中央値回帰、全行とCook距離による感度用除外、ethnicity調整の有無を比較してください。さらに未測定交絡が主な差を打ち消す強さを線形回帰の部分R2シナリオで示し、頑健性を因果効果の証明と誤解しないよう結論を整理してください。

**選定理由**: 観測層別だけでは残る自己選択を評価できず、仕様依存と未測定交絡への感度が結論の強さを左右するためです。Notebookの「反復依頼履歴：第3回」に原文と理由があります。

**結果**: OLS／中央値回帰、全行／Cook距離が `4/n` を超える45行を感度用に除外した標本、ethnicity調整あり／なしの組合せで各8仕様を比較しました。主分析は全1,000行を保持しています。準備講座の係数は6.259〜7.708、昼食の係数は7.333〜9.000で、いずれも全仕様で正でした。基準仕様からの最大相対偏差は準備講座18.06%、昼食16.43%で、明示した20%目安に対し両方の `report.stable=True` が記録されています。20%は科学的に事前設定された許容幅ではなく実務上の目安であり、平均と中央値は異なる推定対象です。

未測定交絡は、通常OLSの標準誤差と残差自由度987を用いた部分R²のシナリオで検討しています。交絡変数と準備講座、および交絡変数と得点との条件付き部分R²を同じ強さと置く場合、点推定を0にする閾値は準備講座0.253103、昼食0.285361でした。両部分R²を0.30とするシナリオでは点推定がそれぞれ−1.714、−0.546となりました。これは仮想的な最悪方向のバイアス計算で、実際の交絡がその強さで存在することも、HC3による有意性が消える閾値も示していません。

AIは仕様上の正の関連を確認しつつ、頑健性を因果効果の証明とはしませんでした。最大3回で停止し、学校内依存、抽出機構、事前学力は同じCSVでの追加計算では解消できず、独立データと追加情報が必要と記録しています。これら3回の追加依頼は初回実行内に残っている反復であり、後述の外部追加確認ログとは別です。

**最終結論**: この1,000行の標本では、準備講座完了、昼食standard、一部の保護者学歴・ethnicityカテゴリに、観測5要因を調整しても成績差との関連が残りました。準備講座と昼食の正の関連は科目別・仕様比較でも維持されましたが、自己選択や未測定交絡を取り除いたわけではありません。genderの差は科目で方向が異なり、3科目平均だけによる一律の説明は不適切です。受講・給食・学歴の介入効果や、母集団の代表値は主張できません。

完了状態は二層に分けます。Notebook内容、保存後監査、ライフサイクルは分析・再実行済みを支持し、`status.json` の `final_completion.ready=true` と8要件すべてtrueもそれに整合します。一方、同ファイルの **`analysis_complete=false`** は残り、外部追加確認も失敗しています。したがって、Notebook成果が揃っていることは確認できますが、ベンチマーク全体の完了フラグまで成功と読み替えることはできません。状態の不一致を解消したとは扱わず、無条件の「実験全体完了」とは判定しません。

**監査・再現性**: Notebookは `benchmark/projects/kaggle-v020-kaggle-exp-10-students/notebooks/kaggle-v020-kaggle-exp-10-students.ipynb`、run_idは `v020-exp-10` です。最終ファイルには10コードセル、3枚の埋込みPNG、根拠付きInsight8件、3回の反復履歴があります。保存されたexecution_countは1〜10で、Notebook metadataの再現性記録は、新しいカーネルでの順次再実行、初回45推定値との最大絶対差0.0、許容誤差 `rtol=atol=1e-8`、CSVのSHA-256一致を示します。コードソースのSHA-256もmetadataに記録されています。

最終セルの実行中出力は監査対象に自身を含むため実行済み9/10と一時的な監査例外を示し、IPython内部カウンタ11により `clean_kernel_top_to_bottom=false` と表示しています。Notebookの説明では、保存後の実execution_countによる確認を最終判定としており、metadataには `clean_kernel_top_to_bottom=true`、`post_execution_audit_ok=true` が残っています。保存後の監査metadataと `status.json` の `final_audit` は、nbformat妥当、実行済み10/10、未実行・エラー・findings・visual_findingsがいずれも0、Insight8件を示します。画像は1つのコードセルに3枚あり、chart_cellsが1件であることと矛盾しません。

`lifecycle_final` はcompletedで、実行数・書込み数・ロック数はすべて0でした。実行環境の出力はPython 3.12.3、pandas 3.0.6、NumPy 2.5.3、SciPy 1.18.1、statsmodels 0.15.0、Matplotlib 3.11.2、Kaggle SDK 2.2.4、nbformat 5.11.1、japanize-matplotlib 1.1.3、seedは20261002です。再現にはこれらの依存環境、Kaggle認証、ネットワーク、保存済みCSVのハッシュ確認が必要です。本節作成時に分析コードやKaggle取得を新たに再実行したわけではなく、記述は指定Notebook・プロンプト・ログ・状態ファイルの証拠に限定しています。Notebookが参照する別の作成用Notebookやdata配下ファイルは、本節の独立した証拠としては読んでいません。

**失敗内容と責任層の切り分け**: 初回プロセスは `initial_exit_code=0`、1,503.4秒、終了理由exitedで、ログ末尾に分析・再実行・最終監査の報告があります。ただし、途中に回復した失敗もNotebookに残っています。表示名修正によるSyntaxErrorとcontextlibのimport漏れは分析者コード、初期ディレクトリ未作成はJupyter MCPの利用手順、filesystem MCPの許可ルート不一致は設定の問題として記録されています。実行中セルの移動に伴う出力位置の不整合も、MCPと書込み手順の相互作用として分離されています。修正・回避後の最終Notebookにエラー出力はありませんが、これを「途中の失敗なし」とは表現しません。

外部追加確認は **`followup_exit_code=1`、39.6秒** で終了しています。`followup.log` の実エラーは `Failed to load models`、`Model catalog request timed out after 30000ms` であり、Copilot CLIがモデル一覧を取得できなかったことを示します。追加確認の分析結果はこのログにありません。認証不備や通信障害のどちらが根本原因かは特定できず、JupytermindやKaggle APIの失敗とは分類しません。初回・追加確認ログ末尾の `[runner] stopping process group` はCLI終了後の子プロセス清掃という記録で、分析タイムアウトの証拠ではありません。Notebook中の「ベンチマークランナー未使用」という記述はセル内処理の自己報告であり、外部ログに残るランナーの存在を否定する根拠にはしません。

**Jupytermind改善候補**: 4候補を `issue-candidate.json` のJSONオブジェクトに保存しました。再現手順、期待・実際の挙動、影響、証拠、回避策、受け入れ条件を含みます。候補は修正済みの不具合という意味ではありません。

| 分類 | 観測・報告された挙動 | 回避策と証拠の強さ |
|---|---|---|
| 根拠出力形式の機能不足 | 実行済み `print` のstream.textにある値を `record_insight` に渡すと `EvidenceMissingError` | `display` のtext/plain証拠台帳を引用。最終セルの実出力に `STREAM_EVIDENCE_REPRO=EvidenceMissingError` があり、再現コードも保存されている |
| 日本語フォントの状態依存 | `rc_context` 内の初回描画後、フォント設定が戻っても初回設定済み状態が残り、次の日本語描画で欠落グリフ警告が出ると記録 | 全描画に `font.family=IPAexGothic` を明示。Notebookの記録と初回ログは整合するが、修正前警告の原ログは指定証拠に含まれず、内部原因の独立検証は未実施 |
| ラベル切れ・図表監査の限界の疑い | 元の棒グラフで長い回転カテゴリと横軸ラベルが切れ、視覚監査では検出されなかったと記録 | 短い表記とautolayout、カスタム図のtight bounding box・凡例外側配置。最終PNGは確認できるが、別ファイルの修正前PNGは今回の証拠範囲外 |
| MCP連携の書込み同期候補（責任層未確定） | Insight重複、MCP完了保存による根拠execution_countの9→16への巻戻りが記録されている | 非アクティブ証拠Notebook、固定8スロットへの一括反映、保存後の再同期・監査。Jupytermind単体の責任は未確定で、MCP連携として切り分けた調査候補 |

最後の同期事象はmetadataの `actual_ledger_count=9`、`stale_count_detected=16`、`restored_insight_count=8` と、Notebook説明・初回ログの再同期報告に基づきます。`stale_count_detected` の16を不整合16件と数えず、説明にある旧execution_count=16として扱います。これらの改善候補と、Copilot CLIのモデル一覧タイムアウト、Kaggle API、外部ランナー、分析者コードの問題は分けています。

**残る限界**: 母集団、抽出方法、国・年度・学校、独立した生徒かどうか、各変数の操作的定義・測定手順は未確認です。得点は観測上0〜100ですが、100点満点という制度も検証していません。独立性・3科目平均の妥当性・一般化や因果推論に関する前提検査には3件の警告が残り、最終Notebook監査の指摘0件はそれらを解消したことを意味しません。HC3は異分散には対応しますが学校内クラスタ依存には対応せず、信頼区間は行の独立という作業仮定に依存します。事前学力、学習意欲・時間、家庭支援、所得、学校・教師、受講時期などがなく、層別・仕様比較でも未測定交絡は除けません。図表監査と数値再現性の成立は、測定の妥当性、標本の代表性、因果解釈を保証しません。
