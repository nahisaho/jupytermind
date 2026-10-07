"""CHA2DS2-VASc clinical risk score (DES-AIDS-104 / REQ-AIDS-104).

Pure function module: no network, database, or ML-model call.
"""

from __future__ import annotations


def _check_flag(value, name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name}: must be exactly True or False")


# @id CODE-AIDS-158
# @implements REQ-AIDS-104
# @design DES-AIDS-104
def cha2ds2_vasc_score(
    congestive_heart_failure: bool,
    hypertension: bool,
    age: int,
    diabetes: bool,
    stroke_tia_thromboembolism_history: bool,
    vascular_disease: bool,
    sex: str,
) -> dict[str, int | str]:
    """Compute the fixed-weight CHA2DS2-VASc score and its 3-tier risk category.

    Computational aid only — not a clinical diagnosis or recommendation
    (REQ-AIDS-104). The 3-tier ``risk_category`` mapping is this module's
    own simplification for anticoagulation-discussion framing, not a
    verbatim guideline table.
    """
    if not isinstance(age, int) or isinstance(age, bool):
        raise ValueError("age: must be a non-negative int, not bool or float")
    if age < 0:
        raise ValueError("age: must be >= 0")

    _check_flag(congestive_heart_failure, "congestive_heart_failure")
    _check_flag(hypertension, "hypertension")
    _check_flag(diabetes, "diabetes")
    _check_flag(stroke_tia_thromboembolism_history, "stroke_tia_thromboembolism_history")
    _check_flag(vascular_disease, "vascular_disease")

    if sex not in ("male", "female"):
        raise ValueError("sex: must be 'male' or 'female'")

    score = (
        (1 if congestive_heart_failure else 0)
        + (1 if hypertension else 0)
        + (2 if age >= 75 else 1 if age >= 65 else 0)
        + (1 if diabetes else 0)
        + (2 if stroke_tia_thromboembolism_history else 0)
        + (1 if vascular_disease else 0)
        + (1 if sex == "female" else 0)
    )

    if score == 0:
        risk_category = "low"
    elif score == 1:
        risk_category = "moderate"
    else:
        risk_category = "high"

    return {"score": score, "risk_category": risk_category}
