"""Inspectable, session-only PRD 03 screening panel for a catalog detail."""

from collections.abc import MutableMapping
from urllib.parse import urlsplit

import streamlit as st

from schemas.catalog import CatalogEnvelope
from services.ingredient_rules import RULE_MANIFEST_PATH, RuleManifestStore
from services.ingredient_screening import evaluate_ingredients, screening_input_from_catalog
from services.personal_exclusions import evaluate_personal_exclusions

SCREENING_SESSION_KEYS = ("screening_avoid_list", "ingredient_rule_manifest_store")


def clear_screening_state(state: MutableMapping[str, object]) -> None:
    """Clear only session-only inputs and the session's public manifest cache."""
    for key in SCREENING_SESSION_KEYS:
        state.pop(key, None)


def _safe_https_reference(reference: str) -> str | None:
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


def _store() -> RuleManifestStore:
    store = st.session_state.get("ingredient_rule_manifest_store")
    if isinstance(store, RuleManifestStore):
        return store
    created = RuleManifestStore()
    st.session_state["ingredient_rule_manifest_store"] = created
    return created


def _avoid_list(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.splitlines() if item.strip())


def render_ingredient_screening(catalog: CatalogEnvelope, product_id: str) -> None:
    """Render public rule findings and never persist personal exclusions."""
    st.markdown("### Ingredient screening")
    st.caption(
        "This is a limited rule set. It does not establish safety, allergy suitability, "
        "or complete regulatory compliance."
    )
    avoidance_text = st.text_area(
        "Session-only ingredient exclusions",
        placeholder="Enter one exact ingredient per line",
        key="screening_avoid_list",
    )
    outcome = _store().refresh(RULE_MANIFEST_PATH)
    if outcome.rules is None:
        st.warning(outcome.message)
        return
    if outcome.status == "retained_last_valid":
        st.warning(outcome.message)

    screening = screening_input_from_catalog(catalog, product_id)
    regulatory = evaluate_ingredients(screening, outcome.rules)
    personal = evaluate_personal_exclusions(
        declaration=screening.declaration,
        exclusions=_avoid_list(avoidance_text),
        rules=outcome.rules,
    )
    eligibility = "excluded" if personal.excluded else regulatory.eligibility
    st.text(f"Screening status: {eligibility}")
    st.caption(f"Rule set: {outcome.rules.rule_set_id}, version {outcome.rules.version}")

    if regulatory.findings:
        st.caption("Regulatory findings")
        for regulatory_finding in regulatory.findings:
            st.text(f"{regulatory_finding.matched_declaration}: {regulatory_finding.status}")
            details = [
                f"Rule: {regulatory_finding.canonical_ingredient}",
                f"Section: {regulatory_finding.source_section}",
                f"Checked: {regulatory_finding.checked_on.isoformat()}",
            ]
            if regulatory_finding.checked_conditions:
                details.append(
                    f"Conditions checked: {', '.join(regulatory_finding.checked_conditions)}"
                )
            if regulatory_finding.failed_conditions:
                details.append(
                    f"Conditions failed: {', '.join(regulatory_finding.failed_conditions)}"
                )
            if regulatory_finding.missing_conditions:
                details.append(
                    f"Conditions unresolved: {', '.join(regulatory_finding.missing_conditions)}"
                )
            st.caption(" · ".join(details))
            reference = _safe_https_reference(regulatory_finding.source_reference)
            if reference is not None:
                st.link_button(
                    "Open rule source",
                    reference,
                    key=f"rule_source_{regulatory_finding.rule_id}",
                    icon=":material/open_in_new:",
                )
    elif regulatory.eligibility == "eligible_within_checks":
        st.info("No matching issue was found within the limited rule set.")

    if personal.findings:
        st.caption("Personal exclusions")
        for personal_finding in personal.findings:
            if personal_finding.status == "matched":
                st.warning(
                    f"Personal exclusion match: {', '.join(personal_finding.matched_declarations)}"
                )
            else:
                st.info(
                    f"Clarify '{personal_finding.requested_term}' as an exact ingredient; "
                    "no exclusion was applied."
                )

    if regulatory.eligibility == "requires_verification":
        st.warning("Ingredient evidence or a required rule condition needs verification.")
