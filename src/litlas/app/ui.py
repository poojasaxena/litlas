"""Shared Streamlit styling for Litlas."""


import base64
from pathlib import Path
from html import escape
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

            /* Warm paper background for Litlas */
            .stApp {
                background-color: #FAF7F1 !important;
            }

            /* Vintage styling for Streamlit information messages */
            div[data-testid="stAlert"] {
                background-color: #F0E6D7 !important;
                border: 1px solid #D4C1A7 !important;
                border-radius: 8px !important;
            }

            /* Remove Streamlit's inner blue background */
            div[data-testid="stAlert"] > div,
            div[data-testid="stAlert"] [data-baseweb="notification"] {
                background-color: transparent !important;
                border-color: transparent !important;
            }

            /* Alert text and icons */
            div[data-testid="stAlert"] p,
            div[data-testid="stAlert"] svg {
                color: #58412F !important;
                fill: #58412F !important;
            }

            /* Distinct information icon in antique bronze */
            div[data-testid="stAlert"] [data-testid="stIconMaterial"] {
                color: #A47B43 !important;
                font-size: 25px !important;
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

            /* Vintage illustration */
            .litlas-page-illustration {
                position: absolute;
                top: -45px;
                left: 0;
                object-fit: contain;
                pointer-events: none;
                z-index: 2;
            }

            /* Shared header */
            .litlas-heading {
                min-height: 170px;
            }

            /* Literary title */
            .litlas-heading h1 {
                font-family: "Vivaldi", Georgia, serif;
                font-size: 5.5rem;
                font-weight: 400;
                letter-spacing: 0;
                line-height: 0.75;
                color: #58412F;
                margin: 0;
                padding: 0;
            }

            /* Stronger, longer ornamental line */
            .litlas-heading h1::after {
                content: "";
                display: block;
                width: 570px;
                margin-left: 10px;
                max-width: 100%;
                height: 2px;
                margin-top: 10px;
                background: #B29A7C;
            }

            /* Subtitle */
            .litlas-heading p {
                margin: 12px 0 0;
                padding-left: 10px;
                font-family: Georgia, serif;
                font-size: 0.95rem;
                font-style: italic;
                color: #81776E;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def litlas_info(message: str) -> None:
    """Display a vintage-styled informational message."""
    st.markdown(
        f"""
        <div style="
            display:flex;
            align-items:center;
            gap:14px;
            padding:18px 20px;
            background:#F0E6D7;
            border:1px solid #D4C1A7;
            border-radius:8px;
            color:#58412F;
            font-family:Georgia,serif;
            font-style:italic;
            font-size: 0.95rem;
            font-weight: 400;
            color: #81776E;
        ">
            <span style="
                display:inline-flex;
                align-items:center;
                justify-content:center;
                flex-shrink:0;
                width:25px;
                height:25px;
                border:2px solid #A47B43;
                border-radius:50%;
                color:#A47B43;
                font-size:17px;
                font-weight:bold;
                font-family:Georgia,serif;
                font-style:italic;
            ">i</span>
            <span>{escape(message)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
  

def load_illustration_path(name: str) -> Path | None:
    """Resolve a page illustration from the Vault."""
    config = load_config()
    value = config.get("illustrations", {}).get(name)

    if not value:
        return None

    path = Path(value).expanduser()
    return path if path.is_file() else None


def render_page_header(
    title: str,
    subtitle: str,
    illustration: str | None = None,
    illustration_size: int = 110,
    illustration_top: int = -45,
    illustration_left: int = 0,
    heading_gap: int = 5,
) -> None:
    """Render the shared vintage Litlas heading."""

    logo = load_logo_path()

    if logo:
        encoded = base64.b64encode(logo.read_bytes()).decode("ascii")

        st.markdown(
            f'<img class="litlas-logo" '
            f'src="data:image/png;base64,{encoded}" '
            f'alt="Personal signature">',
            unsafe_allow_html=True,
        )

    image_html = ""
    left_padding = 0

    if illustration:
        image_path = load_illustration_path(illustration)

        if image_path:
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")

            image_html = (
                f'<img class="litlas-page-illustration" '
                f'src="data:image/png;base64,{encoded}" '
                f'style="width:{illustration_size}px;'
                f'height:{illustration_size}px;'
                f'top:{illustration_top}px;'
                f'left:{illustration_left}px;" '
                f'alt="">'
            )

            left_padding = illustration_left + illustration_size + heading_gap

    st.markdown(
        f"""
        {image_html}
        <div class="litlas-heading"
             style="padding-left:{left_padding}px;">
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
