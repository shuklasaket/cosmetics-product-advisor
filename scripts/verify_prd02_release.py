"""Verify the strict, payload-free PRD 02 release gate."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import NoReturn

from repositories.catalog import CatalogRepository, CatalogStorageError
from repositories.refresh import RefreshRepository
from repositories.source_registry import SourceRegistryRepository, SourceRegistryStorageError

MIN_PRODUCTS = 20
MAX_PRODUCTS = 30
MIN_PER_CATEGORY = 10
MIN_REVIEWED_MAPPINGS = 5
PRICE_AVAILABILITY_MAX_AGE = timedelta(days=7)
OTHER_FACT_MAX_AGE = timedelta(days=30)


@dataclass(frozen=True)
class Prd02ReleaseReport:
    status: str
    product_count: int
    sunscreen_count: int
    moisturiser_count: int
    reviewed_mapping_count: int
    accepted_refresh_count: int
    freshness_limits_days: dict[str, int]
    failures: tuple[str, ...]


def _age(when: datetime, today: date) -> timedelta:
    return datetime.combine(today, when.timetz()).astimezone(UTC) - when


def verify_prd02_release(database: Path, *, today: date | None = None) -> Prd02ReleaseReport:
    """Read-only gate; never mutates storage or exposes source payloads."""
    checked = today or date.today()
    failures: list[str] = []
    product_count = sunscreen_count = moisturiser_count = 0
    mapping_count = accepted_count = 0
    try:
        catalog = CatalogRepository(database).read()
        registry = SourceRegistryRepository(database).read()
        refresh = RefreshRepository(database)
    except (CatalogStorageError, SourceRegistryStorageError, ValueError, OSError):
        failures.append("catalog, approved-source registry, or refresh history is unavailable")
        return Prd02ReleaseReport(
            "failed", 0, 0, 0, 0, 0, {"price_availability": 7, "other_facts": 30}, tuple(failures)
        )

    product_count = len(catalog.products)
    sunscreen_count = sum(p.category == "sunscreen" for p in catalog.products)
    moisturiser_count = sum(p.category == "moisturiser" for p in catalog.products)
    if not MIN_PRODUCTS <= product_count <= MAX_PRODUCTS:
        failures.append("catalog must contain between 20 and 30 exact product variants")
    if sunscreen_count < MIN_PER_CATEGORY or moisturiser_count < MIN_PER_CATEGORY:
        failures.append("catalog must contain at least 10 sunscreen and 10 moisturiser variants")

    if not registry.sources:
        failures.append("approved source registry must contain reviewed sources")
    for source in (*catalog.sources, *registry.sources):
        enabled = getattr(source, "enabled", False)
        permission = getattr(source, "permission_reference", "")
        attribution = getattr(source, "attribution", "")
        if not enabled:
            failures.append("all release sources must be enabled")
        if not permission or not attribution:
            failures.append("every release source requires permission and attribution")

    for product in catalog.products:
        try:
            mappings = refresh.mappings(product.product_id)
            outcomes = refresh.outcomes(product.product_id)
        except ValueError:
            failures.append("refresh history is invalid or unavailable")
            break
        mapping_count += len(mappings)
        accepted_ids = {item.mapping_id for item in mappings}
        accepted_count += sum(
            item.decision == "accepted"
            and item.mapping_id in accepted_ids
            and item.refresh.status in {"fetched", "cached"}
            for item in outcomes
        )

    if mapping_count < MIN_REVIEWED_MAPPINGS:
        failures.append("at least five exact reviewed variant mappings are required")
    if accepted_count < MIN_REVIEWED_MAPPINGS:
        failures.append("at least five accepted refresh outcomes are required")

    for observation in catalog.observations:
        limit = (
            PRICE_AVAILABILITY_MAX_AGE
            if observation.field_name in {"price_paise", "availability"}
            else OTHER_FACT_MAX_AGE
        )
        if _age(observation.verified_at, checked) > limit:
            failures.append("catalog facts exceed the approved freshness window")
            break

    return Prd02ReleaseReport(
        "passed" if not failures else "failed",
        product_count,
        sunscreen_count,
        moisturiser_count,
        mapping_count,
        accepted_count,
        {"price_availability": 7, "other_facts": 30},
        tuple(dict.fromkeys(failures)),
    )


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ValueError("Supply one existing catalog database path.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(prog="python -m scripts.verify_prd02_release", description=__doc__)
    parser.add_argument("database", type=Path)
    try:
        report = asdict(verify_prd02_release(parser.parse_args(argv).database))
    except (OSError, ValueError) as error:
        report = {"status": "failed", "failures": (str(error),)}
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
