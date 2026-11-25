"""US-039: synthetic refresh candidates and temporary SQLite only."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
from test_catalog_contracts import catalog, source

from repositories.catalog import CatalogRepository, migrate
from repositories.refresh import RefreshRepository
from repositories.source_registry import SourceRegistryRepository
from schemas.catalog import CatalogEnvelope, FactObservation
from schemas.refresh import (
    ApprovedSource,
    RefreshLookup,
    RefreshResult,
    RetrievedField,
    ReviewedVariantMapping,
    SourceRegistry,
)
from services.catalog_policy import evaluate_catalog
from services.open_beauty_facts import OpenBeautyFactsClient

STAMP = datetime(2026, 10, 20, 10, tzinfo=UTC)


def approved_source() -> ApprovedSource:
    return ApprovedSource(
        source_id="open-beauty-facts",
        source_type="dataset",
        endpoints=("https://world.openbeautyfacts.org/api/v3/product/",),
        redirect_origins=(),
        access_conditions="Synthetic fixture",
        reuse_conditions="Synthetic fixture",
        permission_reference="document:synthetic-permission",
        attribution="Synthetic fixture",
        checked_on="2026-10-20",
        enabled=True,
        external_id_namespace="open-beauty-facts-barcode",
    )


def seeded(tmp_path: Path) -> tuple[Path, CatalogRepository]:
    path = tmp_path / "synthetic.db"
    migrate(path)
    data = catalog()
    data["sources"].append(dict(source("open-beauty-facts"), source_type="dataset"))
    repo = CatalogRepository(path)
    repo.save(CatalogEnvelope.model_validate(data))
    SourceRegistryRepository(path).replace(
        SourceRegistry(
            version="approved-sources-v1",
            sources=(approved_source(),),
        )
    )
    return path, repo


def lookup(*, ingredient: str = "Synthetic A, B") -> RefreshLookup:
    values = {
        "brand": "Synthetic Brand",
        "name": "Synthetic Screen",
        "pack_size": "50 ml",
        "ingredient_declaration": ingredient,
    }
    observations = tuple(
        FactObservation(
            evidence_id=f"obf-{field}-1",
            product_id="synthetic-50ml",
            source_id="open-beauty-facts",
            field_name=field,
            value=value,
            source_reference="https://world.openbeautyfacts.org/api/v3/product/8901234567890.json",
            retrieved_at=STAMP,
            verified_at=STAMP,
            content_version=f"sha256:synthetic-{field}-{value}",
            snapshot_id="synthetic-snapshot",
            validation_status="unverified",
        )
        for field, value in values.items()
    )
    return RefreshLookup(
        refresh=RefreshResult(
            status="fetched",
            source_id="open-beauty-facts",
            external_id="8901234567890",
            product_id="synthetic-50ml",
            evidence_ids=tuple(item.evidence_id for item in observations),
            cache_state="miss",
            attempts=1,
            started_at=STAMP,
            retrieved_at=STAMP,
            completed_at=STAMP,
        ),
        fields=tuple(
            RetrievedField(
                field_name=item.field_name, status="returned", evidence_id=item.evidence_id
            )
            for item in observations
        ),
        observations=observations,
    )


def mapping(**changes: object) -> ReviewedVariantMapping:
    data: dict[str, object] = {
        "source_id": "open-beauty-facts",
        "external_id": "8901234567890",
        "product_id": "synthetic-50ml",
        "catalog_brand": "Synthetic Brand",
        "catalog_name": "Synthetic Screen",
        "catalog_variant": "formulation-a-50ml",
        "catalog_pack_size": "50 ml",
        "source_brand": "Synthetic Brand",
        "source_name": "Synthetic Screen",
        "source_pack_size": "50 ml",
        "source_ingredient_declaration": "Synthetic A, B",
        "review_reference": "document:synthetic-review",
        "reviewed_at": STAMP,
    }
    data.update(changes)
    return ReviewedVariantMapping.model_validate(data)


def test_reviewed_mapping_commits_history_and_outcome_atomically(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    result = RefreshRepository(path).commit(lookup(), mapping())
    assert result.status == "committed"
    after = catalog_repo.read()
    assert len(after.observations) == len(before.observations) + 4
    assert after.resolved_value("synthetic-50ml", "ingredient_declaration") == "Synthetic A, B"
    assert all(item.validation_status == "unverified" for item in after.observations[-4:])
    assert len(RefreshRepository(path).outcomes("synthetic-50ml")) == 1
    assert RefreshRepository(path).mappings("synthetic-50ml")[0].mapping == mapping()


def test_uncertain_mapping_retains_rejected_outcome_without_catalog_mutation(
    tmp_path: Path,
) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    result = RefreshRepository(path).commit(lookup(), mapping(source_pack_size="100 ml"))
    assert result.status == "review_required"
    assert result.outcome_id is not None
    assert catalog_repo.read() == before
    outcomes = RefreshRepository(path).outcomes("synthetic-50ml")
    assert len(outcomes) == 1
    assert outcomes[0].decision == "failed"
    assert outcomes[0].mapping_id is None
    assert outcomes[0].fields == lookup().fields


def test_identical_replay_adds_no_duplicate_evidence_or_outcome(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    first = RefreshRepository(path).commit(lookup(), mapping())
    after_first = catalog_repo.read()
    second = RefreshRepository(path).commit(lookup(), mapping())
    assert first.status == "committed"
    assert second.status == "unchanged"
    assert catalog_repo.read() == after_first
    assert len(RefreshRepository(path).outcomes("synthetic-50ml")) == 1


def test_formula_change_requires_new_review_and_preserves_last_valid(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    result = RefreshRepository(path).commit(lookup(ingredient="Different formula"), mapping())
    assert result.status == "review_required"
    assert catalog_repo.read() == before


def test_disabled_source_cannot_commit_candidate_evidence(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    SourceRegistryRepository(path).replace(
        SourceRegistry(version="approved-sources-v1", sources=())
    )
    result = RefreshRepository(path).commit(lookup(), mapping())
    assert result.status == "rejected"
    assert catalog_repo.read() == before
    assert RefreshRepository(path).outcomes("synthetic-50ml") == ()


def test_storage_failure_rolls_back_mapping_evidence_and_outcome(tmp_path: Path) -> None:
    from repositories.catalog import connection

    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    with connection(path) as con:
        con.execute(
            "CREATE TRIGGER fail_outcome BEFORE INSERT ON refresh_outcomes "
            "BEGIN SELECT RAISE(ABORT, 'private-sentinel'); END"
        )
    result = RefreshRepository(path).commit(lookup(), mapping())
    assert result.status == "failed"
    assert "private-sentinel" not in str(result)
    assert catalog_repo.read() == before
    assert RefreshRepository(path).outcomes("synthetic-50ml") == ()
    with connection(path, readonly=True) as con:
        assert con.execute("SELECT count(*) FROM variant_mappings").fetchone()[0] == 0


def test_failed_refresh_records_outcome_without_advancing_fact_dates(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    failed = RefreshLookup(
        refresh=RefreshResult(
            status="unavailable",
            source_id="open-beauty-facts",
            external_id="8901234567890",
            product_id="synthetic-50ml",
            evidence_ids=(),
            cache_state="miss",
            attempts=3,
            started_at=STAMP,
            completed_at=STAMP,
            error_code="timeout",
        ),
        fields=(),
        observations=(),
    )
    first = RefreshRepository(path).commit(failed)
    second = RefreshRepository(path).commit(failed)
    assert first.status == "committed"
    assert second.status == "unchanged"
    assert catalog_repo.read() == before
    outcomes = RefreshRepository(path).outcomes("synthetic-50ml")
    assert len(outcomes) == 1
    assert outcomes[0].refresh.error_code == "timeout"


def test_missing_mapping_and_incomplete_identity_require_review(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    assert RefreshRepository(path).commit(lookup()).status == "review_required"
    incomplete = lookup().model_copy(
        update={
            "refresh": lookup().refresh.model_copy(
                update={"status": "partial", "error_code": "incomplete_payload"}
            ),
            "fields": tuple(item for item in lookup().fields if item.field_name != "pack_size"),
            "observations": tuple(
                item for item in lookup().observations if item.field_name != "pack_size"
            ),
        }
    )
    incomplete = incomplete.model_copy(
        update={
            "refresh": incomplete.refresh.model_copy(
                update={"evidence_ids": tuple(item.evidence_id for item in incomplete.observations)}
            )
        }
    )
    assert RefreshRepository(path).commit(incomplete, mapping()).status == "review_required"
    assert catalog_repo.read() == before


def test_v2_upgrade_keeps_catalog_registry_and_backup(tmp_path: Path, monkeypatch) -> None:
    from repositories import catalog as storage

    path = tmp_path / "upgrade.db"
    with monkeypatch.context() as patch:
        patch.setattr(storage, "SCHEMA_VERSION", 2)
        storage.migrate(path)
        original = CatalogEnvelope.model_validate(catalog())
        storage.CatalogRepository(path).save(original)
        with storage.connection(path) as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO approved_sources(payload) VALUES (?)",
                (approved_source().model_dump_json(),),
            )
            con.execute("COMMIT")
    backup = storage.migrate(path)
    assert backup is not None
    with storage.connection(backup, readonly=True) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 2
        assert con.execute("SELECT count(*) FROM approved_sources").fetchone()[0] == 1
    assert storage.CatalogRepository(path).read() == original
    assert SourceRegistryRepository(path).read().sources == (approved_source(),)
    assert RefreshRepository(path).outcomes("synthetic-50ml") == ()


def test_source_reference_must_match_reviewed_external_id(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    candidate = lookup()
    other = candidate.observations[0].model_copy(
        update={
            "source_reference": "https://world.openbeautyfacts.org/api/v3/product/0000000000000.json"
        }
    )
    candidate = candidate.model_copy(update={"observations": (other, *candidate.observations[1:])})
    assert RefreshRepository(path).commit(candidate, mapping()).status == "rejected"
    assert catalog_repo.read() == before


def test_duplicate_field_candidates_are_rejected(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    candidate = lookup()
    duplicate = candidate.observations[0].model_copy(update={"evidence_id": "obf-brand-2"})
    candidate = candidate.model_copy(
        update={
            "observations": (*candidate.observations, duplicate),
            "fields": (
                *candidate.fields,
                RetrievedField(
                    field_name="brand", status="returned", evidence_id=duplicate.evidence_id
                ),
            ),
            "refresh": candidate.refresh.model_copy(
                update={"evidence_ids": (*candidate.refresh.evidence_ids, duplicate.evidence_id)}
            ),
        }
    )
    assert RefreshRepository(path).commit(candidate, mapping()).status == "rejected"
    assert catalog_repo.read() == before


def test_wrong_external_id_namespace_is_rejected(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    registry = SourceRegistryRepository(path).read()
    SourceRegistryRepository(path).replace(
        registry.model_copy(
            update={
                "sources": (
                    registry.sources[0].model_copy(
                        update={"external_id_namespace": "different-namespace"}
                    ),
                )
            }
        )
    )
    assert RefreshRepository(path).commit(lookup(), mapping()).status == "rejected"
    assert catalog_repo.read() == before


def test_invalid_outcome_cannot_reference_uncommitted_candidates(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    before = catalog_repo.read()
    candidate = lookup()
    candidate = candidate.model_copy(
        update={
            "refresh": candidate.refresh.model_copy(
                update={"status": "invalid", "error_code": "invalid_payload"}
            )
        }
    )
    assert RefreshRepository(path).commit(candidate).status == "rejected"
    assert catalog_repo.read() == before
    assert RefreshRepository(path).outcomes("synthetic-50ml") == ()


def test_unverified_identity_conflict_withholds_qualification_but_keeps_selected_fact(
    tmp_path: Path,
) -> None:
    path, catalog_repo = seeded(tmp_path)
    candidate = lookup()
    renamed = candidate.observations[1].model_copy(update={"value": "Different label"})
    candidate = candidate.model_copy(
        update={
            "observations": (
                candidate.observations[0],
                renamed,
                *candidate.observations[2:],
            )
        }
    )
    assert (
        RefreshRepository(path).commit(candidate, mapping(source_name="Different label")).status
        == "committed"
    )
    current = catalog_repo.read()
    assert current.resolved_value("synthetic-50ml", "name") == "Synthetic Screen"
    qualification = evaluate_catalog(current, now=STAMP).qualification("synthetic-50ml")
    assert not qualification.qualified
    assert "unresolved_identity" in qualification.reason_codes


def test_adapter_to_repository_cached_replay_reuses_evidence(tmp_path: Path) -> None:
    path, catalog_repo = seeded(tmp_path)
    calls = 0

    def respond(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "status": "success",
                "product": {
                    "brands": "Synthetic Brand",
                    "product_name": "Synthetic Screen",
                    "quantity": "50 ml",
                    "ingredients_text_en": "Synthetic A, B",
                },
            },
        )

    client = OpenBeautyFactsClient(
        approved_source(),
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
        now=lambda: STAMP,
    )
    first = client.lookup(product_id="synthetic-50ml", external_id="8901234567890")
    assert RefreshRepository(path).commit(first, mapping()).status == "committed"
    count = len(catalog_repo.read().observations)
    cached = client.lookup(product_id="synthetic-50ml", external_id="8901234567890")
    assert cached.refresh.status == "cached"
    assert RefreshRepository(path).commit(cached, mapping()).evidence_added == 0
    assert len(catalog_repo.read().observations) == count
    assert calls == 1
