"""Approved retrieval destinations and payload-free refresh result contracts."""

from datetime import date
from posixpath import normpath
from typing import Annotated, Literal, Self
from urllib.parse import unquote, urlsplit

from pydantic import (
    BeforeValidator,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)

from schemas.catalog import FactName, FactObservation, Reference, UtcTimestamp
from schemas.common import Contract, Identifier, Text

SourceType = Literal["manufacturer", "retailer", "dataset", "document"]
RefreshStatus = Literal[
    "fetched", "cached", "missing", "stale", "partial", "invalid", "unavailable"
]
CacheState = Literal["miss", "fresh", "stale", "bypass"]
RetrievedFieldStatus = Literal["returned", "missing", "rejected"]
RefreshErrorCode = Literal[
    "product_not_found",
    "refresh_unavailable",
    "incomplete_payload",
    "invalid_payload",
    "source_unavailable",
    "timeout",
    "rate_limited",
    "destination_not_approved",
]


def checked_date(value: object) -> object:
    if isinstance(value, date) and not isinstance(value, str):
        return value
    if isinstance(value, str) and len(value) == 10:
        return value
    raise ValueError("Supply the source check date as YYYY-MM-DD.")


CheckedDate = Annotated[date, BeforeValidator(checked_date)]


def _https_parts(value: str) -> tuple[str, str]:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError("Supply a configured HTTPS destination without credentials.") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
        or any(character.isspace() for character in value)
        or "\\" in value
        or port not in (None, 443)
    ):
        raise ValueError("Supply a configured HTTPS destination without credentials.")
    origin = f"https://{parsed.hostname.lower()}"
    decoded_path = unquote(parsed.path or "/")
    segments = decoded_path.split("/")
    if any(segment in (".", "..") for segment in segments):
        raise ValueError("Destination paths cannot contain traversal segments.")
    normalized = normpath(decoded_path)
    if decoded_path.endswith("/") and not normalized.endswith("/"):
        normalized += "/"
    return origin, normalized


def endpoint(value: str) -> str:
    origin, path = _https_parts(value)
    parsed = urlsplit(value)
    if parsed.query:
        raise ValueError("Configured endpoint prefixes cannot contain a query.")
    return f"{origin}{path}"


def redirect_origin(value: str) -> str:
    origin, path = _https_parts(value)
    parsed = urlsplit(value)
    if path != "/" or parsed.query:
        raise ValueError("Redirect allowlists contain HTTPS origins, not paths or queries.")
    return origin


Endpoint = Annotated[Text, BeforeValidator(endpoint)]
RedirectOrigin = Annotated[Text, BeforeValidator(redirect_origin)]


class ApprovedSource(Contract):
    """One reviewed source registration; disabled records cannot authorize retrieval."""

    source_id: Identifier
    source_type: SourceType
    endpoints: tuple[Endpoint, ...] = Field(min_length=1)
    redirect_origins: tuple[RedirectOrigin, ...] = ()
    access_conditions: Text
    reuse_conditions: Text
    permission_reference: Reference
    attribution: Text
    checked_on: CheckedDate
    enabled: StrictBool
    external_id_namespace: Identifier

    @field_validator("endpoints", "redirect_origins")
    @classmethod
    def unique_destinations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("Configured destinations must be unique.")
        return value


class SourceRegistry(Contract):
    version: Literal["approved-sources-v1"]
    sources: tuple[ApprovedSource, ...]

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        identities = [source.source_id for source in self.sources]
        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate source identity in approved registry.")
        return self


class DestinationNotApproved(ValueError):
    """Fixed authorization failure safe to surface without the candidate URL."""


def authorize_destination(
    source: ApprovedSource, candidate: str, *, redirect: bool = False
) -> bool:
    """Authorize before network access; never include an rejected URL in the error."""
    if not source.enabled:
        raise DestinationNotApproved("Retrieval source is disabled.")
    try:
        origin, path = _https_parts(candidate)
        parsed = urlsplit(candidate)
    except (TypeError, ValueError):
        raise DestinationNotApproved("Retrieval destination is not approved.") from None
    if redirect:
        allowed = origin in source.redirect_origins
    else:
        allowed = any(
            origin == endpoint_origin
            and (
                path == prefix or path.startswith(prefix if prefix.endswith("/") else f"{prefix}/")
            )
            for configured in source.endpoints
            for endpoint_origin, prefix in (_https_parts(configured),)
        )
    if not allowed or parsed.fragment:
        raise DestinationNotApproved("Retrieval destination is not approved.")
    return True


class RefreshResult(Contract):
    """Inspectable bounded outcome; raw source payloads are deliberately not representable."""

    status: RefreshStatus
    source_id: Identifier
    external_id: Identifier
    product_id: Identifier
    evidence_ids: tuple[Identifier, ...]
    cache_state: CacheState
    attempts: int = Field(strict=True, ge=0, le=3)
    started_at: UtcTimestamp
    completed_at: UtcTimestamp
    retrieved_at: UtcTimestamp | None = None
    error_code: RefreshErrorCode | None = None

    @field_validator("evidence_ids")
    @classmethod
    def unique_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("Refresh results cannot repeat evidence IDs.")
        return value

    @model_validator(mode="after")
    def consistent_outcome(self) -> Self:
        if self.completed_at < self.started_at:
            raise ValueError("Refresh completion cannot precede its start.")
        if (
            self.retrieved_at is not None
            and not self.started_at <= self.retrieved_at <= self.completed_at
        ):
            raise ValueError("Retrieval time must fall within the refresh attempt.")
        if self.status in {"fetched", "cached", "stale", "partial"} and not self.evidence_ids:
            raise ValueError("Evidence-bearing outcomes require evidence IDs.")
        if self.status == "fetched" and self.retrieved_at is None:
            raise ValueError("Fetched outcomes require an actual retrieval timestamp.")
        if self.status == "cached" and self.cache_state != "fresh":
            raise ValueError("Cached outcomes require a fresh cache state.")
        if self.status == "stale" and self.cache_state != "stale":
            raise ValueError("Stale outcomes require a stale cache state.")
        successful = self.status in {"fetched", "cached"}
        if successful != (self.error_code is None):
            raise ValueError("Only successful refresh outcomes omit a sanitized error code.")
        return self


class RetrievedField(Contract):
    """One allowlisted source-field result, never a raw response member."""

    field_name: FactName
    status: RetrievedFieldStatus
    evidence_id: Identifier | None = None

    @model_validator(mode="after")
    def consistent_status(self) -> Self:
        if (self.status == "returned") != (self.evidence_id is not None):
            raise ValueError("Returned fields require evidence; absent or rejected fields cannot.")
        return self


class RefreshLookup(Contract):
    """Validated candidate evidence and a payload-free refresh outcome."""

    refresh: RefreshResult
    fields: tuple[RetrievedField, ...]
    observations: tuple[FactObservation, ...]

    @model_validator(mode="after")
    def linked_candidates(self) -> Self:
        evidence = {item.evidence_id for item in self.observations}
        returned = {item.evidence_id for item in self.fields if item.evidence_id is not None}
        if evidence != returned or evidence != set(self.refresh.evidence_ids):
            raise ValueError("Refresh evidence must exactly match returned validated fields.")
        if any(item.validation_status != "unverified" for item in self.observations):
            raise ValueError("Retrieved candidates require later review before selection.")
        return self
