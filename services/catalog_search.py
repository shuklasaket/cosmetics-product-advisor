"""Model-free catalog queries. Requests/results remain transient and uncached."""

from repositories.catalog import CatalogRepository, CatalogStorageError
from schemas.catalog import CatalogEnvelope
from schemas.requirements import UserRequirements
from schemas.search import CatalogDetailQuery, CatalogFilters, CatalogSearchResult


class CatalogUnavailableError(Exception):
    """Fixed public diagnostics shared by search and detail consumers."""


UNAVAILABLE = (
    "Catalog unavailable or invalid. Check the configured database file, "
    "run the documented migration if required, or restore a verified backup."
)


class CatalogSearchService:
    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    def search(self, requirements: UserRequirements) -> CatalogSearchResult:
        # Revalidate copied/constructed instances before dispatch, without logging errors.
        value = UserRequirements.model_validate(requirements.model_dump(warnings=False))
        filters = CatalogFilters(
            category=value.category,
            country=value.country,
            currency=value.currency,
            budget_paise=value.budget_paise,
        )
        try:
            return CatalogSearchResult(filters=filters, catalog=self.repository.search(filters))
        except CatalogStorageError:
            raise CatalogUnavailableError(UNAVAILABLE) from None

    def detail(self, product_id: str) -> CatalogEnvelope | None:
        """Exact ID lookup, independent of prior search. None means absent, not unavailable."""
        query = CatalogDetailQuery(product_id=product_id)
        try:
            catalog = self.repository.detail(query.product_id)
            return catalog if catalog.products else None
        except CatalogStorageError:
            raise CatalogUnavailableError(UNAVAILABLE) from None
