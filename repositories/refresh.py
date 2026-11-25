"""Atomic, review-gated catalog refresh evidence and outcome storage."""

import json
import sqlite3
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from repositories.catalog import SCHEMA_VERSION, CatalogStorageError, _read, _version, connection
from repositories.source_registry import _read_registry
from schemas.catalog import CatalogEnvelope, FactName, FactObservation, FactResolution
from schemas.refresh import (
    RefreshLookup,
    ReviewedVariantMapping,
    StoredRefresh,
    StoredVariantMapping,
    authorize_destination,
)

CommitStatus = Literal["committed", "unchanged", "review_required", "rejected", "failed"]


@dataclass(frozen=True)
class RefreshCommitReport:
    status: CommitStatus
    evidence_added: int = 0
    outcome_id: str | None = None
    reason_code: str | None = None


def _identity(prefix: str, value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}-{sha256(encoded.encode()).hexdigest()}"


def _reviewed(
    current: CatalogEnvelope, lookup: RefreshLookup, mapping: ReviewedVariantMapping
) -> bool:
    result = lookup.refresh
    if (mapping.source_id, mapping.external_id, mapping.product_id) != (
        result.source_id,
        result.external_id,
        result.product_id,
    ):
        return False
    product = next((p for p in current.products if p.product_id == result.product_id), None)
    if product is None or (
        product.brand,
        product.name,
        product.variant,
        product.pack_size,
    ) != (
        mapping.catalog_brand,
        mapping.catalog_name,
        mapping.catalog_variant,
        mapping.catalog_pack_size,
    ):
        return False
    values = {item.field_name: item.value for item in lookup.observations}
    # Require observed exact source identity, pack, and formulation before any write.
    comparisons: tuple[tuple[FactName, str], ...] = (
        ("brand", mapping.source_brand),
        ("name", mapping.source_name),
        ("pack_size", mapping.source_pack_size),
        ("ingredient_declaration", mapping.source_ingredient_declaration),
    )
    if any(values.get(field) != expected for field, expected in comparisons):
        return False
    # An existing stable variant cannot silently become a different formulation.
    return (
        current.resolved_value(product.product_id, "ingredient_declaration")
        == mapping.source_ingredient_declaration
    )


def _combined(current: CatalogEnvelope, candidates: tuple[FactObservation, ...]) -> CatalogEnvelope:
    evidence = {item.evidence_id: item for item in current.observations}
    for item in candidates:
        prior = evidence.get(item.evidence_id)
        if prior is not None and prior != item:
            raise ValueError("Evidence identity was reused with different content.")
        evidence[item.evidence_id] = item
    resolutions = {(item.product_id, item.field_name): item for item in current.resolutions}
    for item in candidates:
        key = (item.product_id, item.field_name)
        resolution = resolutions.get(key)
        if resolution is None:
            resolutions[key] = FactResolution(
                product_id=item.product_id,
                field_name=item.field_name,
                status="unresolved",
                evidence_ids=(item.evidence_id,),
                policy_version="explicit-selection-v1",
            )
        elif resolution.status == "unresolved" and item.evidence_id not in resolution.evidence_ids:
            resolutions[key] = resolution.model_copy(
                update={"evidence_ids": (*resolution.evidence_ids, item.evidence_id)}
            )
    return CatalogEnvelope(
        contract_version="catalog-v1",
        products=current.products,
        sources=current.sources,
        observations=tuple(evidence.values()),
        resolutions=tuple(resolutions.values()),
    )


class RefreshRepository:
    """Commit only reviewed exact mappings; keep every candidate unverified."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def commit(
        self, lookup: RefreshLookup, mapping: ReviewedVariantMapping | None = None
    ) -> RefreshCommitReport:
        try:
            value = RefreshLookup.model_validate_json(lookup.model_dump_json())
            reviewed = (
                ReviewedVariantMapping.model_validate_json(mapping.model_dump_json())
                if mapping is not None
                else None
            )
            with connection(self.path) as con:
                con.execute("BEGIN IMMEDIATE")
                if _version(con) != SCHEMA_VERSION:
                    return RefreshCommitReport("failed", reason_code="migration_required")
                current = _read(con)
                result = value.refresh
                source = next((s for s in current.sources if s.source_id == result.source_id), None)
                approved = next(
                    (s for s in _read_registry(con).sources if s.source_id == result.source_id),
                    None,
                )
                if (
                    source is None
                    or not source.enabled
                    or not any(
                        product.product_id == result.product_id for product in current.products
                    )
                ):
                    return RefreshCommitReport("rejected", reason_code="unknown_identity_or_source")
                if (
                    approved is None
                    or not approved.enabled
                    or approved.source_type != source.source_type
                ):
                    return RefreshCommitReport("rejected", reason_code="source_not_approved")
                if (
                    result.source_id == "open-beauty-facts"
                    and approved.external_id_namespace != "open-beauty-facts-barcode"
                ):
                    return RefreshCommitReport("rejected", reason_code="source_not_approved")
                if any(
                    (item.source_id, item.product_id) != (result.source_id, result.product_id)
                    for item in value.observations
                ):
                    return RefreshCommitReport(
                        "rejected", reason_code="candidate_identity_mismatch"
                    )
                fields = [item.field_name for item in value.observations]
                if len(fields) != len(set(fields)):
                    return RefreshCommitReport("rejected", reason_code="duplicate_candidate_field")
                if result.source_id == "open-beauty-facts":
                    expected_reference = (
                        f"{approved.endpoints[0]}{result.external_id}.json"
                        if len(approved.endpoints) == 1
                        else None
                    )
                    if any(
                        item.source_reference != expected_reference for item in value.observations
                    ):
                        return RefreshCommitReport(
                            "rejected", reason_code="candidate_reference_mismatch"
                        )
                for item in value.observations:
                    authorize_destination(approved, item.source_reference)
                has_candidates = result.status in {"fetched", "partial", "cached"}
                if not has_candidates and result.status != "stale" and value.observations:
                    return RefreshCommitReport("rejected", reason_code="unexpected_candidates")
                if has_candidates and (reviewed is None or not _reviewed(current, value, reviewed)):
                    return RefreshCommitReport(
                        "review_required", reason_code="variant_review_required"
                    )
                if reviewed is not None and not has_candidates:
                    return RefreshCommitReport("rejected", reason_code="unexpected_mapping")
                if (
                    reviewed is not None
                    and con.execute(
                        "SELECT 1 FROM variant_mappings WHERE source_id = ? AND external_id = ? "
                        "AND product_id != ?",
                        (reviewed.source_id, reviewed.external_id, reviewed.product_id),
                    ).fetchone()
                ):
                    return RefreshCommitReport("review_required", reason_code="mapping_conflict")
                stored = {item.evidence_id: item for item in current.observations}
                if result.status == "stale" and not set(result.evidence_ids) <= stored.keys():
                    return RefreshCommitReport("rejected", reason_code="unknown_cached_evidence")
                if any(
                    stored.get(item.evidence_id) not in (None, item) for item in value.observations
                ):
                    return RefreshCommitReport("rejected", reason_code="evidence_id_conflict")
                new_observations = (
                    tuple(item for item in value.observations if item.evidence_id not in stored)
                    if has_candidates
                    else ()
                )
                combined = _combined(current, new_observations)
                mapping_id = (
                    _identity("mapping", reviewed.model_dump(mode="json"))
                    if reviewed is not None
                    else None
                )
                if reviewed is not None and mapping_id is not None:
                    mapped = StoredVariantMapping(mapping_id=mapping_id, mapping=reviewed)
                    con.execute(
                        "INSERT OR IGNORE INTO variant_mappings(payload) VALUES (?)",
                        (mapped.model_dump_json(),),
                    )
                for item in new_observations:
                    con.execute(
                        "INSERT INTO observations(payload) VALUES (?)", (item.model_dump_json(),)
                    )
                old_resolutions = {(r.product_id, r.field_name): r for r in current.resolutions}
                for resolution in combined.resolutions:
                    key = (resolution.product_id, resolution.field_name)
                    if old_resolutions.get(key) == resolution:
                        continue
                    con.execute(
                        "DELETE FROM resolution_evidence WHERE product_id = ? AND field_name = ?",
                        key,
                    )
                    con.execute(
                        "DELETE FROM resolutions WHERE product_id = ? AND field_name = ?", key
                    )
                    con.execute(
                        "INSERT INTO resolutions(payload) VALUES (?)",
                        (resolution.model_dump_json(),),
                    )
                    con.executemany(
                        "INSERT INTO resolution_evidence VALUES (?, ?, ?)",
                        [
                            (resolution.product_id, resolution.field_name, eid)
                            for eid in resolution.evidence_ids
                        ],
                    )
                outcome_id = _identity(
                    "outcome",
                    {"refresh": result.model_dump(mode="json"), "mapping_id": mapping_id},
                )
                outcome = StoredRefresh(
                    outcome_id=outcome_id,
                    refresh=result,
                    mapping_id=mapping_id,
                    decision="accepted" if has_candidates else "failed",
                )
                inserted = con.execute(
                    "INSERT OR IGNORE INTO refresh_outcomes(payload) VALUES (?)",
                    (outcome.model_dump_json(),),
                ).rowcount
                if _read(con) != combined:
                    raise ValueError("Refresh verification failed.")
                con.execute("COMMIT")
                changed = bool(new_observations or inserted)
                return RefreshCommitReport(
                    "committed" if changed else "unchanged",
                    evidence_added=len(new_observations),
                    outcome_id=outcome_id,
                )
        except (sqlite3.Error, OSError):
            return RefreshCommitReport("failed", reason_code="storage_failed")
        except (CatalogStorageError, ValidationError, ValueError):
            return RefreshCommitReport("rejected", reason_code="invalid_refresh")

    def outcomes(self, product_id: str) -> tuple[StoredRefresh, ...]:
        try:
            with connection(self.path, readonly=True) as con:
                con.execute("BEGIN")
                if _version(con) != SCHEMA_VERSION:
                    raise ValueError("Upgrade required.")
                rows = con.execute(
                    "SELECT payload FROM refresh_outcomes WHERE product_id = ? ORDER BY rowid",
                    (product_id,),
                )
                return tuple(StoredRefresh.model_validate(json.loads(row[0])) for row in rows)
        except (sqlite3.Error, OSError, ValueError):
            raise ValueError("Refresh history is unavailable. Restore a verified backup.") from None

    def mappings(self, product_id: str) -> tuple[StoredVariantMapping, ...]:
        try:
            with connection(self.path, readonly=True) as con:
                con.execute("BEGIN")
                if _version(con) != SCHEMA_VERSION:
                    raise ValueError("Upgrade required.")
                rows = con.execute(
                    "SELECT payload FROM variant_mappings WHERE product_id = ? ORDER BY rowid",
                    (product_id,),
                )
                return tuple(
                    StoredVariantMapping.model_validate(json.loads(row[0])) for row in rows
                )
        except (sqlite3.Error, OSError, ValueError):
            raise ValueError(
                "Variant mappings are unavailable. Restore a verified backup."
            ) from None
