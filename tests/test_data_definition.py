"""Tests for the data-definition manifest (REQ-AIDS-052)."""

import pytest

from ai_data_scientist.data_definition import FieldValue, build_manifest


# @id TEST-AIDS-079
# @verifies REQ-AIDS-052
def test_TEST_AIDS_079_scale_inferred_unit_is_not_verified():
    unit = FieldValue(value="million km²", status="inferred", source="inferred from value scale")
    manifest = build_manifest(
        source={"owner_slug": FieldValue("nsidc/arctic-sea-ice", status="verified")},
        dataset_scope={},
        variables={"extent": {"unit": unit}},
    )
    assert manifest.variables["extent"]["unit"].status == "inferred"
    assert manifest.variables["extent"]["unit"].status != "verified"


# @id TEST-AIDS-080
# @verifies REQ-AIDS-052
def test_TEST_AIDS_080_missing_unit_information_is_unknown():
    unit = FieldValue(value=None, status="unknown")
    manifest = build_manifest(
        source={}, dataset_scope={}, variables={"exports_usd": {"unit": unit}}
    )
    assert manifest.variables["exports_usd"]["unit"].status == "unknown"


# @id TEST-AIDS-081
# @verifies REQ-AIDS-052
def test_TEST_AIDS_081_unresolved_fields_lists_every_unknown_status():
    manifest = build_manifest(
        source={"license": FieldValue(None, status="unknown")},
        dataset_scope={"population": FieldValue("unknown", status="unknown")},
        variables={"value": {"unit": FieldValue(None, status="unknown")}},
    )
    paths = {path for path, _ in manifest.unresolved_fields()}
    assert paths == {"source.license", "dataset_scope.population", "variables.value.unit"}


# @id TEST-AIDS-082
# @verifies REQ-AIDS-052
def test_TEST_AIDS_082_verified_field_preserves_exact_source_text():
    verified = FieldValue(
        value="World Bank Open Data", status="verified", source="Kaggle metadata field 'source'"
    )
    inferred = FieldValue(value="World Bank Open Data", status="inferred", source=None)

    manifest = build_manifest(
        source={"primary_source": verified},
        dataset_scope={},
        variables={"gdp": {"origin": inferred}},
    )

    assert manifest.source["primary_source"].status == "verified"
    assert manifest.source["primary_source"].source == "Kaggle metadata field 'source'"
    assert manifest.variables["gdp"]["origin"].status == "inferred"
    # Same value, different status/provenance: distinguishable, not merged.
    assert manifest.source["primary_source"].value == manifest.variables["gdp"]["origin"].value
    assert manifest.source["primary_source"].status != manifest.variables["gdp"]["origin"].status

    with pytest.raises(Exception):  # noqa: B017 - frozen dataclass must reject mutation
        verified.status = "unknown"


# @id TEST-AIDS-108
# @verifies REQ-AIDS-052
def test_TEST_AIDS_108_inferred_fields_lists_every_inferred_status_disjoint_from_unknown():
    """GitHub #33: a manifest-level check must separately surface every
    "inferred" field, without conflating it with the "unknown" list."""
    manifest = build_manifest(
        source={
            "license": FieldValue(None, status="unknown"),
            "owner_slug": FieldValue("nsidc/arctic-sea-ice", status="inferred"),
        },
        dataset_scope={"population": FieldValue("unknown", status="unknown")},
        variables={
            "extent": {
                "unit": FieldValue("million km²", status="inferred"),
                "scale": FieldValue(None, status="unknown"),
            }
        },
    )

    inferred_paths = {path for path, _ in manifest.inferred_fields()}
    unknown_paths = {path for path, _ in manifest.unresolved_fields()}

    assert inferred_paths == {"source.owner_slug", "variables.extent.unit"}
    assert unknown_paths == {"source.license", "dataset_scope.population", "variables.extent.scale"}
    assert inferred_paths.isdisjoint(unknown_paths)
