"""Local development entry point; catalog behavior arrives in PRD 01."""

import streamlit as st
from pydantic import ValidationError

from schemas.settings import Settings


def main() -> None:
    st.set_page_config(page_title="AI Cosmetic Product Advisor", page_icon="🧴")
    st.title("AI Cosmetic Product Advisor")
    st.caption("Local development preview")

    try:
        settings = Settings()
    except ValidationError:
        st.error(
            "Configuration is invalid. Check the documented ADVISOR_ settings in .env.example. "
            "Configuration values have been omitted from this message."
        )
        st.stop()

    st.info("Catalog search is planned for PRD 01. No catalog has been loaded by this preview.")
    st.markdown("**Planned scope:** sunscreen and moisturiser available in India, priced in INR.")

    with st.expander("Development status"):
        st.write("Configuration validated. No source or model connections are started.")
        st.write(f"Catalog directory: {settings.data_dir}")
        st.write("Hosted inference: disabled")
        st.write("Use the repository README for setup and the PRD index for release scope.")


if __name__ == "__main__":
    main()
