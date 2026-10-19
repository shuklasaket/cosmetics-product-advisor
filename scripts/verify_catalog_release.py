"""Verify the loaded PRD 01 catalog release; stdout is a sanitized JSON report."""

import argparse
import json
import platform
import sqlite3
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NoReturn

import streamlit

from repositories.catalog import CatalogRepository, CatalogStorageError
from schemas.catalog import CatalogEnvelope, FactName, FactObservation
from schemas.requirements import UserRequirements
from services.catalog_search import CatalogSearchService, CatalogUnavailableError

PROVENANCE_PRODUCT_ID = "minimalist-light-fluid-spf50-50ml"


class ReleaseVerificationError(Exception):
    """A fixed, non-sensitive release-check failure."""


@dataclass(frozen=True)
class ReleaseReport:
    status: str
    product_count: int
    sunscreen_ids: tuple[str, ...]
    moisturiser_ids: tuple[str, ...]
    provenance_product_id: str
    price_source_id: str
    ingredients_source_id: str
    price_verified_at: str
    ingredients_verified_at: str
    python_version: str
    streamlit_version: str
    sqlite_version: str


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ReleaseVerificationError("Supply one existing catalog database path.") from None


def _selected_observation(
    catalog: CatalogEnvelope, product_id: str, field_name: FactName
) -> FactObservation:
    resolution = next(
        (
            item
            for item in catalog.resolutions
            if item.product_id == product_id
            and item.field_name == field_name
            and item.status == "selected"
        ),
        None,
    )
    if resolution is None or len(resolution.evidence_ids) != 1:
        raise ReleaseVerificationError("Required selected provenance is unavailable.")
    evidence_id = resolution.evidence_ids[0]
    observation = next(
        (item for item in catalog.observations if item.evidence_id == evidence_id), None
    )
    if observation is None:
        raise ReleaseVerificationError("Required selected provenance is unavailable.")
    return observation


def _search_ids(
    service: CatalogSearchService, *, category: str, budget_inr: str
) -> tuple[str, ...]:
    result = service.search(
        UserRequirements.model_validate(
            {
                "category": category,
                "skin_type": "normal",
                "country": "India",
                "currency": "INR",
                "budget_inr": budget_inr,
            }
        )
    )
    return tuple(product.product_id for product in result.catalog.products)


def verify_catalog_release(database: Path) -> ReleaseReport:
    """Verify the already-loaded genuine seed without changing the database."""
    try:
        repository = CatalogRepository(database)
        catalog = repository.read()
        service = CatalogSearchService(repository)
        sunscreen_ids = _search_ids(service, category="sunscreen", budget_inr="800")
        moisturiser_ids = _search_ids(service, category="moisturiser", budget_inr="600")
    except (CatalogStorageError, CatalogUnavailableError):
        raise ReleaseVerificationError(
            "Catalog verification failed. Initialize, import the reviewed seed, "
            "or restore a valid backup."
        ) from None

    if len(catalog.products) != 10 or len(sunscreen_ids) != 5 or len(moisturiser_ids) != 5:
        raise ReleaseVerificationError(
            "Catalog does not match the reviewed ten-product release seed."
        )

    price = _selected_observation(catalog, PROVENANCE_PRODUCT_ID, "price_paise")
    ingredients = _selected_observation(catalog, PROVENANCE_PRODUCT_ID, "ingredient_declaration")
    if not price.source_id.startswith("retailer:") or not ingredients.source_id.startswith(
        "maker:"
    ):
        raise ReleaseVerificationError("Required retailer/manufacturer provenance is unavailable.")
    if price.source_id == ingredients.source_id:
        raise ReleaseVerificationError("Price and ingredient provenance must remain separate.")

    return ReleaseReport(
        status="passed",
        product_count=len(catalog.products),
        sunscreen_ids=sunscreen_ids,
        moisturiser_ids=moisturiser_ids,
        provenance_product_id=PROVENANCE_PRODUCT_ID,
        price_source_id=price.source_id,
        ingredients_source_id=ingredients.source_id,
        price_verified_at=price.verified_at.isoformat(),
        ingredients_verified_at=ingredients.verified_at.isoformat(),
        python_version=platform.python_version(),
        streamlit_version=streamlit.__version__,
        sqlite_version=sqlite3.sqlite_version,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(prog="python -m scripts.verify_catalog_release", description=__doc__)
    parser.add_argument("database", type=Path, help="Existing initialized catalog database.")
    try:
        arguments = parser.parse_args(argv)
        report = asdict(verify_catalog_release(arguments.database))
    except (OSError, ValueError, ReleaseVerificationError) as error:
        report = {"status": "failed", "message": str(error)}
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
