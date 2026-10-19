"""Validated, session-only search form for US-017."""

from collections.abc import MutableMapping
from typing import Final

import streamlit as st
from pydantic import ValidationError

from schemas.requirements import Preferences, UserRequirements

CATEGORY_LABELS: Final = {"Sunscreen": "sunscreen", "Moisturiser": "moisturiser"}
SKIN_TYPE_LABELS: Final = {
    "Oily": "oily",
    "Dry": "dry",
    "Combination": "combination",
    "Normal": "normal",
    "Sensitive": "sensitive",
}
SEARCH_WIDGET_DEFAULTS: Final = {
    "search_category": "Sunscreen",
    "search_skin_type": "Oily",
    "search_country": "India",
    "search_currency": "INR",
    "search_budget": "",
    "search_exclusions": "",
    "search_texture": "",
    "search_finish": "",
}
SEARCH_TRANSIENT_KEYS: Final = (
    "active_search_request",
    "active_search_result",
    "search_validation_messages",
    "search_dispatch_count",
)


def clear_search_state(state: MutableMapping[str, object]) -> None:
    """Remove only state owned by the search form."""
    state.update(SEARCH_WIDGET_DEFAULTS)
    for key in SEARCH_TRANSIENT_KEYS:
        state.pop(key, None)


def _optional_text(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None


def build_search_request(
    *,
    category_label: str,
    skin_type_label: str,
    budget: str,
    exclusions: str,
    texture: str,
    finish: str,
) -> UserRequirements:
    """Validate widget values at the UI-to-domain boundary."""
    texture_value = _optional_text(texture)
    finish_value = _optional_text(finish)
    preferences = None
    if texture_value is not None or finish_value is not None:
        preferences = Preferences(texture=texture_value, finish=finish_value)

    return UserRequirements.model_validate(
        {
            "category": CATEGORY_LABELS.get(category_label, category_label),
            "skin_type": SKIN_TYPE_LABELS.get(skin_type_label, skin_type_label),
            "country": "India",
            "currency": "INR",
            "budget_inr": budget,
            "exclusions": tuple(line.strip() for line in exclusions.splitlines() if line.strip()),
            "preferences": preferences,
        }
    )


def _accept_validated_request(request: UserRequirements) -> None:
    """Controlled handoff point for the result UI introduced by US-018."""
    st.session_state["active_search_request"] = request
    st.session_state.pop("active_search_result", None)
    st.session_state["search_dispatch_count"] = st.session_state.get("search_dispatch_count", 0) + 1


def render_search_form() -> None:
    """Render and process the catalog search inputs."""
    st.subheader("Find products")
    st.caption(
        "Ingredient exclusions and preferences stay only in this browser session. "
        "They are collected for later screening and do not filter results yet."
    )

    with st.form("catalog_search"):
        category_label = st.segmented_control(
            "Category",
            list(CATEGORY_LABELS),
            default="Sunscreen",
            key="search_category",
        )
        skin_type_label = st.selectbox(
            "Skin type",
            list(SKIN_TYPE_LABELS),
            key="search_skin_type",
        )
        market, money = st.columns(2)
        with market:
            st.text_input("Country", value="India", disabled=True, key="search_country")
        with money:
            st.text_input("Currency", value="INR", disabled=True, key="search_currency")
        budget = st.text_input(
            "Maximum budget (INR)",
            placeholder="For example, 800.00",
            key="search_budget",
        )
        exclusions = st.text_area(
            "Ingredient exclusions (optional)",
            placeholder="Enter one ingredient per line",
            key="search_exclusions",
        )
        texture = st.text_input(
            "Preferred texture (optional)",
            placeholder="For example, gel",
            key="search_texture",
        )
        finish = st.text_input(
            "Preferred finish (optional)",
            placeholder="For example, matte",
            key="search_finish",
        )
        submitted = st.form_submit_button("Validate search", icon=":material/search:")

    st.button(
        "Clear",
        key="clear_search",
        icon=":material/clear_all:",
        on_click=clear_search_state,
        args=(st.session_state,),
    )

    if submitted:
        st.session_state.pop("active_search_request", None)
        st.session_state.pop("active_search_result", None)
        st.session_state.pop("search_validation_messages", None)
        try:
            request = build_search_request(
                category_label=category_label or "",
                skin_type_label=skin_type_label,
                budget=budget,
                exclusions=exclusions,
                texture=texture,
                finish=finish,
            )
        except ValidationError as error:
            messages = UserRequirements.validation_messages(error)
            st.session_state["search_validation_messages"] = messages
        else:
            _accept_validated_request(request)

    for message in st.session_state.get("search_validation_messages", ()):
        st.error(message)
    if "active_search_request" in st.session_state:
        st.success("Search requirements validated. Catalog results are added in the next story.")
