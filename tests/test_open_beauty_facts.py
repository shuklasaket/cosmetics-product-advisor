"""US-036: bounded, payload-free Open Beauty Facts product retrieval."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx

from schemas.refresh import ApprovedSource
from services.open_beauty_facts import OpenBeautyFactsClient


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 10, 28, 12, tzinfo=UTC)

    def now(self) -> datetime:
        return self.value


def source() -> ApprovedSource:
    return ApprovedSource(
        source_id="open-beauty-facts",
        source_type="dataset",
        endpoints=("https://world.openbeautyfacts.org/api/v3/product/",),
        redirect_origins=(),
        access_conditions="Read-only documented product API with an identifying User-Agent.",
        reuse_conditions="ODbL database attribution applies; product images are excluded.",
        permission_reference="https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/license-be-on-the-legal-side/",
        attribution="Open Beauty Facts contributors",
        checked_on="2026-10-28",
        enabled=True,
        external_id_namespace="open-beauty-facts-barcode",
    )


def client(
    handler: Callable[[httpx.Request], httpx.Response], clock: Clock
) -> OpenBeautyFactsClient:
    return OpenBeautyFactsClient(
        source(),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        now=clock.now,
        sleep=lambda _: None,
    )


def test_fetches_validated_candidates_without_exposing_the_source_payload() -> None:
    clock = Clock()

    def handler(request: httpx.Request) -> httpx.Response:
        assert (
            str(request.url)
            == "https://world.openbeautyfacts.org/api/v3/product/3560070791460.json"
        )
        assert request.headers["User-Agent"].startswith("cosmetics-product-advisor/")
        assert request.extensions["timeout"]["read"] == 10.0
        return httpx.Response(
            200,
            json={
                "status": "success",
                "product": {
                    "brands": "Nuxe",
                    "product_name": "Huile Prodigieuse",
                    "quantity": "50 ml",
                    "ingredients_text_en": "Helianthus Annuus Seed Oil",
                },
            },
        )

    result = client(handler, clock).lookup(
        product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460"
    )

    assert result.refresh.status == "fetched"
    assert result.refresh.attempts == 1
    assert {item.field_name for item in result.observations} == {
        "brand",
        "name",
        "pack_size",
        "ingredient_declaration",
    }
    assert {item.status for item in result.fields} == {"returned"}
    assert "payload" not in result.model_dump_json()
    assert "Helianthus" not in result.refresh.model_dump_json()


def test_keeps_missing_and_invalid_fields_explicit() -> None:
    clock = Clock()

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": "success", "product": {"brands": "", "quantity": 50}},
        )

    result = client(handler, clock).lookup(
        product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460"
    )

    assert result.refresh.status == "invalid"
    assert result.refresh.error_code == "invalid_payload"
    assert result.observations == ()
    assert {item.status for item in result.fields} == {"missing", "rejected"}


def test_missing_product_is_not_retried_or_fabricated() -> None:
    clock = Clock()
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"status": "failure"})

    result = client(handler, clock).lookup(
        product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460"
    )

    assert calls == 1
    assert result.refresh.status == "missing"
    assert result.refresh.error_code == "product_not_found"
    assert result.observations == ()


def test_retries_transient_failures_at_most_twice_then_caches_validated_result() -> None:
    clock = Clock()
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "status": "success",
                "product": {"brands": "Nuxe", "product_name": "Huile"},
            },
        )

    connector = client(handler, clock)
    fetched = connector.lookup(
        product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460"
    )
    cached = connector.lookup(product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460")

    assert calls == 3
    assert fetched.refresh.attempts == 3
    assert cached.refresh.status == "cached"
    assert cached.refresh.cache_state == "fresh"


def test_marks_expired_cached_data_stale_when_refresh_fails() -> None:
    clock = Clock()
    mode = "success"

    def handler(_: httpx.Request) -> httpx.Response:
        if mode == "success":
            return httpx.Response(
                200,
                json={
                    "status": "success",
                    "product": {"brands": "Nuxe", "product_name": "Huile"},
                },
            )
        return httpx.Response(503)

    connector = client(handler, clock)
    connector.lookup(product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460")
    clock.value += timedelta(days=31)
    mode = "failure"

    result = connector.lookup(product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460")

    assert result.refresh.status == "stale"
    assert result.refresh.cache_state == "stale"
    assert result.refresh.error_code == "source_unavailable"


def test_defers_long_server_backoff_without_a_retry() -> None:
    clock = Clock()
    waits: list[float] = []

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "60"})

    connector = OpenBeautyFactsClient(
        source(),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        now=clock.now,
        sleep=waits.append,
    )

    result = connector.lookup(product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460")

    assert waits == []
    assert result.refresh.status == "unavailable"
    assert result.refresh.error_code == "rate_limited"
    assert result.refresh.attempts == 1


def test_timeout_retries_are_bounded_and_sanitized() -> None:
    clock = Clock()
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("fixture timeout", request=request)

    result = client(handler, clock).lookup(
        product_id="nuxe-huile-prodigieuse-50ml", external_id="3560070791460"
    )

    assert calls == 3
    assert result.refresh.status == "unavailable"
    assert result.refresh.error_code == "timeout"
    assert result.refresh.attempts == 3
