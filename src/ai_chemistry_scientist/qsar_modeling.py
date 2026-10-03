"""QSAR linear-regression module (DES-ACHEM-030 / REQ-ACHEM-030)."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LinearRegression

from ai_chemistry_scientist.molecular_descriptors import compute_descriptors, parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "qsar-modeling"
_MIN_TRAINING_COMPOUNDS = 5


def _design_row(descriptors: dict) -> list[float]:
    return [1.0, descriptors["mol_wt"], descriptors["mol_logp"], descriptors["tpsa"]]


def _qsar_modeling_validator(params: dict) -> dict:
    """DES-ACHEM-002 registered atomic validator for this module.

    Validates every training/query SMILES parses, the training set has at
    least 5 compounds, and its augmented design matrix is full column rank
    4. This descriptor extraction is part of validation itself, distinct
    from the governed "model fit" computation (REQ-ACHEM-003, ADR-0030).
    """
    training_set = params.get("training_set")
    query_smiles_list = params.get("query_smiles_list")

    if training_set is None:
        return fail("training_set", "is required")
    if query_smiles_list is None:
        return fail("query_smiles_list", "is required")

    if len(training_set) < _MIN_TRAINING_COMPOUNDS:
        return fail(
            "training_set",
            "must contain at least 5 compounds with a full-rank descriptor matrix",
        )

    design_matrix = []
    for compound in training_set:
        mol = parse_smiles(compound["smiles"])
        if mol is None:
            return fail("training_set", "must parse to a valid RDKit molecule")
        design_matrix.append(_design_row(compute_descriptors(mol)))

    rank = np.linalg.matrix_rank(np.array(design_matrix, dtype=np.float64))
    if rank < 4:
        return fail(
            "training_set",
            "must contain at least 5 compounds with a full-rank descriptor matrix",
        )

    for query_smiles in query_smiles_list:
        if parse_smiles(query_smiles) is None:
            return fail("query_smiles_list", "must parse to a valid RDKit molecule")

    return ok()


register_validator(_MODULE_NAME, _qsar_modeling_validator)


# @id CODE-ACHEM-030
# @implements REQ-ACHEM-030
# @design DES-ACHEM-030
def run_qsar_modeling(training_set: list[dict], query_smiles_list: list[str]) -> dict:
    """Fit an OLS linear regression and predict each query's activity.

    Receives ``training_set``/``query_smiles_list`` already validated
    atomically by its handler wrapper; independently (re)computes each
    molecule's descriptors here for the actual fit/prediction, since
    `validate_parameters`'s boolean-shaped return carries no descriptor
    payload to reuse (ADR-0030) — this duplication is intentional and
    always agrees, since REQ-ACHEM-004 requires every computation to be a
    deterministic pure function of its inputs.
    """
    features = []
    activities = []
    for compound in training_set:
        mol = parse_smiles(compound["smiles"])
        descriptors = compute_descriptors(mol)
        features.append([descriptors["mol_wt"], descriptors["mol_logp"], descriptors["tpsa"]])
        activities.append(compound["activity"])

    model = LinearRegression()
    model.fit(np.array(features, dtype=np.float64), np.array(activities, dtype=np.float64))

    predictions = []
    for query_smiles in query_smiles_list:
        mol = parse_smiles(query_smiles)
        descriptors = compute_descriptors(mol)
        feature_row = np.array(
            [[descriptors["mol_wt"], descriptors["mol_logp"], descriptors["tpsa"]]],
            dtype=np.float64,
        )
        predicted_activity = float(model.predict(feature_row)[0])
        predictions.append({"smiles": query_smiles, "predicted_activity": predicted_activity})

    return {
        "coefficients": [float(c) for c in model.coef_],
        "intercept": float(model.intercept_),
        "predictions": predictions,
    }
