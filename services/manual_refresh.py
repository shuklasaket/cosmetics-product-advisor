"""Manual, public-ID-only refresh orchestration for the local operator UI."""

from dataclasses import dataclass
from pathlib import Path
from re import fullmatch

from repositories.catalog import CatalogRepository, CatalogStorageError
from repositories.refresh import RefreshCommitReport, RefreshRepository
from repositories.source_registry import SourceRegistryRepository, SourceRegistryStorageError
from schemas.refresh import ApprovedSource, RefreshResult, ReviewedVariantMapping
from services.open_beauty_facts import OpenBeautyFactsClient


class RefreshUnavailableError(Exception):
    """Fixed recovery message; never includes storage or remote exception contents."""


@dataclass(frozen=True)
class RefreshTarget:
    source: ApprovedSource
    mapping: ReviewedVariantMapping


@dataclass(frozen=True)
class ManualRefreshResult:
    refresh: RefreshResult
    commit: RefreshCommitReport


class ManualRefreshService:
    """Recheck authorization on every action; retain only public adapter cache in memory."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._client: OpenBeautyFactsClient | None = None

    def target(self, product_id: str) -> RefreshTarget:
        try:
            catalog = CatalogRepository(self.path).read()
            registry = SourceRegistryRepository(self.path).read()
            mappings = RefreshRepository(self.path).mappings(product_id)
        except (CatalogStorageError, SourceRegistryStorageError, ValueError):
            raise RefreshUnavailableError(
                "Refresh unavailable: check the catalog migration, approved source registry, "
                "and reviewed mappings. Restore a verified backup if storage is invalid."
            ) from None
        product = next((p for p in catalog.products if p.product_id == product_id), None)
        source = next(
            (s for s in registry.sources if s.source_id == "open-beauty-facts" and s.enabled),
            None,
        )
        public_source = next(
            (s for s in catalog.sources if s.source_id == "open-beauty-facts" and s.enabled),
            None,
        )
        if (
            product is None
            or source is None
            or public_source is None
            or source.source_type != "dataset"
            or source.external_id_namespace != "open-beauty-facts-barcode"
            or len(source.endpoints) != 1
        ):
            raise RefreshUnavailableError(
                "Read-only catalog: configure and approve the Open Beauty Facts source first."
            )
        candidates = [m.mapping for m in mappings if m.mapping.source_id == source.source_id]
        if not candidates or len({m.external_id for m in candidates}) != 1:
            raise RefreshUnavailableError(
                "Read-only catalog: review one exact product/barcode mapping outside the app."
            )
        mapping = max(candidates, key=lambda m: m.reviewed_at)
        if fullmatch(r"[0-9]{8,14}", mapping.external_id) is None:
            raise RefreshUnavailableError(
                "Read-only catalog: review an 8–14 digit Open Beauty Facts barcode mapping."
            )
        if (product.brand, product.name, product.variant, product.pack_size) != (
            mapping.catalog_brand,
            mapping.catalog_name,
            mapping.catalog_variant,
            mapping.catalog_pack_size,
        ) or catalog.resolved_value(
            product_id, "ingredient_declaration"
        ) != mapping.source_ingredient_declaration:
            raise RefreshUnavailableError(
                "Read-only catalog: the product changed. Review its exact variant mapping again."
            )
        return RefreshTarget(source, mapping)

    def refresh(self, product_id: str) -> ManualRefreshResult:
        target = self.target(product_id)
        if self._client is None or self._client.source != target.source:
            self._client = OpenBeautyFactsClient(target.source)
        lookup = self._client.lookup(product_id=product_id, external_id=target.mapping.external_id)
        report = RefreshRepository(self.path).commit(
            lookup,
            target.mapping if lookup.refresh.status in {"fetched", "cached", "partial"} else None,
        )
        return ManualRefreshResult(lookup.refresh, report)
