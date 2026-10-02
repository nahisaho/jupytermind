"""Data-definition and provenance manifest with per-field confidence status.

Implements DES-AIDS-040 (REQ-AIDS-052): structurally distinguishes
reproducible file identity (owner/slug, SHA-256, retrieval time) from
verified semantic metadata (units, definitions, measurement pathway),
making data-definition uncertainty visible and queryable instead of
silently promoting an inferred value to "verified".
"""

from __future__ import annotations

from dataclasses import dataclass, field

_VALID_STATUSES = frozenset({"verified", "inferred", "reported", "unknown"})


# @id CODE-AIDS-071
# @implements REQ-AIDS-052
# @design DES-AIDS-040
@dataclass(frozen=True)
class FieldValue:
    """A single semantic field paired with its confidence status.

    Frozen so a constructed instance's status cannot be mutated in place;
    changing a field's confidence always requires building a brand-new
    ``FieldValue``, which is always an explicit caller action rather than an
    automatic promotion from "inferred"/"unknown" to "verified".
    """

    value: object
    status: str
    source: str | None = None

    def __post_init__(self) -> None:
        if self.status not in _VALID_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(_VALID_STATUSES)}, got {self.status!r}."
            )


# @id CODE-AIDS-083
# @implements REQ-AIDS-052
# @design DES-AIDS-040
@dataclass(frozen=True)
class DataDefinitionManifest:
    """Aggregated data-definition manifest for one ingested dataset."""

    source: dict
    dataset_scope: dict
    variables: dict[str, dict[str, FieldValue]]
    transformations: tuple = field(default_factory=tuple)

    def unresolved_fields(self) -> list[tuple[str, FieldValue]]:
        """Return every ``FieldValue`` across the manifest whose status is "unknown".

        Each entry's first element is a dotted path identifying its location
        (e.g. ``"source.license"`` or ``"variables.value.unit"``).
        """
        return self._fields_with_status("unknown")

    def inferred_fields(self) -> list[tuple[str, FieldValue]]:
        """Return every ``FieldValue`` across the manifest whose status is "inferred".

        GitHub #33: surfaces unconfirmed-but-assumed fields as their own
        actionable, listed item, separate from (and never overlapping
        with) :meth:`unresolved_fields`'s "unknown" list.
        """
        return self._fields_with_status("inferred")

    def _fields_with_status(self, status: str) -> list[tuple[str, FieldValue]]:
        matches: list[tuple[str, FieldValue]] = []
        for key, field_value in self.source.items():
            if isinstance(field_value, FieldValue) and field_value.status == status:
                matches.append((f"source.{key}", field_value))
        for key, field_value in self.dataset_scope.items():
            if isinstance(field_value, FieldValue) and field_value.status == status:
                matches.append((f"dataset_scope.{key}", field_value))
        for variable_name, fields in self.variables.items():
            for field_name, field_value in fields.items():
                if isinstance(field_value, FieldValue) and field_value.status == status:
                    matches.append((f"variables.{variable_name}.{field_name}", field_value))
        return matches


# @id CODE-AIDS-072
# @implements REQ-AIDS-052
# @design DES-AIDS-040
def build_manifest(
    source: dict,
    dataset_scope: dict,
    variables: dict[str, dict[str, FieldValue]],
    transformations: tuple = (),
) -> DataDefinitionManifest:
    """Construct a ``DataDefinitionManifest`` from its component dicts."""
    return DataDefinitionManifest(
        source=source,
        dataset_scope=dataset_scope,
        variables=variables,
        transformations=tuple(transformations),
    )
