"""In-memory search handoff; never persist or log active filters/results."""

from typing import Literal

from pydantic import Field

from schemas.catalog import CatalogEnvelope, NonNegativeInt
from schemas.common import Category, Contract, Identifier


class CatalogFilters(Contract):
    category: Category = Field(repr=False)
    country: Literal["India"] = Field(repr=False)
    currency: Literal["INR"] = Field(repr=False)
    budget_paise: NonNegativeInt = Field(repr=False)


class CatalogSearchResult(Contract):
    filters: CatalogFilters = Field(repr=False)
    catalog: CatalogEnvelope = Field(repr=False)

    @property
    def status(self) -> Literal["matches", "empty"]:
        return "matches" if self.catalog.products else "empty"


class CatalogDetailQuery(Contract):
    product_id: Identifier = Field(repr=False)
