"""US-037: synthetic public evidence, real SQLite and offline Streamlit interactions."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from test_app import APP, submit_default_search
from test_refresh_commit import lookup, mapping, seeded

from repositories.refresh import RefreshRepository


def mapped_page(tmp_path: Path, monkeypatch) -> AppTest:
    path, _ = seeded(tmp_path)
    assert RefreshRepository(path).commit(lookup(), mapping()).status == "committed"
    monkeypatch.setenv("ADVISOR_DATABASE_PATH", str(path))
    page = AppTest.from_file(str(APP)).run()
    submit_default_search(page)
    return page.button(key="detail_synthetic-50ml").click().run()


def test_manual_refresh_requires_explicit_click(tmp_path: Path, monkeypatch) -> None:
    page = mapped_page(tmp_path, monkeypatch)
    assert not page.exception
    assert not page.button(key="refresh_synthetic-50ml").disabled
    assert "Last refresh: fetched" in "\n".join(item.value for item in page.text)
    assert len(RefreshRepository(tmp_path / "synthetic.db").outcomes("synthetic-50ml")) == 1


def test_detail_displays_freshness_conflicts_and_unverified_history(
    tmp_path: Path, monkeypatch
) -> None:
    from datetime import UTC, datetime

    from repositories.catalog import CatalogRepository
    from schemas.catalog import CatalogEnvelope

    path, repo = seeded(tmp_path)
    RefreshRepository(path).commit(lookup(), mapping())
    data = repo.read().model_dump(mode="json")
    alternate = dict(data["observations"][0])
    alternate.update(evidence_id="synthetic-conflict", value="Different brand")
    # Keep current facts fresh while retaining old, unverified source evidence.
    fresh = []
    for observation in data["observations"]:
        if observation["validation_status"] == "verified":
            updated = dict(
                observation,
                evidence_id="fresh-" + observation["evidence_id"],
                verified_at=datetime.now(UTC).isoformat(),
            )
            fresh.append(updated)
            for resolution in data["resolutions"]:
                if resolution["evidence_ids"] == [observation["evidence_id"]]:
                    resolution["evidence_ids"] = [updated["evidence_id"]]
    data["observations"].extend(fresh)
    data["observations"].append(alternate)
    CatalogRepository(path).save(CatalogEnvelope.model_validate(data))
    monkeypatch.setenv("ADVISOR_DATABASE_PATH", str(path))
    page = AppTest.from_file(str(APP)).run()
    submit_default_search(page)
    page.button(key="detail_synthetic-50ml").click().run()
    text = "\n".join(item.value for item in page.text)
    assert not page.exception
    assert "Freshness: fresh" in text
    assert "Conflicting evidence: 1" in text
    assert "Different brand" in text
    assert "Validation: unverified" in text
    assert "2026-10-20T10:00:00Z" in text


def install_http(monkeypatch, handler, clock=None):
    import httpx

    import services.manual_refresh as module
    from services.open_beauty_facts import OpenBeautyFactsClient

    monkeypatch.setattr(
        module,
        "OpenBeautyFactsClient",
        lambda source: OpenBeautyFactsClient(
            source,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            sleep=lambda _: None,
            now=clock,
        ),
    )


def response_product():
    return {
        "status": 1,
        "product": {
            "brands": "Synthetic Brand",
            "product_name": "Synthetic Screen",
            "quantity": "50 ml",
            "ingredients_text_en": "Synthetic A, B",
            "private_payload": "REMOTE-SECRET-SENTINEL",
        },
    }


def test_click_fetches_once_then_cached_without_changing_selected_facts(
    tmp_path: Path, monkeypatch
) -> None:
    import httpx

    from repositories.catalog import CatalogRepository

    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, json=response_product())

    install_http(monkeypatch, handler)
    page = mapped_page(tmp_path, monkeypatch)
    before = CatalogRepository(tmp_path / "synthetic.db").read()
    assert calls == []
    page.button(key="refresh_synthetic-50ml").click().run()
    assert not page.exception
    assert len(calls) == 1
    assert "Last refresh: fetched" in [item.value for item in page.text]
    page.button(key="refresh_synthetic-50ml").click().run()
    assert not page.exception
    assert len(calls) == 1
    assert "Last refresh: cached" in [item.value for item in page.text]
    after = CatalogRepository(tmp_path / "synthetic.db").read()
    assert before.resolutions == after.resolutions
    assert before.observations == after.observations[: len(before.observations)]
    assert "REMOTE-SECRET-SENTINEL" not in after.model_dump_json()


@pytest.mark.parametrize(
    ("kind", "status", "code", "attempts"),
    [
        ("timeout", "unavailable", "timeout", 3),
        ("rate", "unavailable", "rate_limited", 3),
        ("invalid", "invalid", "invalid_payload", 1),
        ("missing", "missing", "product_not_found", 1),
        ("partial", "partial", "incomplete_payload", 1),
    ],
)
def test_refresh_failures_preserve_dated_facts(
    tmp_path: Path, monkeypatch, caplog, capsys, kind, status, code, attempts
) -> None:
    import httpx

    from repositories.catalog import CatalogRepository

    calls = []

    def handler(request):
        calls.append(request)
        if kind == "timeout":
            raise httpx.ReadTimeout("REMOTE-SECRET-SENTINEL")
        if kind == "rate":
            return httpx.Response(429)
        if kind == "invalid":
            return httpx.Response(200, text="REMOTE-SECRET-SENTINEL")
        if kind == "missing":
            return httpx.Response(200, json={"status": 0})
        payload = response_product()
        del payload["product"]["ingredients_text_en"]
        return httpx.Response(200, json=payload)

    install_http(monkeypatch, handler)
    page = mapped_page(tmp_path, monkeypatch)
    path = tmp_path / "synthetic.db"
    before = CatalogRepository(path).read()
    page.button(key="refresh_synthetic-50ml").click().run()
    assert not page.exception
    assert len(calls) == attempts
    text = "\n".join(item.value for item in page.text)
    warnings = "\n".join(item.value for item in page.warning)
    assert f"Last refresh: {status}" in text
    assert code in warnings
    assert "Synthetic A, B" in text
    assert "2026-10-19T10:00:00Z" in text
    assert "Freshness: stale" in text
    assert CatalogRepository(path).read() == before
    if kind == "partial":
        assert "review_required" in warnings
        assert "not saved" in warnings
        assert "ingredient_declaration: missing" in text
    assert "REMOTE-SECRET-SENTINEL" not in text + warnings + caplog.text + str(capsys.readouterr())
    assert b"REMOTE-SECRET-SENTINEL" not in path.read_bytes()


def test_operator_status_shows_counts_and_recovery_without_search_inputs(
    tmp_path: Path, monkeypatch
) -> None:
    page = mapped_page(tmp_path, monkeypatch)
    page.toggle(key="show_operator_status").set_value(True).run()
    assert not page.exception
    text = "\n".join(item.value for item in page.text)
    assert "Product ID: synthetic-50ml" in text
    assert "Stale facts: 13" in text
    assert "Conflicting facts: 0" in text
    assert any("Review stale" in item.value for item in page.info)


def test_stale_cache_failure_keeps_evidence_dates(tmp_path: Path, monkeypatch) -> None:
    from datetime import timedelta

    import httpx
    from test_open_beauty_facts import Clock

    from repositories.catalog import CatalogRepository

    clock = Clock()
    fail = False

    def handler(_):
        if fail:
            raise httpx.ReadTimeout("REMOTE-SECRET-SENTINEL")
        return httpx.Response(200, json=response_product())

    install_http(monkeypatch, handler, clock.now)
    page = mapped_page(tmp_path, monkeypatch)
    page.button(key="refresh_synthetic-50ml").click().run()
    before = CatalogRepository(tmp_path / "synthetic.db").read()
    fail = True
    clock.value += timedelta(days=31)
    page.button(key="refresh_synthetic-50ml").click().run()
    assert not page.exception
    assert "Last refresh: stale" in [item.value for item in page.text]
    assert any("timeout" in item.value for item in page.warning)
    assert CatalogRepository(tmp_path / "synthetic.db").read() == before


def test_stored_review_required_outcome_exposes_field_statuses_after_restart(
    tmp_path: Path, monkeypatch
) -> None:
    path, _ = seeded(tmp_path)
    candidate = lookup()
    candidate = candidate.model_copy(
        update={
            "refresh": candidate.refresh.model_copy(
                update={
                    "status": "partial",
                    "error_code": "incomplete_payload",
                    "evidence_ids": tuple(
                        item.evidence_id
                        for item in candidate.observations
                        if item.field_name != "ingredient_declaration"
                    ),
                }
            ),
            "fields": tuple(
                item for item in candidate.fields if item.field_name != "ingredient_declaration"
            )
            + (candidate.fields[-1].model_copy(update={"status": "missing", "evidence_id": None}),),
            "observations": tuple(
                item
                for item in candidate.observations
                if item.field_name != "ingredient_declaration"
            ),
        }
    )
    assert RefreshRepository(path).commit(candidate, mapping()).status == "review_required"

    monkeypatch.setenv("ADVISOR_DATABASE_PATH", str(path))
    page = AppTest.from_file(str(APP)).run()
    submit_default_search(page)
    page.button(key="detail_synthetic-50ml").click().run()

    assert not page.exception
    text = "\n".join(item.value for item in page.text)
    assert "Last refresh: partial" in text
    assert "ingredient_declaration: missing" in text


def test_storage_failure_is_not_presented_as_saved_success(tmp_path: Path, monkeypatch) -> None:
    import httpx

    from repositories.refresh import RefreshCommitReport

    install_http(monkeypatch, lambda _: httpx.Response(200, json=response_product()))
    page = mapped_page(tmp_path, monkeypatch)
    monkeypatch.setattr(
        RefreshRepository,
        "commit",
        lambda *args: RefreshCommitReport("failed", reason_code="storage_failed"),
    )
    page.button(key="refresh_synthetic-50ml").click().run()
    assert not page.exception
    assert "Last refresh: fetched" in [item.value for item in page.text]
    assert any(
        "storage_failed" in item.value and "not saved" in item.value for item in page.warning
    )
    assert len(RefreshRepository(tmp_path / "synthetic.db").outcomes("synthetic-50ml")) == 1


def test_revoked_source_disables_action_and_service_rechecks_authorization(
    tmp_path: Path, monkeypatch
) -> None:
    from repositories.source_registry import SourceRegistryRepository
    from schemas.refresh import SourceRegistry
    from services.manual_refresh import ManualRefreshService, RefreshUnavailableError

    page = mapped_page(tmp_path, monkeypatch)
    path = tmp_path / "synthetic.db"
    service = ManualRefreshService(path)
    service.target("synthetic-50ml")
    registry = SourceRegistryRepository(path)
    registry.replace(
        SourceRegistry(
            version="approved-sources-v1",
            sources=tuple(s.model_copy(update={"enabled": False}) for s in registry.read().sources),
        )
    )
    with pytest.raises(RefreshUnavailableError, match="approve"):
        service.refresh("synthetic-50ml")
    page.run()
    assert not page.exception
    assert page.button(key="refresh_synthetic-50ml").disabled
    assert len(RefreshRepository(path).outcomes("synthetic-50ml")) == 1


def test_no_mapping_keeps_catalog_read_only(tmp_path: Path, monkeypatch) -> None:
    path, _ = seeded(tmp_path)
    monkeypatch.setenv("ADVISOR_DATABASE_PATH", str(path))
    page = AppTest.from_file(str(APP)).run()
    submit_default_search(page)
    page.button(key="detail_synthetic-50ml").click().run()
    assert not page.exception
    assert page.button(key="refresh_synthetic-50ml").disabled
    assert any("mapping outside" in item.value for item in page.info)


def test_operator_unavailable_storage_is_safe_and_does_not_create_database() -> None:
    page = AppTest.from_file(str(APP)).run()
    page.toggle(key="show_operator_status").set_value(True).run()
    assert not page.exception
    assert any("Catalog unavailable" in item.value for item in page.warning)
    assert not Path("database/advisor.db").exists()


def test_operator_reports_errors_and_excludes_private_session_fields(
    tmp_path: Path, monkeypatch
) -> None:
    import httpx

    install_http(monkeypatch, lambda _: httpx.Response(429, headers={"Retry-After": "60"}))
    page = mapped_page(tmp_path, monkeypatch)
    page.session_state["private_test_input"] = "USER-SECRET-SENTINEL"
    page.button(key="refresh_synthetic-50ml").click().run()
    page.toggle(key="show_operator_status").set_value(True).run()
    operator = page.container(key="operator_status")
    visible = "\n".join(
        item.value for kind in ("text", "warning", "info", "caption") for item in operator.get(kind)
    )
    assert not page.exception
    assert "rate_limited" in visible
    assert "Product ID: synthetic-50ml" in visible
    assert "USER-SECRET-SENTINEL" not in visible
    assert b"USER-SECRET-SENTINEL" not in (tmp_path / "synthetic.db").read_bytes()


def test_non_barcode_mapping_stays_read_only(tmp_path: Path, monkeypatch) -> None:
    """The mapping contract accepts identifiers; the OBF UI needs a barcode."""
    from schemas.refresh import RefreshLookup

    path, _ = seeded(tmp_path)
    data = lookup().model_dump(mode="json")
    data["refresh"]["external_id"] = "not-a-barcode"
    for observation in data["observations"]:
        observation["source_reference"] = observation["source_reference"].replace(
            "8901234567890", "not-a-barcode"
        )
    report = RefreshRepository(path).commit(
        RefreshLookup.model_validate(data), mapping(external_id="not-a-barcode")
    )
    assert report.status == "committed"
    monkeypatch.setenv("ADVISOR_DATABASE_PATH", str(path))
    page = AppTest.from_file(str(APP)).run()
    submit_default_search(page)
    page.button(key="detail_synthetic-50ml").click().run()
    assert not page.exception
    assert page.button(key="refresh_synthetic-50ml").disabled
