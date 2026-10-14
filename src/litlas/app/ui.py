"""Shared Streamlit styling for Litlas."""


import base64
from pathlib import Path

import streamlit as st

from litlas.processing.core import load_config

def load_logo_path() -> Path | None:
    """Return the original Vault logo path, if available."""
    config = load_config()
    path = Path(config["branding"]["logo"]).expanduser()
    return path if path.is_file() else None


def apply_page_style():
    """Apply consistent styling across all Litlas pages."""

    st.markdown(
        """
        <style>
            [data-testid="stHeader"] {
                background: transparent !important;
                box-shadow: none !important;
            }

            .block-container {
                padding-top: 0.7rem !important;
                padding-bottom: 1rem !important;
                max-width: 1550px;
            }

            h1 {
                margin-top: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0.2rem !important;
            }

            #MainMenu, footer {
                visibility: hidden;
            }

            /* Anchor the logo to the page content */
            [data-testid="stMainBlockContainer"] {
                position: relative;
            }

            .litlas-logo {
                position: absolute;
                top: 0;
                right: 0;
                width: 180px;
                height: 180px;
                object-fit: contain;
                pointer-events: none;
                z-index: 2;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    """Render the shared Litlas header."""

    logo = load_logo_path()

    if logo:
        encoded = base64.b64encode(logo.read_bytes()).decode("ascii")

        st.markdown(
            f'<img class="litlas-logo" '
            f'src="data:image/png;base64,{encoded}" '
            f'alt="Personal signature">',
            unsafe_allow_html=True,
        )

    st.title(title)
    st.caption(subtitle)

    # Reserve enough space to prevent the logo overlapping page content.
    st.markdown(
        '<div style="height: 75px;"></div>',
        unsafe_allow_html=True,
    )
