"""Safe, evidence-first catalog result presentation for US-018."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Final
from urllib.parse import urlsplit

import streamlit as st

from schemas.catalog import CatalogEnvelope, FactName, FactObservation, Rating
from schemas.requirements import UserRequirements
from schemas.search import CatalogSearchResult
from services.catalog_search import CatalogSearchService, CatalogUnavailableError

DETAIL_FIELDS: Final[tuple[FactName, ...]] = (
    "brand",
    "name",
    "category",
    "variant",
    "pack_size",
    "availability",
    "price_paise",
    "skin_type_claims",
    "rating",
    "review_count",
    "ingredient_declaration",
    "ingredient_completeness",
    "sponsorship",
)
FIELD_LABELS: Final[dict[FactName, str]] = {
    "brand": "Brand",
    "name": "Product name",
    "category": "Category",
    "variant": "Variant",
    "pack_size": "Pack size",
    "availability": "Availability",
    "price_paise": "India price",
    "skin_type_claims": "Declared skin-type claims",
    "rating": "Source rating",
    "review_count": "Source review count",
    "ingredient_declaration": "Declared ingredients",
    "ingredient_completeness": "Ingredient declaration completeness",
    "sponsorship": "Sponsorship",
}


def safe_https_reference(reference: str) -> str | None:
    """Return a browser-safe HTTPS reference or no executable link."""
    try:
        parsed = urlsplit(reference)
        if (
            parsed.scheme == "https"
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not any(character.isspace() for character in reference)
            and "\\" not in reference
        ):
            _ = parsed.port
            return reference
    except ValueError:
        pass
    return None


def _timestamp(value: datetime) -> str:
    normalized = value.astimezone(UTC).isoformat(timespec="seconds")
    return normalized.replace("+00:00", "Z")


def _decimal(value: Decimal) -> str:
    return format(value, "f")


def _fact_text(field: FactName, value: object) -> str:
    if value is None or value == ():
        return "Unknown"
    if field == "price_paise" and isinstance(value, int):
        return f"₹{value // 100:,}.{value % 100:02d}"
    if isinstance(value, Rating):
        return (
            f"{_decimal(value.score)} / {_decimal(value.scale_max)} "
            f"(scale {_decimal(value.scale_min)}–{_decimal(value.scale_max)})"
        )
    if isinstance(value, tuple):
        return ", ".join(str(item) for item in value) or "Unknown"
    if field == "sponsorship":
        return "Unknown (evidence-backed)" if value == "unknown" else str(value).title()
    return str(value)


def _selected_evidence(
    catalog: CatalogEnvelope, product_id: str, field: FactName
) -> tuple[FactObservation, ...]:
    resolution = next(
        (
            item
            for item in catalog.resolutions
            if item.product_id == product_id
            and item.field_name == field
            and item.status == "selected"
        ),
        None,
    )
    if resolution is None:
        return ()
    evidence = {item.evidence_id: item for item in catalog.observations}
    return tuple(evidence[evidence_id] for evidence_id in resolution.evidence_ids)


def _render_evidence(catalog: CatalogEnvelope, observations: tuple[FactObservation, ...]) -> None:
    sources = {source.source_id: source for source in catalog.sources}
    for observation in observations:
        source = sources[observation.source_id]
        st.caption("Evidence source")
        st.text(source.attribution)
        st.caption("Verified at")
        st.text(_timestamp(observation.verified_at))
        reference = safe_https_reference(observation.source_reference)
        if reference is not None:
            st.link_button(
                "Open original HTTPS source",
                reference,
                icon=":material/open_in_new:",
                key=f"source_{observation.evidence_id}",
            )
        else:
            st.caption("Document reference")
            st.text(observation.source_reference)


def _render_fact(catalog: CatalogEnvelope, product_id: str, field: FactName) -> None:
    value = catalog.resolved_value(product_id, field)
    st.caption(FIELD_LABELS[field])
    st.text(_fact_text(field, value))
    evidence = _selected_evidence(catalog, product_id, field)
    if value is not None:
        _render_evidence(catalog, evidence)
    elif evidence:
        st.caption("Evidence records this fact as unknown")
        _render_evidence(catalog, evidence)


def execute_search(service: CatalogSearchService, request: UserRequirements) -> None:
    """Replace stale UI state with this search result or sanitized recovery guidance."""
    for key in ("active_search_result", "catalog_search_error", "selected_product_id"):
        st.session_state.pop(key, None)
    try:
        st.session_state["active_search_result"] = service.search(request)
    except CatalogUnavailableError as error:
        st.session_state["catalog_search_error"] = str(error)


def _select_product(product_id: str) -> None:
    st.session_state["selected_product_id"] = product_id


def _render_empty(result: CatalogSearchResult) -> None:
    filters = result.filters
    budget = f"₹{filters.budget_paise // 100:,}.{filters.budget_paise % 100:02d}"
    st.info(
        f"No {filters.category} products matched India at or below {budget}. "
        "Change the filters and search again; no fallback products were invented."
    )


def _render_cards(result: CatalogSearchResult) -> None:
    st.subheader("Matching products")
    st.caption("Discovery results are ordered by product name, then stable product ID.")
    for product in result.catalog.products:
        with st.container(border=True, key=f"result_{product.product_id}"):
            st.caption("Product name")
            st.text(product.name)
            st.caption("India price")
            st.text(
                _fact_text(
                    "price_paise", result.catalog.resolved_value(product.product_id, "price_paise")
                )
            )
            st.caption("Pack size")
            st.text(
                _fact_text(
                    "pack_size", result.catalog.resolved_value(product.product_id, "pack_size")
                )
            )
            st.button(
                "View details",
                key=f"detail_{product.product_id}",
                icon=":material/fact_check:",
                on_click=_select_product,
                args=(product.product_id,),
            )


def _render_detail(service: CatalogSearchService, product_id: str) -> None:
    try:
        catalog = service.detail(product_id)
    except CatalogUnavailableError as error:
        st.session_state.pop("active_search_result", None)
        st.session_state.pop("selected_product_id", None)
        st.session_state["catalog_search_error"] = str(error)
        st.error(str(error))
        return
    if catalog is None:
        st.warning("This product is no longer available in the catalog. Search again.")
        st.session_state.pop("selected_product_id", None)
        return

    product = catalog.products[0]
    st.subheader("Product details")
    st.info(
        "Declared skin-type claims are source statements, not a safety or suitability finding. "
        "This discovery view does not calculate a suitability score or recommendation."
    )
    for field in DETAIL_FIELDS:
        with st.container(border=True, key=f"fact_{product.product_id}_{field}"):
            _render_fact(catalog, product.product_id, field)


def render_catalog_results(service: CatalogSearchService) -> None:
    """Render one transient search result and its optional evidence detail."""
    error = st.session_state.get("catalog_search_error")
    if isinstance(error, str):
        st.error(error)
        return
    result = st.session_state.get("active_search_result")
    if not isinstance(result, CatalogSearchResult):
        return
    if result.status == "empty":
        _render_empty(result)
        return
    _render_cards(result)
    selected = st.session_state.get("selected_product_id")
    if isinstance(selected, str):
        _render_detail(service, selected)
