"""Load reviewed, payload-free PRD 02 Open Beauty Facts release evidence."""

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import NoReturn

from pydantic import ValidationError

from repositories.catalog import CatalogRepository, CatalogStorageError
from repositories.refresh import RefreshRepository
from repositories.source_registry import SourceRegistryRepository, SourceRegistryStorageError
from schemas.catalog import FactName, FactObservation
from schemas.refresh import (
    ApprovedSource,
    RefreshLookup,
    RefreshResult,
    RetrievedField,
    ReviewedVariantMapping,
    SourceRegistry,
)
from services.catalog_import import MAX_INPUT_BYTES, unique_object


@dataclass(frozen=True)
class EvidenceImportReport:
    status: str
    mappings: int
    accepted_outcomes: int
    reason: str | None = None


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ValueError("Supply an existing database and one release-evidence JSON file.")


def _content_version(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def _lookup(mapping: ReviewedVariantMapping) -> RefreshLookup:
    """Reconstruct only the reviewed allowlisted fields, never a source payload."""
    stamp = mapping.reviewed_at.astimezone(UTC)
    values: dict[FactName, str] = {
        "brand": mapping.source_brand,
        "name": mapping.source_name,
        "pack_size": mapping.source_pack_size,
        "ingredient_declaration": mapping.source_ingredient_declaration,
    }
    reference = f"https://world.openbeautyfacts.org/api/v3/product/{mapping.external_id}.json"
    observations = tuple(
        FactObservation(
            evidence_id=f"obf-{mapping.external_id}-{field}-{_content_version(value)[7:19]}",
            product_id=mapping.product_id,
            source_id=mapping.source_id,
            field_name=field,
            value=value,
            source_reference=reference,
            retrieved_at=stamp,
            verified_at=stamp,
            content_version=_content_version(value),
            snapshot_id=f"obf-reviewed-{mapping.external_id}-{stamp.date().isoformat()}",
            validation_status="unverified",
        )
        for field, value in values.items()
    )
    return RefreshLookup(
        refresh=RefreshResult(
            status="fetched",
            source_id=mapping.source_id,
            external_id=mapping.external_id,
            product_id=mapping.product_id,
            evidence_ids=tuple(item.evidence_id for item in observations),
            cache_state="miss",
            attempts=1,
            started_at=stamp,
            retrieved_at=stamp,
            completed_at=stamp,
        ),
        fields=tuple(
            RetrievedField(
                field_name=item.field_name,
                status="returned",
                evidence_id=item.evidence_id,
            )
            for item in observations
        ),
        observations=observations,
    )


def import_prd02_release_evidence(evidence_path: Path, database: Path) -> EvidenceImportReport:
    """Persist five reviewed mappings and their accepted outcomes after catalog import."""
    try:
        raw = evidence_path.read_bytes()
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("evidence input exceeds the local limit")
        data = json.loads(raw.decode(), object_pairs_hook=unique_object)
        if set(data) != {"version", "approved_source", "mappings"}:
            raise ValueError("release evidence has unexpected fields")
        if data["version"] != "prd02-release-evidence-v1" or not isinstance(data["mappings"], list):
            raise ValueError("release evidence version is unsupported")
        source = ApprovedSource.model_validate(data["approved_source"])
        mappings = tuple(ReviewedVariantMapping.model_validate(item) for item in data["mappings"])
        if len(mappings) != 5 or len({item.product_id for item in mappings}) != len(mappings):
            raise ValueError("release evidence needs five distinct reviewed mappings")
        if any(item.source_id != source.source_id for item in mappings):
            raise ValueError("mappings must use the approved source")
        catalog = CatalogRepository(database).read()
        catalog_source = next(
            (item for item in catalog.sources if item.source_id == source.source_id),
            None,
        )
        if catalog_source is None or not catalog_source.enabled:
            raise ValueError("catalog does not contain the reviewed enabled source")
        for mapping in mappings:
            product = next(
                (item for item in catalog.products if item.product_id == mapping.product_id),
                None,
            )
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
                raise ValueError("catalog identity no longer matches a reviewed mapping")
            if catalog.resolved_value(mapping.product_id, "ingredient_declaration") != (
                mapping.source_ingredient_declaration
            ):
                raise ValueError("catalog formulation no longer matches a reviewed mapping")
    except (OSError, UnicodeError, ValueError, ValidationError, CatalogStorageError):
        return EvidenceImportReport("rejected", 0, 0, "invalid_release_evidence")

    try:
        registry_repository = SourceRegistryRepository(database)
        current = registry_repository.read()
        sources = {item.source_id: item for item in current.sources}
        sources[source.source_id] = source
        registry_repository.replace(
            SourceRegistry(version="approved-sources-v1", sources=tuple(sources.values()))
        )
        repository = RefreshRepository(database)
        reports = tuple(repository.commit(_lookup(mapping), mapping) for mapping in mappings)
    except SourceRegistryStorageError:
        return EvidenceImportReport("failed", 0, 0, "storage_failed")

    accepted = sum(report.status in {"committed", "unchanged"} for report in reports)
    if accepted != len(mappings):
        return EvidenceImportReport("rejected", len(mappings), accepted, "mapping_rejected")
    return EvidenceImportReport("committed", len(mappings), accepted)


def main() -> int:
    parser = Parser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("database", type=Path)
    try:
        arguments = parser.parse_args()
        report = import_prd02_release_evidence(arguments.evidence, arguments.database)
    except ValueError:
        report = EvidenceImportReport("rejected", 0, 0, "invalid_arguments")
    print(json.dumps(report.__dict__, sort_keys=True))
    return 0 if report.status == "committed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
