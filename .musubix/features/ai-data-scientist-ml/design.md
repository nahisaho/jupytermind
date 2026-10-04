---
schemaVersion: 1
feature: ai-data-scientist-ml
---
# Design / 設計 (ML Extension)

Architecture blueprint for the `ai-data-scientist-ml` feature: advanced
modeling, analytics, NLP, dashboards, and report export built on top of the
MVP's Project & Notebook Manager (DES-AIDS-003), Jupyter MCP Execution
Gateway (DES-AIDS-004), and Visualization module (DES-AIDS-009). Every
component below produces its interpretive claims subject to the MVP's
Insight & Evidence Engine (DES-AIDS-010) rules (REQ-AIDS-009/010) and
executes exclusively through DES-AIDS-004 unless explicitly noted (see
DES-AIDS-024).

## DES-AIDS-012: Supervised ML modeling module / 教師あり学習モデリング
Responsibilities: Split a dataframe into train/test partitions, train the
requested classification or regression model, and report the appropriate
evaluation metrics for that model type.
Interfaces: trainModel(df, target, modelType, testSize) -> ModelResult
{model, metrics, trainIndex, testIndex}, executed via
DES-AIDS-004.executeCell.
Constraints: Train/test row indices must be non-overlapping and must be
reported alongside metrics so overlap can be asserted against in tests.
Requirements: REQ-AIDS-008
ADRs: none — model-type selection follows directly from the user's request with no competing architectural option considered.
Depends-On: DES-AIDS-004

## DES-AIDS-013: Feature engineering module / 特徴量エンジニアリング
Responsibilities: Apply the requested encoding, scaling, row-wise
aggregation, categorical interaction, missing-value flagging, or
explicit-edge binning transformation to a dataframe and report the
resulting feature set as a structured column-name-to-definition mapping.
(Feature-selection support named in REQ-AIDS-015's statement predates this
change, has no acceptance criterion or implemented operation, and remains
out of CHANGE-008's scope — tracked as a pre-existing gap, not introduced
or newly accepted here.)
Interfaces: `engineer_features(df: DataFrame, operation: str, columns:
list[str] | None = None, **params) -> FeatureResult` executed via
`DES-AIDS-004.executeCell`, where `FeatureResult = {dataframe,
added_columns, removed_columns, definitions: dict[str, str] =
field(default_factory=dict)}` (the new `definitions` field defaults to an
empty dict, so existing 3-positional-argument `FeatureResult(...)`
construction stays valid). `operation` accepts `one_hot`, `scale`,
`aggregate`, `interaction`, `missing_flag`, or `bin`. Operation-specific
`**params`: `aggregate` requires `group_col: str`, `agg_func: Literal["mean",
"sum", "count_eq"]`, and (only for `count_eq`) `compare_value`, with
`columns` naming the source column(s) to aggregate — one output column per
`columns` entry; `interaction` requires `col_a: str`, `col_b: str`;
`missing_flag` uses `columns` only; `bin` requires `edges: list[float]` and
`columns` naming the single column to bin. Unknown/missing required params
for the given `operation` raise `ValueError`.
Constraints: One-hot encoding output must match the pandas get_dummies
reference output exactly (REQ-AIDS-015 acceptance). Aggregation uses
`groupby(group_col)[source_col].transform(...)` semantics with nulls
excluded from `mean`/`sum` and treated as non-matching for `count_eq`
(`df[source_col].eq(compare_value).groupby(df[group_col]).transform("sum")`
is the `count_eq` reference). Interaction concatenates `astype("string")`
values with a `"__"` separator and nulls propagate. Binning requires
explicit monotonically increasing edges and matches `pandas.cut(...,
right=True, include_lowest=True)`, mapping out-of-range values to null.
Every added column has a non-empty `definitions` entry naming the operation
and source column(s). Existing `one_hot`/`scale` calls keep their current
`FeatureResult.dataframe`/`added_columns`/`removed_columns` values
unchanged.
Requirements: REQ-AIDS-015
ADRs: none — pandas/scikit-learn provide the transformation primitives directly; no rejected alternative was evaluated.
Depends-On: DES-AIDS-004

## DES-AIDS-061: Leakage-safe fit/transform feature engineering API / リーク防止fit/transform API
Responsibilities: Separate statistics estimation from transformation
application for statistics-estimating `engineer_features` operations
(currently `scale`), so a model-selection/cross-validation caller can fit
on a training fold and transform a disjoint fold without ever deriving
statistics from the held-out rows.
Interfaces: `fit_features(df: DataFrame, operation: Literal["scale"],
columns: list[str]) -> FittedFeatureState` where `FittedFeatureState =
@dataclass(frozen=True) {operation: str, columns: tuple[str, ...], scaler:
StandardScaler}` and `scaler` is exactly the object produced by
`StandardScaler().fit(df[list(columns)])` (no other state is held for the
currently-supported `scale` operation); `transform_features(fitted_state:
FittedFeatureState, df: DataFrame) -> FeatureResult`, selecting
`df[list(fitted_state.columns)]` in `fitted_state.columns` order and
calling `fitted_state.scaler.transform(...)` on it — never re-fitting —
then returning a `FeatureResult` whose `dataframe` preserves `df`'s
index/row order with the transformed columns replaced in place.
Constraints: `fit_features(df, "scale", columns).scaler.mean_`/`.scale_`
must be bit-for-bit equal to a `StandardScaler` fitted only on
`df[columns]`. `transform_features` must never read or recompute
statistics from its `df` argument; it only applies
`fitted_state.scaler.transform`. `transform_features(fitted_state, df)`
called with the same `df` the `fitted_state` was fit from must reproduce
the legacy single-call `engineer_features(df, "scale", columns)` output
exactly, so the existing entry point can be re-implemented in terms of this
pair without behavior drift. A fit column with zero training-fold variance
keeps scikit-learn's `StandardScaler` convention of `scale_=1` for that
column (confirmed: `StandardScaler().fit([[1.0],[1.0],[1.0]]).scale_ ==
[1.0]`), so its transform output reduces to mean-centering without a
division-by-zero error; this requires no special-case code beyond
delegating to `StandardScaler`.
Requirements: REQ-AIDS-073
ADRs: none — this narrowly splits an existing scikit-learn-backed
transformation into two calls using the same `StandardScaler` primitive;
no competing architectural alternative was considered.
Depends-On: DES-AIDS-013

## DES-AIDS-014: Clustering & dimensionality reduction module / クラスタリング・次元削減
Responsibilities: Fit the requested unsupervised model (clustering or
dimensionality reduction) and report cluster assignments or reduced
component values.
Interfaces: clusterOrReduce(df, method, params) -> UnsupervisedResult
{labels_or_components, method, params}.
Constraints: Cluster label value counts must sum to the original row count
(REQ-AIDS-016 acceptance).
Requirements: REQ-AIDS-016
ADRs: none — scikit-learn's clustering/decomposition estimators are used directly with no rejected alternative.
Depends-On: DES-AIDS-004

## DES-AIDS-015: Anomaly detection module / 異常検知
Responsibilities: Flag anomalous records in a dataframe using the
requested detection method and report the count of flagged records.
Interfaces: detectAnomalies(df, method, params) -> AnomalyResult
{flagged_indices, method}.
Constraints: Must flag at least the known injected-outlier indices in the
acceptance test dataset (REQ-AIDS-017).
Requirements: REQ-AIDS-017
ADRs: none — the detection method is user-selected per request with no competing architectural option considered.
Depends-On: DES-AIDS-004

## DES-AIDS-016: Time series analysis & forecasting module / 時系列分析・予測
Responsibilities: Decompose or forecast a requested time series and report
trend, seasonality, or forecast values.
Interfaces: analyzeTimeSeries(series, operation, params) -> TimeSeriesResult
{trend, seasonality, forecast}.
Constraints: Forecast values must stay within a documented error tolerance
of a reference statsmodels forecast computed on the same input
(REQ-AIDS-018 acceptance).
Requirements: REQ-AIDS-018
ADRs: none — statsmodels' decomposition/forecast primitives are used directly with no rejected alternative.
Depends-On: DES-AIDS-004

## DES-AIDS-017: Hyperparameter tuning & model comparison module / ハイパーパラメータ調整・モデル比較
Responsibilities: Evaluate multiple parameter sets or model candidates
against DES-AIDS-012's training interface and report the best-performing
configuration with its metric.
Interfaces: tuneOrCompare(df, target, grid) -> TuningResult
{best_params, best_metric, all_candidates}.
Constraints: The reported best metric must be the maximum or minimum among
all evaluated candidates shown in the output (REQ-AIDS-019 acceptance).
Requirements: REQ-AIDS-019
ADRs: none — grid evaluation is a direct consequence of REQ-AIDS-019 with no competing architectural option considered.
Depends-On: DES-AIDS-012

## DES-AIDS-018: AutoML module / AutoMLモジュール
Responsibilities: Train multiple candidate model types via DES-AIDS-012/017
and report a ranked comparison of their evaluation metrics.
Interfaces: runAutoML(df, target) -> AutoMLResult {ranked_candidates}.
Constraints: Must produce at least three candidate models with a
consistent evaluation metric column, sorted in the correct order
(REQ-AIDS-020 acceptance).
Requirements: REQ-AIDS-020
ADRs: none — AutoML composes DES-AIDS-012/017 directly with no rejected alternative.
Depends-On: DES-AIDS-012, DES-AIDS-017

## DES-AIDS-019: Model explainability module / モデル説明性
Responsibilities: Compute feature importance or SHAP values for a model
trained via DES-AIDS-012 and report them alongside a markdown
interpretation subject to DES-AIDS-010's evidence rules.
Interfaces: explainModel(model, df) -> ExplainabilityResult
{feature_importances, ranking}.
Constraints: The top-ranked feature must match the reference scikit-learn
feature_importances_ or SHAP ordering (REQ-AIDS-021 acceptance).
Requirements: REQ-AIDS-021
ADRs: none — feature-importance/SHAP computation is a direct library call with no rejected alternative.
Depends-On: DES-AIDS-012

## DES-AIDS-020: A/B testing & experiment evaluation module / A/Bテスト・実験評価
Responsibilities: Compute the statistical significance of the observed
difference between two groups and report the result with a markdown
interpretation.
Interfaces: evaluateExperiment(control, treatment, test) -> ExperimentResult
{statistic, p_value, interpretation}.
Constraints: The reported p-value must match a reference two-sample test
within 1e-6 (REQ-AIDS-022 acceptance).
Requirements: REQ-AIDS-022
ADRs: none — scipy's two-sample test primitives are used directly with no rejected alternative.
Depends-On: DES-AIDS-004

## DES-AIDS-021: Japanese NLP module via GiNZA / GiNZAによる日本語NLPモジュール
Responsibilities: Run the pinned GiNZA (`ja_ginza`) pipeline on Japanese
text to perform the requested tokenization/POS/analysis operation and
report the result.
Interfaces: analyzeJapaneseText(text, operation) -> JapaneseNLPResult
{tokens, pos_tags}.
Constraints: Output must match the pinned ja_ginza model's tokenization and
POS tags for the fixed reference sentence used in acceptance testing
(REQ-AIDS-023).
Requirements: REQ-AIDS-023
ADRs: ADR-0006
Depends-On: DES-AIDS-004

## DES-AIDS-022: Non-Japanese NLP module / 日本語以外のNLPモジュール
Responsibilities: Run a configured non-Japanese NLP pipeline on text to
perform the requested operation (e.g. sentiment analysis) and report the
result.
Interfaces: analyzeText(text, operation, language) -> NLPResult
{scores, labels}.
Constraints: Sentiment polarity direction must match the expected label for
at least 80 percent of the acceptance sample (REQ-AIDS-026).
Requirements: REQ-AIDS-026
ADRs: none — this path is intentionally independent of the Japanese-specific GiNZA decision so Japanese and non-Japanese pipelines can evolve separately.
Depends-On: DES-AIDS-004

## DES-AIDS-023: Interactive dashboard module / 簡易ダッシュボードモジュール
Responsibilities: Render an interactive widget or chart embedded in the
notebook output, extending DES-AIDS-009's static chart rendering with an
interactive HTML/widget MIME bundle.
Interfaces: renderDashboard(df, spec) -> InteractiveOutput (HTML/widget
MIME bundle), written via DES-AIDS-003.enqueueWrite.
Constraints: Output must be an interactive HTML or widget MIME bundle
persisted in the saved ipynb JSON (REQ-AIDS-024 acceptance).
Requirements: REQ-AIDS-024
ADRs: none — this composes the MVP visualization/notebook-write path with no rejected architectural alternative.
Depends-On: DES-AIDS-009

## DES-AIDS-024: Report export module / レポートエクスポートモジュール
Responsibilities: Export the current project notebook to PDF, HTML, or
slide form using a local, read-only conversion tool, without invoking any
Jupyter MCP execution call.
Interfaces: exportReport(handle, format) -> ReportPath, writing to
projects/<project_name>/reports/<name>.
Constraints: Must invoke only the configured conversion tool process and
issue zero additional Jupyter MCP code-execution calls (REQ-AIDS-033); must
include the markdown insight cells and referenced chart images from the
source notebook (REQ-AIDS-025).
Requirements: REQ-AIDS-025, REQ-AIDS-033
ADRs: ADR-0007
Depends-On: DES-AIDS-003
