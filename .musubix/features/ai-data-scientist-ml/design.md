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
ADRs: ADR-0058
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
ADRs: ADR-0059
Depends-On: DES-AIDS-013

## DES-AIDS-067: Paired hypothesis-test dispatch for experiment evaluation / 実験評価の対応あり仮説検定ディスパッチ
Responsibilities: Extend `evaluate_experiment` so callers can request
paired significance tests over aligned control/treatment rows or folds
without changing the legacy independent-samples `test="ttest"` behavior.
Interfaces: `evaluate_experiment(control, treatment, test, language="en",
*, y_true=None, metric_fn=None, iterations=1000, confidence_level=0.95,
random_state=None) -> ExperimentResult`, where `test` accepts `ttest`,
`paired_t`, `wilcoxon`, or `paired_bootstrap`.
Constraints: `test="ttest"` must continue to call
`scipy.stats.ttest_ind(control, treatment)` with the same defaults as the
pre-CHANGE-010 implementation. `test="paired_t"` must call
`scipy.stats.ttest_rel(control, treatment)` and `test="wilcoxon"` must
call `scipy.stats.wilcoxon(control, treatment)`. Every paired test path
must require equal-length control/treatment inputs with identical index
order, and must reject any NaN or infinite value before dispatch, because
row/fold alignment and finite numeric pairs are part of the paired-
comparison contract.
Requirements: REQ-AIDS-079, REQ-AIDS-080
ADRs: ADR-0092 (direct SciPy paired-test dispatch).
Depends-On: DES-AIDS-020

## DES-AIDS-068: Paired bootstrap metric-comparison engine / 対応のあるブートストラップ比較エンジン
Responsibilities: Compare aligned control/treatment predictions or
aligned fold-level scores by repeatedly resampling matched pair indices
with replacement, recomputing a treatment-minus-control score difference
for each bootstrap sample, and summarizing the resulting distribution.
Interfaces: `paired_bootstrap(control, treatment, *, y_true=None,
metric_fn=None, iterations=1000, confidence_level=0.95,
random_state=None) -> ExperimentResult`, invoked internally by
`DES-AIDS-067`'s `evaluate_experiment(...)` path for
`test="paired_bootstrap"`. When `metric_fn` and `y_true` are both
provided, one bootstrap iteration computes
`metric_fn(y_true_sample, treatment_sample) - metric_fn(y_true_sample,
control_sample)` on the same sampled row indices; when `y_true` contains
repeated class labels, those sampled indices are drawn within each label
stratum so class-dependent metrics such as ROC AUC stay well-defined.
When both are omitted, one bootstrap iteration computes the mean of
`treatment_sample - control_sample` across the sampled fold-score pairs.
Constraints: `metric_fn` and `y_true` are an all-or-nothing pair: a
prediction-comparison bootstrap requires both, while a fold-score
comparison requires neither. `iterations` must be a positive integer and
`confidence_level` must be strictly between 0 and 1. The observed
difference is computed on the full aligned inputs before resampling, and
the confidence interval is the empirical lower/upper quantile pair at
`((1-confidence_level)/2, 1-(1-confidence_level)/2)` of the bootstrap
difference distribution. This bootstrap path is interval estimation only:
it does not claim a hypothesis-test p-value from the resampled
distribution. When used on fold-level CV scores, the interval summarizes
paired resampling of the reported folds but does not remove any
cross-fold/cross-model dependence already present in those scores.
Requirements: REQ-AIDS-081
ADRs: ADR-0093 (paired-resampling bootstrap engine, interval-only).
Depends-On: DES-AIDS-020

## DES-AIDS-069: Experiment-result payload for paired comparisons / 対応比較向け実験結果ペイロード
Responsibilities: Preserve the existing `ExperimentResult` fields used by
the legacy t-test path while adding optional confidence-interval output
for bootstrap comparisons and a shared interpretation path for all
supported experiment tests.
Interfaces: `ExperimentResult = @dataclass(frozen=True) {statistic: float,
p_value: float, interpretation: str, confidence_interval:
tuple[float, float] | None = None}`. For `ttest`, `paired_t`, and
`wilcoxon`, `statistic` is the hypothesis-test statistic and
`confidence_interval` remains `None`. For `paired_bootstrap`, `statistic`
is the observed treatment-minus-control difference and
`confidence_interval` contains the bootstrap interval reported to the
caller while `p_value` is `NaN` to signal that this path does not expose
an inferential p-value.
Constraints: The existing positional fields (`statistic`, `p_value`,
`interpretation`) must remain present so current `test="ttest"` callers
continue to receive the same shape. `_interpret` remains the bilingual
formatter for significance messaging on the hypothesis-test paths, while
the bootstrap path uses a separate bilingual interval-estimate formatter
that explicitly avoids significance claims.
Requirements: REQ-AIDS-079, REQ-AIDS-080, REQ-AIDS-081
ADRs: ADR-0094 (extend ExperimentResult with optional confidence interval).
Depends-On: DES-AIDS-020, DES-AIDS-067, DES-AIDS-068
Code: CODE-AIDS-101 through CODE-AIDS-105 in `experiment_evaluation.py`.

## DES-AIDS-090: Repeated multi-seed experiment comparison aggregator / 複数seed反復比較集約器
Responsibilities: Repeat one control-versus-treatment comparison across a
caller-supplied sequence of split seeds (and optional model seeds), preserve
the per-seed metrics and treatment-minus-control improvements, and summarize
their central tendency, seed variability, and paired sign counts in one
reusable result object.
Interfaces: `summarize_seed_variability(compare_fn, *, split_seeds,
model_seeds=None) -> SeedComparisonSummary`, where `compare_fn(split_seed,
model_seed)` returns one comparison result for that seed pair and
`SeedComparisonSummary = @dataclass(frozen=True) {results:
tuple[SeedComparisonResult, ...], mean_improvement: float,
seed_variability: float, sign_counts: dict[str, int]}`. Each
`SeedComparisonResult` stores the requested `split_seed`, the effective
`model_seed`, the control metric, the treatment metric, and the derived
improvement.
Constraints: Results preserve the requested seed order exactly so notebook
callers can relate each returned row to the seed they supplied. The
improvement for each seed is always `treatment_metric - control_metric`.
`mean_improvement` is the arithmetic mean of those per-seed improvements.
`seed_variability` is the observed improvement range
`max(improvements) - min(improvements)`, matching the adoption-threshold
examples in REQ-AIDS-090/091. `sign_counts` reports the number of positive,
zero, and negative paired improvements across the repeated comparisons.
Requirements: REQ-AIDS-090
ADRs: ADR-0054
Depends-On: DES-AIDS-020

## DES-AIDS-091: Seed-variability adoption-threshold classifier / seed揺れ採用閾値分類器
Responsibilities: Convert the observed variability from
`DES-AIDS-090` into an explicit adoption threshold and classify a candidate
improvement as adoption-worthy, within observed seed noise, or regression.
Interfaces: `judge_improvement(summary, candidate_improvement=None,
threshold=None) -> AdoptionDecision`, where
`AdoptionDecision = @dataclass(frozen=True) {candidate_improvement: float,
threshold: float, classification: str}` and omitting `candidate_improvement`
uses `summary.mean_improvement`.
Constraints: Unless a caller explicitly overrides it, `threshold` equals
`summary.seed_variability` exactly. Classification is `"adopt"` only when
`candidate_improvement > threshold`, `"within_seed_variability"` when
`0 <= candidate_improvement <= threshold`, and `"regression"` when
`candidate_improvement < 0`. The decision payload records both the threshold
and the measured improvement so downstream notebook commentary can explain why
an apparently positive gain was not adopted.
Requirements: REQ-AIDS-091
ADRs: ADR-0055
Depends-On: DES-AIDS-090

## DES-AIDS-092: Three-way holdout selection-bias evaluator / 3分割ホールドアウト選択バイアス評価器
Responsibilities: Partition labeled rows into train/selection/final-evaluation
subsets, select the best candidate configuration using only the selection
subset, and report both the selection-time and final-evaluation improvements so
optimism from configuration selection is measurable.
Interfaces: `evaluate_selection_bias_holdout(df, target, *, baseline,
candidates, evaluate_candidate_fn, split_seed=42, train_fraction=0.6,
selection_fraction=0.2, evaluation_fraction=0.2, assumption_manifest=None) ->
SelectionBiasHoldoutResult`, where `evaluate_candidate_fn(train_df,
selection_df, evaluation_df, baseline, candidates)` returns per-candidate
selection/evaluation metrics and the chosen winner, and
`SelectionBiasHoldoutResult = @dataclass(frozen=True) {train_index:
tuple, selection_index: tuple, evaluation_index: tuple, selected_candidate:
str, selection_improvement: float, evaluation_improvement: float,
optimism: float, assumption_findings: tuple | None = None}`.
Constraints: The three partitions are mutually disjoint and their union equals
the input rows exactly once. The default fractions must split rows in the
60/20/20 pattern requested by REQ-AIDS-092, with rounding handled so the three
partition lengths still sum exactly to the full row count. Candidate selection
must use only selection-partition metrics; final-evaluation metrics are read
only after the winner is fixed. `optimism` is
`selection_improvement - evaluation_improvement`, so a positive value quantifies
selection optimism. Integration with `analysis_assumptions` is optional and
non-blocking in this change: when `assumption_manifest` is supplied, the result
may carry findings/assumptions about using a dedicated selection split, but the
core evaluator must not require that module to operate.
Requirements: REQ-AIDS-092
ADRs: ADR-0056
Depends-On: DES-AIDS-020
Code: CODE-AIDS-131 through CODE-AIDS-140 in `experiment_evaluation.py` and,
optionally, `analysis_assumptions.py`.

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
Responsibilities: Compute the default global feature-importance
explainability artifact for fitted models supported by the default
`explain_model(..., method="default")` contract defined in DES-AIDS-070 and
report it subject to DES-AIDS-010's evidence rules. Models trained via
DES-AIDS-012 are one supported source of such fitted models, not the only one.
Interfaces: The concrete public `explain_model(...) -> ExplainabilityResult`
contract is specified in DES-AIDS-070; this design section owns the default
global explainability responsibility that DES-AIDS-070 refines.
Constraints: For the default global explainability path, the top-ranked
feature must match the reference scikit-learn `feature_importances_` ordering
for tree-based models or the absolute-coefficient ordering defined by
REQ-AIDS-082 for coefficient-based models
(REQ-AIDS-021 acceptance).
Requirements: REQ-AIDS-021
ADRs: ADR-0053
Depends-On: DES-AIDS-012

## DES-AIDS-070: Explainability result contract and method selection / 説明結果契約と手法選択
Responsibilities: Extend `src/ai_data_scientist.explainability.explain_model`
with keyword-only method selection while preserving the legacy 2-argument call,
and normalize every path into a single `ExplainabilityResult` contract exposing
the existing `feature_importances`/`ranking` fields plus explicit method
metadata.
Interfaces: `explain_model(model, feature_names, *, method: Literal["default",
"signed_contributions", "permutation"] = "default", x=None, y=None, scoring:
str | None = None, n_repeats: int = 5, random_state: int = 42) ->
ExplainabilityResult`, where `ExplainabilityResult = @dataclass(frozen=True)
{feature_importances: dict[str, float], ranking: list[str], importance_kind:
str, contribution_kind: str | None = None, signed_contributions:
list[dict[str, float]] | None = None, baseline_values: list[float] | None =
None, raw_predictions: list[float] | None = None, additivity_check:
dict[str, float | bool] | None = None, scoring: str | None = None}`.
Constraints: The default `method="default"` path must produce the same ranking
and feature-importance values as the pre-change implementation for models using
`feature_importances_` or single-output `abs(coef_)`, differing only by the
added metadata fields. For supported class-aligned multiclass coefficient
models (for example `LogisticRegression`) exposing a 2D `coef_` matrix with
one row per class, it must aggregate global per-feature importance as
`np.abs(coef_).mean(axis=0)` before pairing values with `feature_names`,
preserve one scalar importance per feature instead of silently truncating
flattened class-specific coefficients, and derive `ranking` by sorting those
aggregated per-feature values in descending order. `importance_kind` is `"split"` for `feature_importances_`,
`"coefficient_magnitude"` for coefficient magnitudes,
`"mean_absolute_signed_contribution"` for signed-contribution aggregation, and
`"permutation"` for permutation importance.
Requirements: REQ-AIDS-082, REQ-AIDS-083, REQ-AIDS-084
ADRs: ADR-0053
Depends-On: DES-AIDS-019

## DES-AIDS-071: Signed-contribution provider normalization / 符号付き寄与プロバイダー正規化
Responsibilities: Resolve the strongest available signed-contribution provider
for `method="signed_contributions"` in this order: native
`model.predict(..., pred_contrib=True)`, optional `shap.Explainer`, then a
single-output linear additive decomposition derived from `coef_` and
`intercept_`; for supported single-output regression and binary-classification
models, normalize the chosen provider into row-aligned signed feature
contribution dicts, baseline values, raw-output values, and an additive-
consistency report.
Interfaces: Internal helpers
`_compute_signed_contributions(model, frame, feature_names) ->
{contribution_kind, contributions_matrix, baseline_values, raw_predictions,
additivity_check}` and `_predict_raw_output(model, frame) -> ndarray | None`.
Constraints: Input-row order must be preserved exactly in the returned
`signed_contributions` list. Native `pred_contrib` outputs that include an
extra bias column must be split into `contributions_matrix[:, :-1]` and
`baseline_values = matrix[:, -1]`. The linear fallback supports only
single-output regression/binary-classification models whose flattened
`coef_` length matches `feature_names`; it computes contributions as
`frame.to_numpy(dtype=float) * coef_` and compares
`baseline_values + contributions.sum(axis=1)` against `decision_function(frame)`
when available, else `predict(frame)`. If model raw-output values are
unavailable, the result must leave `raw_predictions` unset and mark
`additivity_check.passed` unavailable instead of synthesizing a successful
comparison from the reconstructed sum alone. Multi-class provider outputs are
out of scope for this change; a native or SHAP output shape that cannot be
normalized to one contribution vector per row over `feature_names` falls
through to the next provider or, if none remain, raises `ValueError`
instructing the caller to install optional `shap` support or request
`method="permutation"` instead.
Requirements: REQ-AIDS-083
ADRs: none — provider selection is a deterministic preference order over
existing library capabilities, not an architectural fork.
Depends-On: DES-AIDS-070
Implementation: `CODE-AIDS-106`-`CODE-AIDS-110` in
`src/ai_data_scientist/explainability.py` (CHANGE-011); native `pred_contrib`
row-count mismatches are validated and treated as a non-fatal fall-through to
the SHAP/linear providers rather than propagated as a raw shape error.

## DES-AIDS-072: Permutation-importance path / permutation importance経路
Responsibilities: For `method="permutation"`, validate the presence of
feature rows and target labels, call
`sklearn.inspection.permutation_importance`, and return mean permutation
importances plus the scoring metadata needed to interpret them.
Interfaces: Internal helper `_compute_permutation_importance(model, frame, y,
feature_names, scoring, n_repeats, random_state) -> ExplainabilityResult`.
Constraints: The helper passes `scoring` through unchanged when provided and
passes `None` otherwise so scikit-learn uses the estimator's default score.
The returned `feature_importances` map uses `result.importances_mean` without
taking absolute values, because negative permutation importance is itself
meaningful evidence of instability/noise. `ranking` sorts those mean values in
descending order. The result sets `importance_kind == "permutation"` and
`scoring` to the caller-supplied scorer string or `None`.
Requirements: REQ-AIDS-084
ADRs: none — scikit-learn already defines the relevant permutation-importance
algorithm and scorer interface; this design only exposes it.
Depends-On: DES-AIDS-070

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

## DES-AIDS-062: Reusable supervised fold-plan builder / 再利用可能な教師あり学習fold計画生成
Responsibilities: Normalize the requested supervised-validation mode into a reusable list of train/test row-index folds, either by generating folds from `StratifiedKFold`, `KFold`, or `GroupKFold`, or by reusing a caller-supplied fold plan verbatim.
Interfaces: `build_cv_splits(df, target, model_type, cv_strategy, n_splits, random_state, groups=None, cv_splits=None) -> list[tuple[list, list]]`, where each tuple contains train-row indices and test-row indices expressed in the dataframe's original index labels.
Constraints: Cross-validation is supported only when `df.index.is_unique` so every emitted row label maps to exactly one row. `StratifiedKFold` is valid only for classification and must stratify on `df[target]`; `GroupKFold` requires one group label per input row and must keep every group entirely on one side of a fold. Re-supplied `cv_splits` are validated before reuse: every train/test label must exist in the dataframe index, each fold's train/test sides must be disjoint, and every input row must appear in the test side of exactly one fold so OOF artifacts are well-defined.
Requirements: REQ-AIDS-074
ADRs: none — the design composes scikit-learn's standard splitters directly and stores only their emitted row-index partitions, with no competing architecture considered.
Depends-On: DES-AIDS-012

## DES-AIDS-063: Probability-aware supervised evaluation results / 確率対応の教師あり学習評価結果
Responsibilities: Extend the supervised modeling interface so a caller can request a configurable scoring metric, evaluate either one legacy holdout split or a reusable fold plan, and receive fold scores plus out-of-fold predictions/probabilities in a backward-compatible result object.
Interfaces: `trainModel(df, target, modelType, testSize=0.2, randomState=42, scoring=None, cvStrategy=None, nSplits=5, groups=None, cvSplits=None, estimator=None, **modelParams) -> ModelResult`, where `ModelResult` keeps the legacy `{model, metrics, trainIndex, testIndex}` fields (using the first fold's indices when cross-validation is active for backward-compatible shape) and adds optional `{scoring, fold_scores, cv_splits, oof_predictions, oof_probabilities}` fields.
Constraints: If `cvStrategy`/`cvSplits` are absent, the function stays on the existing single `train_test_split` path so prior callers observe the same split behavior and legacy metric keys. If cross-validation is active, `cv_splits` is the authoritative split artifact and `oof_predictions` are aligned to the input row order. `oof_probabilities` is populated only when the estimator implements `predict_proba`; probability-dependent scoring (`roc_auc`, `log_loss`) requires that capability and otherwise raises `ValueError` instead of silently substituting another score.
Requirements: REQ-AIDS-074, REQ-AIDS-075
ADRs: none — the extension augments the existing result contract around scikit-learn estimators rather than introducing a new modeling subsystem.
Depends-On: DES-AIDS-012, DES-AIDS-062

## DES-AIDS-064: Shared-fold tuning comparator / 共通foldを用いるチューニング比較器
Responsibilities: Evaluate every hyperparameter/model candidate by delegating to the probability-aware supervised evaluation path, preserve the exact per-candidate modeling artifacts, and compute the winning candidate according to the requested scoring direction.
Interfaces: `tuneOrCompare(df, target, grid, modelType="classification", scoring=None, cvStrategy=None, nSplits=5, groups=None, cvSplits=None) -> TuningResult {best_params, best_metric, all_candidates, scoring?, cv_splits?, best_result?}` where each `all_candidates` entry contains the candidate descriptor, the selected metric value, its fold scores, and the underlying `ModelResult`.
Constraints: Every candidate in one invocation must use the same fold plan, either caller-supplied or generated once then reused. Higher-is-better scoring (`accuracy`, `precision`, `recall`, `roc_auc`, `r2`) selects the maximum metric, while lower-is-better scoring (`log_loss`, `rmse`) selects the minimum. Candidate ordering must not depend on dictionary iteration side effects or per-candidate re-splitting.
Requirements: REQ-AIDS-076
ADRs: none — the comparator is a thin policy layer over DES-AIDS-063 with no alternative orchestration architecture evaluated.
Depends-On: DES-AIDS-017, DES-AIDS-063

## DES-AIDS-065: Shared-fold AutoML candidate ranking / 共通foldを用いるAutoML候補順位付け
Responsibilities: Build an AutoML candidate registry, evaluate each candidate through the shared-fold tuning/modeling path, and return a consistently sorted ranked comparison that exposes each candidate's fold scores and modeling artifacts.
Interfaces: `runAutoML(df, target, modelType="classification", scoring=None, cvStrategy=None, nSplits=5, groups=None, cvSplits=None, candidateEstimators=None) -> AutoMLResult {ranked_candidates, scoring?, cv_splits?}` where each ranked candidate contains its `model_name`, selected metric value, fold scores, and underlying `ModelResult`.
Constraints: If `candidateEstimators` is omitted, the module uses the existing built-in registry so legacy AutoML requests still evaluate the same default model set. If `candidateEstimators` is supplied, its named estimators are appended to that built-in registry and every candidate is evaluated on the exact same fold plan. Ranked output sorts descending for higher-is-better metrics and ascending for lower-is-better metrics.
Requirements: REQ-AIDS-077, REQ-AIDS-078
ADRs: none — AutoML continues to be a composition of existing modeling/tuning paths with an alternate candidate source, not a separate architecture.
Depends-On: DES-AIDS-018, DES-AIDS-064

## DES-AIDS-066: Pluggable estimator resolver / 差し替え可能な推定器解決器
Responsibilities: Resolve either a built-in `model_name`, a caller-supplied estimator instance, or a caller-supplied estimator factory into a fresh sklearn-compatible estimator object for each fit across modeling, tuning, and AutoML flows.
Interfaces: `resolve_estimator(model_type, model_name=None, estimator=None, model_params=None) -> estimator` for single-model training, and AutoML/tuning callers may pass `{name: estimator_or_factory}` or per-grid `{"estimator": estimator_or_factory}` descriptors that flow into the same resolver.
Constraints: The resolved estimator must implement `fit` and `predict`; probability-dependent scoring also requires `predict_proba`. Built-in models preserve the current hard-coded defaults (including existing `random_state=42` injections where they already exist). External estimator instances are cloned or recreated per fit so cross-validation folds and candidate comparisons never share trained state.
Requirements: REQ-AIDS-078
ADRs: none — the resolver centralizes already-implicit estimator construction rules without introducing a new dependency boundary.
Depends-On: DES-AIDS-063, DES-AIDS-064, DES-AIDS-065
Code: CODE-AIDS-119 through CODE-AIDS-124 (renumbered at merge to avoid colliding with CHANGE-008's CODE-AIDS-094/095 in `feature_engineering.py`; see CHANGE-009.md).
