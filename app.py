"""Local Streamlit entry point for the cosmetic product advisor."""

import streamlit as st
from pydantic import ValidationError

from repositories.catalog import CatalogRepository
from schemas.settings import Settings
from services.catalog_search import CatalogSearchService
from ui.catalog_results import execute_search, render_catalog_results
from ui.search_form import render_search_form


def main() -> None:
    st.set_page_config(page_title="AI Cosmetic Product Advisor", page_icon="🧴")
    st.title("AI Cosmetic Product Advisor")
    st.caption("Private, local catalog search")

    try:
        settings = Settings()
    except ValidationError:
        st.error(
            "Configuration is invalid. Check the documented ADVISOR_ settings in .env.example. "
            "Configuration values have been omitted from this message."
        )
        st.stop()

    service = CatalogSearchService(CatalogRepository(settings.database_path))
    request = render_search_form()
    if request is not None:
        execute_search(service, request)
    render_catalog_results(service)

    with st.expander("Development status"):
        st.write("Configuration validated. No source or model connections are started.")
        st.write(f"Catalog directory: {settings.data_dir}")
        st.write("Hosted inference: disabled")
        st.write(
            "Catalog search and evidence detail display are enabled when valid data is loaded."
        )


if __name__ == "__main__":
    main()
