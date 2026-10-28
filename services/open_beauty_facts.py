"""Bounded Open Beauty Facts retrieval with validated, unselected candidates."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from json import JSONDecodeError
from re import fullmatch
from time import sleep as blocking_sleep

import httpx
from pydantic import ValidationError

from schemas.catalog import FactName, FactObservation
from schemas.refresh import (
    ApprovedSource,
    DestinationNotApproved,
    RefreshErrorCode,
    RefreshLookup,
    RefreshResult,
    RefreshStatus,
    RetrievedField,
    authorize_destination,
)

ATTEMPT_TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 2
FRESH_FOR = timedelta(days=30)
RETRY_DELAY_SECONDS = 0.25
USER_AGENT = (
    "cosmetics-product-advisor/0.0.1 (https://github.com/shuklasaket/cosmetics-product-advisor)"
)
_BARCODE = r"[0-9]{8,14}"
_FIELDS: tuple[tuple[FactName, tuple[str, ...]], ...] = (
    ("brand", ("brands",)),
    ("name", ("product_name_en", "product_name")),
    ("pack_size", ("quantity",)),
    ("ingredient_declaration", ("ingredients_text_en", "ingredients_text")),
)


@dataclass(frozen=True)
class _CachedLookup:
    fields: tuple[RetrievedField, ...]
    observations: tuple[FactObservation, ...]
    retrieved_at: datetime


class OpenBeautyFactsClient:
    """Read one reviewed product barcode without retaining raw HTTP bodies."""

    def __init__(
        self,
        source: ApprovedSource,
        *,
        http_client: httpx.Client | None = None,
        now: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = blocking_sleep,
    ) -> None:
        if source.source_id != "open-beauty-facts" or source.source_type != "dataset":
            raise ValueError("Open Beauty Facts requires its reviewed dataset source registration.")
        if source.external_id_namespace != "open-beauty-facts-barcode":
            raise ValueError("Open Beauty Facts requires barcode external IDs.")
        if len(source.endpoints) != 1:
            raise ValueError("Open Beauty Facts requires one reviewed product endpoint.")
        self.source = source
        self.http_client = http_client or httpx.Client(follow_redirects=False)
        self.now = now or (lambda: datetime.now(UTC))
        self.sleep = sleep
        self._cache: dict[tuple[str, str], _CachedLookup] = {}

    def lookup(self, *, product_id: str, external_id: str) -> RefreshLookup:
        """Fetch a mapped barcode, reuse fresh validated candidates, or retain stale ones."""
        if fullmatch(_BARCODE, external_id) is None:
            raise ValueError("Open Beauty Facts external IDs must be 8–14 digit barcodes.")

        started_at = self.now()
        cache_key = (product_id, external_id)
        cached = self._cache.get(cache_key)
        if cached is not None and started_at - cached.retrieved_at <= FRESH_FOR:
            return self._cached_result(product_id, external_id, started_at, cached)

        result = self._retrieve(product_id, external_id, started_at)
        if result.refresh.status in {"fetched", "partial"}:
            self._cache[cache_key] = _CachedLookup(
                fields=result.fields,
                observations=result.observations,
                retrieved_at=result.refresh.retrieved_at or started_at,
            )
        if result.refresh.status == "unavailable" and cached is not None:
            return self._stale_result(product_id, external_id, started_at, cached, result.refresh)
        return result

    def _cached_result(
        self, product_id: str, external_id: str, started_at: datetime, cached: _CachedLookup
    ) -> RefreshLookup:
        completed_at = self.now()
        return RefreshLookup(
            refresh=RefreshResult(
                status="cached",
                source_id=self.source.source_id,
                external_id=external_id,
                product_id=product_id,
                evidence_ids=tuple(item.evidence_id for item in cached.observations),
                cache_state="fresh",
                attempts=0,
                started_at=started_at,
                completed_at=completed_at,
            ),
            fields=cached.fields,
            observations=cached.observations,
        )

    def _stale_result(
        self,
        product_id: str,
        external_id: str,
        started_at: datetime,
        cached: _CachedLookup,
        failed: RefreshResult,
    ) -> RefreshLookup:
        completed_at = self.now()
        return RefreshLookup(
            refresh=RefreshResult(
                status="stale",
                source_id=self.source.source_id,
                external_id=external_id,
                product_id=product_id,
                evidence_ids=tuple(item.evidence_id for item in cached.observations),
                cache_state="stale",
                attempts=failed.attempts,
                started_at=started_at,
                completed_at=completed_at,
                error_code=failed.error_code,
            ),
            fields=cached.fields,
            observations=cached.observations,
        )

    def _retrieve(self, product_id: str, external_id: str, started_at: datetime) -> RefreshLookup:
        destination = f"{self.source.endpoints[0]}{external_id}.json"
        try:
            authorize_destination(self.source, destination)
        except DestinationNotApproved:
            return self._empty(
                "unavailable", product_id, external_id, started_at, 0, "destination_not_approved"
            )

        for attempt in range(1, MAX_RETRIES + 2):
            response, error_code, retryable, backoff = self._request(destination)
            if response is not None:
                if response.status_code == 404:
                    return self._empty(
                        "missing", product_id, external_id, started_at, attempt, "product_not_found"
                    )
                if 300 <= response.status_code < 400:
                    return self._empty(
                        "unavailable",
                        product_id,
                        external_id,
                        started_at,
                        attempt,
                        "destination_not_approved",
                    )
                if response.status_code == 200:
                    return self._map_response(
                        response, product_id, external_id, started_at, attempt, destination
                    )
            if not retryable or attempt == MAX_RETRIES + 1 or backoff > RETRY_DELAY_SECONDS:
                return self._empty(
                    "unavailable", product_id, external_id, started_at, attempt, error_code
                )
            self.sleep(max(RETRY_DELAY_SECONDS, backoff))
        raise AssertionError("The retry loop always returns a bounded outcome.")

    def _request(
        self, destination: str
    ) -> tuple[httpx.Response | None, RefreshErrorCode, bool, float]:
        try:
            response = self.http_client.get(
                destination,
                headers={"User-Agent": USER_AGENT},
                timeout=ATTEMPT_TIMEOUT_SECONDS,
                follow_redirects=False,
            )
        except httpx.TimeoutException:
            return None, "timeout", True, 0.0
        except httpx.TransportError:
            return None, "source_unavailable", True, 0.0
        if response.status_code == 429:
            return response, "rate_limited", True, self._retry_after(response)
        if response.status_code >= 500 or response.status_code == 408:
            return response, "source_unavailable", True, self._retry_after(response)
        if response.status_code >= 400:
            return response, "source_unavailable", False, 0.0
        return response, "source_unavailable", False, 0.0

    @staticmethod
    def _retry_after(response: httpx.Response) -> float:
        try:
            return max(0.0, float(response.headers.get("Retry-After", "0")))
        except ValueError:
            return 0.0

    def _map_response(
        self,
        response: httpx.Response,
        product_id: str,
        external_id: str,
        started_at: datetime,
        attempts: int,
        source_reference: str,
    ) -> RefreshLookup:
        try:
            body = response.json()
        except (JSONDecodeError, ValueError):
            return self._empty(
                "invalid", product_id, external_id, started_at, attempts, "invalid_payload"
            )
        if not isinstance(body, Mapping):
            return self._empty(
                "invalid", product_id, external_id, started_at, attempts, "invalid_payload"
            )
        if body.get("status") in {0, "failure"}:
            return self._empty(
                "missing", product_id, external_id, started_at, attempts, "product_not_found"
            )
        product = body.get("product")
        if body.get("status") not in {1, "success"} or not isinstance(product, Mapping):
            return self._empty(
                "invalid", product_id, external_id, started_at, attempts, "invalid_payload"
            )

        retrieved_at = self.now()
        observations: list[FactObservation] = []
        fields: list[RetrievedField] = []
        rejected = False
        for field_name, source_keys in _FIELDS:
            matched = next((product.get(key) for key in source_keys if key in product), None)
            present = any(key in product for key in source_keys)
            if not present:
                fields.append(RetrievedField(field_name=field_name, status="missing"))
                continue
            if not isinstance(matched, str) or not matched.strip():
                fields.append(RetrievedField(field_name=field_name, status="rejected"))
                rejected = True
                continue
            evidence_id = self._evidence_id(external_id, field_name, matched, retrieved_at)
            try:
                observation = FactObservation(
                    evidence_id=evidence_id,
                    product_id=product_id,
                    source_id=self.source.source_id,
                    field_name=field_name,
                    value=matched,
                    source_reference=source_reference,
                    retrieved_at=retrieved_at,
                    verified_at=retrieved_at,
                    content_version=self._content_version(field_name, matched),
                    snapshot_id=f"obf-{external_id}-{retrieved_at:%Y%m%dT%H%M%SZ}",
                    validation_status="unverified",
                )
            except ValidationError:
                fields.append(RetrievedField(field_name=field_name, status="rejected"))
                rejected = True
                continue
            observations.append(observation)
            fields.append(
                RetrievedField(field_name=field_name, status="returned", evidence_id=evidence_id)
            )

        if not observations:
            return self._empty(
                "invalid", product_id, external_id, started_at, attempts, "invalid_payload", fields
            )
        completed_at = self.now()
        partial = rejected or len(observations) < len(_FIELDS)
        return RefreshLookup(
            refresh=RefreshResult(
                status="partial" if partial else "fetched",
                source_id=self.source.source_id,
                external_id=external_id,
                product_id=product_id,
                evidence_ids=tuple(item.evidence_id for item in observations),
                cache_state="miss",
                attempts=attempts,
                started_at=started_at,
                completed_at=completed_at,
                retrieved_at=retrieved_at,
                error_code="incomplete_payload" if partial else None,
            ),
            fields=tuple(fields),
            observations=tuple(observations),
        )

    def _empty(
        self,
        status: RefreshStatus,
        product_id: str,
        external_id: str,
        started_at: datetime,
        attempts: int,
        error_code: RefreshErrorCode,
        fields: list[RetrievedField] | None = None,
    ) -> RefreshLookup:
        return RefreshLookup(
            refresh=RefreshResult(
                status=status,
                source_id=self.source.source_id,
                external_id=external_id,
                product_id=product_id,
                evidence_ids=(),
                cache_state="miss",
                attempts=attempts,
                started_at=started_at,
                completed_at=self.now(),
                error_code=error_code,
            ),
            fields=tuple(fields or ()),
            observations=(),
        )

    @staticmethod
    def _content_version(field_name: str, value: str) -> str:
        return sha256(f"{field_name}\0{value}".encode()).hexdigest()

    @staticmethod
    def _evidence_id(external_id: str, field_name: str, value: str, retrieved_at: datetime) -> str:
        material = f"{external_id}\0{field_name}\0{value}\0{retrieved_at.isoformat()}"
        return f"obf-{sha256(material.encode()).hexdigest()[:24]}"
