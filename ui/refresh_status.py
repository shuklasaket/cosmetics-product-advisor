"""Explicit refresh controls and payload-free operator outcomes."""

from datetime import UTC, datetime
from pathlib import Path
from typing import get_args

import streamlit as st

from repositories.catalog import CatalogRepository, CatalogStorageError
from repositories.refresh import RefreshRepository
from schemas.catalog import FactName
from schemas.refresh import RefreshResult, RetrievedField
from services.catalog_policy import evaluate_catalog
from services.manual_refresh import (
    ManualRefreshResult,
    ManualRefreshService,
    RefreshUnavailableError,
)


def session_refresh_service(path: Path) -> ManualRefreshService:
    service = st.session_state.get("manual_refresh_service")
    if not isinstance(service, ManualRefreshService) or service.path != path:
        service = ManualRefreshService(path)
        st.session_state["manual_refresh_service"] = service
        st.session_state["manual_refresh_results"] = {}
    return service


def render_outcome(result: RefreshResult, fields: tuple[RetrievedField, ...] = ()) -> None:
    st.text(f"Last refresh: {result.status}")
    st.text(
        f"Source: {result.source_id} | Cache: {result.cache_state} | Attempts: {result.attempts}"
    )
    st.text(f"Completed at: {result.completed_at.isoformat()}")
    if result.retrieved_at is not None:
        st.text(f"Retrieved at: {result.retrieved_at.isoformat()}")
    else:
        st.caption("No new retrieval date. Original evidence dates are retained.")
    if result.error_code:
        st.warning(
            f"{result.error_code}: local evidence remains available with its original dates. "
            "Check the approved source and mapping; retry later for temporary source failures."
        )
    if fields:
        st.caption("Retrieved field status")
        for field in fields:
            st.text(f"{field.field_name}: {field.status}")


def render_refresh_controls(service: ManualRefreshService, product_id: str) -> None:
    unavailable = None
    try:
        service.target(product_id)
    except RefreshUnavailableError as error:
        unavailable = str(error)
    st.caption("Manual source refresh — Open Beauty Facts")
    st.caption("Only this mapped product is requested. Up to 3 attempts, 10 seconds per attempt.")
    if unavailable:
        st.info(unavailable)
    if st.button("Refresh product", key=f"refresh_{product_id}", disabled=unavailable is not None):
        try:
            with st.spinner("Refreshing approved source; waiting for a bounded result…"):
                result = service.refresh(product_id)
            st.session_state["manual_refresh_results"][product_id] = result
            st.rerun()
        except RefreshUnavailableError as error:
            st.warning(str(error))
    render_refresh_history(service, product_id)


def render_refresh_history(service: ManualRefreshService, product_id: str) -> None:
    recent = st.session_state.get("manual_refresh_results", {}).get(product_id)
    try:
        outcomes = RefreshRepository(service.path).outcomes(product_id)
    except ValueError:
        st.warning("Refresh history unavailable. Check migration or restore a verified backup.")
        outcomes = ()
    latest = max(outcomes, key=lambda item: item.refresh.completed_at) if outcomes else None
    if isinstance(recent, ManualRefreshResult) and (
        latest is None or recent.refresh.completed_at >= latest.refresh.completed_at
    ):
        render_outcome(recent.refresh, recent.fields)
        if recent.commit.status in {"committed", "unchanged"}:
            st.text(
                f"Storage: {recent.commit.status}; "
                f"new evidence records: {recent.commit.evidence_added}"
            )
        else:
            outcome_note = (
                "Candidate facts and mapping were not saved; the payload-free outcome is recorded. "
                if recent.commit.status == "review_required"
                else "This attempt was not saved. "
            )
            st.warning(
                f"Storage: {recent.commit.status} ({recent.commit.reason_code}). "
                f"{outcome_note}Review the mapping or repair storage before retrying."
            )
    elif latest:
        render_outcome(latest.refresh, latest.fields)
    else:
        st.caption("No recorded refresh outcome.")
    st.caption(
        "Retrieved evidence is unverified until reviewed. Refresh does not select facts, "
        "clear conflicts, or establish product suitability. "
        "Unsaved attempts last only this session."
    )


def render_operator_status(service: ManualRefreshService) -> None:
    """Read-only catalog-wide attention view, independent of private search criteria."""
    if not st.toggle("Show operator status", key="show_operator_status"):
        return
    with st.container(border=True, key="operator_status"):
        st.subheader("Operator status")
        st.caption("Public catalog evidence only. No source requests run when opening this view.")
        try:
            catalog = CatalogRepository(service.path).read()
        except CatalogStorageError:
            st.warning(
                "Catalog unavailable. Import approved evidence or restore a verified backup."
            )
            return
        policy = evaluate_catalog(catalog, now=datetime.now(UTC))
        if not catalog.products:
            st.info("No catalog products. Import approved evidence first.")
        for product in catalog.products:
            with st.container(border=True):
                st.text(f"Product ID: {product.product_id}")
                facts = [fact for fact in policy.facts if fact.product_id == product.product_id]
                st.text(f"Fresh facts: {sum(f.freshness == 'fresh' for f in facts)}")
                st.text(f"Stale facts: {sum(f.freshness == 'stale' for f in facts)}")
                st.text(
                    f"Conflicting facts: {sum(bool(f.conflicting_evidence_ids) for f in facts)}"
                )
                unresolved = sum(
                    item.status != "selected"
                    for item in catalog.resolutions
                    if item.product_id == product.product_id
                )
                st.text(f"Unresolved recorded facts: {unresolved}")
                unknown = len(get_args(FactName)) - len(facts)
                unknown += sum(f.freshness == "unknown" for f in facts)
                st.text(f"Unknown or absent facts: {unknown}")
                render_refresh_history(service, product.product_id)
                try:
                    service.target(product.product_id)
                except RefreshUnavailableError as error:
                    st.info(str(error))
                st.info(
                    "Review stale, missing, conflicting, or unverified evidence against approved "
                    "sources. Open product details to refresh an approved mapping. For mapping "
                    "changes, use the operator review process outside this app."
                )
