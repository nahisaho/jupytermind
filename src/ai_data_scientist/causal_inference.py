"""Causal-inference helpers (single-covariate propensity-score matching)."""

import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import PerfectSeparationError

_MATCH_NOTE = (
    "Matched pairs alone do not identify or estimate a causal effect; "
    "validity additionally requires exchangeability, positivity, correct "
    "model specification, and no unmeasured confounding."
)


def _is_finite_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value == value
        and abs(value) != float("inf")
    )


# @id CODE-AIDS-168
# @implements REQ-AIDS-113
# @design DES-AIDS-111
def propensity_score_match(covariate: list, treatment: list) -> dict:
    """Fit a single-covariate logistic propensity model and greedily match treated-to-control units."""
    if not isinstance(covariate, list) or len(covariate) < 2:
        raise ValueError("covariate: must be a list of at least 2 finite numbers")
    if not all(_is_finite_number(v) for v in covariate):
        raise ValueError("covariate: entries must all be finite numbers")
    if not isinstance(treatment, list) or len(treatment) != len(covariate):
        raise ValueError("covariate, treatment: must be the same length")
    if not all(t in (0, 1, True, False) for t in treatment):
        raise ValueError("treatment: entries must each be 0, 1, or bool")

    treated_idx = [i for i, t in enumerate(treatment) if t]
    control_idx = [i for i, t in enumerate(treatment) if not t]
    if not treated_idx or not control_idx:
        raise ValueError("treatment: must contain at least 1 treated (1) and 1 control (0) unit")

    design = sm.add_constant(covariate)
    try:
        result = sm.Logit(treatment, design).fit(disp=0)
    except PerfectSeparationError as exc:
        raise ValueError(
            "covariate, treatment: logistic fit did not converge "
            "(data may be perfectly or quasi-separated)"
        ) from exc
    if result.mle_retvals.get("converged") is not True:
        raise ValueError(
            "covariate, treatment: logistic fit did not converge "
            "(data may be perfectly or quasi-separated)"
        )

    propensity_scores = [float(s) for s in result.predict(design)]

    unmatched_controls = set(control_idx)
    matches = []
    for treated in treated_idx:
        if not unmatched_controls:
            break
        best_control = min(
            unmatched_controls,
            key=lambda ci: abs(propensity_scores[ci] - propensity_scores[treated]),
        )
        matches.append(
            {
                "treated_index": treated,
                "control_index": best_control,
                "score_distance": abs(propensity_scores[best_control] - propensity_scores[treated]),
            }
        )
        unmatched_controls.discard(best_control)

    return {
        "propensity_scores": propensity_scores,
        "matches": matches,
        "note": _MATCH_NOTE,
    }
