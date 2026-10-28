"""US-034: approved destinations and inspectable refresh outcomes."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from schemas.refresh import (
    ApprovedSource,
    DestinationNotApproved,
    RefreshResult,
    SourceRegistry,
    authorize_destination,
)

STAMP = datetime(2026, 10, 20, tzinfo=UTC)


def approved_source(**changes: object) -> ApprovedSource:
    data: dict[str, object] = {
        "source_id": "open-beauty-facts",
        "source_type": "dataset",
        "endpoints": ("https://world.openbeautyfacts.org/api/v3/product/",),
        "redirect_origins": ("https://world.openbeautyfacts.org",),
        "access_conditions": "Public product API; identify the client and obey rate limits.",
        "reuse_conditions": "ODbL database terms; verify field-level reuse before enablement.",
        "permission_reference": "https://world.openbeautyfacts.org/terms-of-use",
        "attribution": "Open Beauty Facts contributors",
        "checked_on": "2026-10-20",
        "enabled": False,
        "external_id_namespace": "open-beauty-facts-barcode",
    }
    data.update(changes)
    return ApprovedSource.model_validate(data)


def test_complete_registry_round_trips_with_disabled_source() -> None:
    registry = SourceRegistry(version="approved-sources-v1", sources=(approved_source(),))
    assert SourceRegistry.model_validate_json(registry.model_dump_json()) == registry
    assert registry.sources[0].enabled is False


@pytest.mark.parametrize(
    "change",
    [
        {"endpoints": ()},
        {"endpoints": ("http://world.openbeautyfacts.org/api/v2/product/",)},
        {"endpoints": ("https://user:secret@example.com/api/",)},
        {"redirect_origins": ("https://example.com/path",)},
        {"checked_on": "2026-10-21T00:00:00Z"},
        {"external_id_namespace": ""},
        {"enabled": 1},
    ],
)
def test_incomplete_or_unsafe_source_metadata_is_rejected(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        approved_source(**change)


def test_only_configured_destinations_and_redirects_are_authorized() -> None:
    enabled = approved_source(enabled=True)
    assert authorize_destination(
        enabled, "https://world.openbeautyfacts.org/api/v3/product/8901234567890?fields=code"
    )
    assert authorize_destination(
        enabled,
        "https://world.openbeautyfacts.org/api/v3/product/8901234567890",
        redirect=True,
    )
    for candidate in (
        "https://evil.example/api/v3/product/8901234567890",
        "https://world.openbeautyfacts.org.evil.example/api/v3/product/1",
        "https://world.openbeautyfacts.org/api/v1/product/1",
        "https://world.openbeautyfacts.org/api/v3/product/../cgi/search.pl",
        "https://world.openbeautyfacts.org/api/v3/product/1#instructions",
    ):
        with pytest.raises(DestinationNotApproved, match="not approved"):
            authorize_destination(enabled, candidate)
    with pytest.raises(DestinationNotApproved, match="disabled"):
        authorize_destination(approved_source(), enabled.endpoints[0])


@pytest.mark.parametrize(
    ("status", "cache_state", "evidence_ids", "error_code"),
    [
        ("fetched", "miss", ("evidence-1",), None),
        ("cached", "fresh", ("evidence-1",), None),
        ("missing", "miss", (), "product_not_found"),
        ("stale", "stale", ("evidence-1",), "refresh_unavailable"),
        ("partial", "miss", ("evidence-1",), "incomplete_payload"),
        ("invalid", "miss", (), "invalid_payload"),
        ("unavailable", "miss", (), "source_unavailable"),
    ],
)
def test_refresh_outcomes_are_typed_and_inspectable(
    status: str, cache_state: str, evidence_ids: tuple[str, ...], error_code: str | None
) -> None:
    result = RefreshResult.model_validate(
        {
            "status": status,
            "source_id": "open-beauty-facts",
            "external_id": "8901234567890",
            "product_id": "product-50ml",
            "evidence_ids": evidence_ids,
            "cache_state": cache_state,
            "attempts": 1,
            "started_at": STAMP,
            "completed_at": STAMP,
            "retrieved_at": STAMP if status in {"fetched", "partial"} else None,
            "error_code": error_code,
        }
    )
    assert result.status == status
    assert "payload" not in result.model_dump()


@pytest.mark.parametrize(
    "change",
    [
        {"status": "fetched", "evidence_ids": (), "error_code": None},
        {"status": "unavailable", "evidence_ids": (), "error_code": None},
        {"status": "fetched", "evidence_ids": ("evidence-1",), "error_code": "secret"},
        {"status": "cached", "evidence_ids": ("evidence-1",), "cache_state": "miss"},
        {"attempts": 4},
        {"completed_at": datetime(2026, 10, 19, tzinfo=UTC)},
        {"raw_payload": {"private": "data"}},
    ],
)
def test_refresh_outcomes_reject_ambiguous_or_raw_results(change: dict[str, object]) -> None:
    data: dict[str, object] = {
        "status": "fetched",
        "source_id": "open-beauty-facts",
        "external_id": "8901234567890",
        "product_id": "product-50ml",
        "evidence_ids": ("evidence-1",),
        "cache_state": "miss",
        "attempts": 1,
        "started_at": STAMP,
        "completed_at": STAMP,
        "retrieved_at": STAMP,
        "error_code": None,
    }
    data.update(change)
    with pytest.raises(ValidationError):
        RefreshResult.model_validate(data)
