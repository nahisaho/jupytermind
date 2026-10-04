"""Drug-likeness rule screening module (DES-ACHEM-060 / REQ-ACHEM-060)."""

from __future__ import annotations

from rdkit.Chem import Descriptors, rdMolDescriptors

from ai_chemistry_scientist.molecular_descriptors import compute_descriptors, parse_smiles
from ai_chemistry_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "drug-likeness-rules"

# Named Ghose/Egan threshold constants (DES-ACHEM-060) so the fixed rule
# boundaries are documented in one place instead of as inline magic numbers.
GHOSE_MOLWT_MIN, GHOSE_MOLWT_MAX = 160, 480
GHOSE_MOLLOGP_MIN, GHOSE_MOLLOGP_MAX = -0.4, 5.6
GHOSE_MOLMR_MIN, GHOSE_MOLMR_MAX = 40, 130
GHOSE_HEAVY_ATOM_COUNT_MIN, GHOSE_HEAVY_ATOM_COUNT_MAX = 20, 70
EGAN_TPSA_MAX = 131.6
EGAN_MOLLOGP_MAX = 5.88

_GHOSE_CRITERIA = (
    (
        "MolWt",
        lambda d, heavy_atom_count, mol_mr: GHOSE_MOLWT_MIN <= d["mol_wt"] <= GHOSE_MOLWT_MAX,
    ),
    (
        "MolLogP",
        lambda d, heavy_atom_count, mol_mr: GHOSE_MOLLOGP_MIN <= d["mol_logp"] <= GHOSE_MOLLOGP_MAX,
    ),
    ("MolMR", lambda d, heavy_atom_count, mol_mr: GHOSE_MOLMR_MIN <= mol_mr <= GHOSE_MOLMR_MAX),
    (
        "heavy_atom_count",
        lambda d, heavy_atom_count, mol_mr: (
            GHOSE_HEAVY_ATOM_COUNT_MIN <= heavy_atom_count <= GHOSE_HEAVY_ATOM_COUNT_MAX
        ),
    ),
)
_EGAN_CRITERIA = (
    ("TPSA", lambda d: d["tpsa"] <= EGAN_TPSA_MAX),
    ("MolLogP", lambda d: d["mol_logp"] <= EGAN_MOLLOGP_MAX),
)


# @id CODE-ACHEM-917
# @implements REQ-ACHEM-003 REQ-ACHEM-060
# @design DES-ACHEM-002
def _drug_likeness_rules_validator(params: dict) -> dict:
    if "smiles" not in params:
        return fail("smiles", "is required")
    if parse_smiles(params["smiles"]) is None:
        return fail("smiles", "must parse to a valid RDKit molecule")
    return ok()


register_validator(_MODULE_NAME, _drug_likeness_rules_validator)


# @id CODE-ACHEM-060
# @implements REQ-ACHEM-060
# @design DES-ACHEM-060
def run_drug_likeness_rules(smiles: str) -> dict:
    """Compute fixed-threshold Ghose and Egan rule outcomes for ``smiles``."""
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("smiles must already be validated by the handler wrapper")
    descriptors = compute_descriptors(mol)
    aromatic_ring_count = int(rdMolDescriptors.CalcNumAromaticRings(mol))
    mol_mr = float(Descriptors.MolMR(mol))
    heavy_atom_count = int(mol.GetNumHeavyAtoms())

    ghose_violations = [
        name for name, check in _GHOSE_CRITERIA if not check(descriptors, heavy_atom_count, mol_mr)
    ]
    egan_violations = [name for name, check in _EGAN_CRITERIA if not check(descriptors)]

    return {
        "aromatic_ring_count": aromatic_ring_count,
        "mol_mr": mol_mr,
        "heavy_atom_count": heavy_atom_count,
        "ghose_violations": ghose_violations,
        "ghose_pass": len(ghose_violations) == 0,
        "egan_violations": egan_violations,
        "egan_pass": len(egan_violations) == 0,
    }
