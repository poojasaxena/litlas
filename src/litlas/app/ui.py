"""Shared Streamlit styling for Litlas."""

import streamlit as st


def apply_page_style():
    """Apply consistent styling across all Litlas pages."""

    st.markdown(
        """
<style>
    /* Preserve sidebar functionality without a visible header */
    [data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Compact page layout */
    .block-container {
        padding-top: 0.7rem !important;
        padding-bottom: 1rem !important;
        max-width: 1550px;
    }

    /* Compact page titles */
    h1 {
        margin-top: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0.2rem !important;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
</style>
""",
        unsafe_allow_html=True,
    )
