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

            /* Sidebar: muted parchment, distinct from the main page */
            [data-testid="stSidebar"],
            [data-testid="stSidebar"] > div {
                background-color: #EDE6DA !important;
            }

            /* Subtle separation between navigation and content */
            [data-testid="stSidebar"] {
                border-right: 1px solid #D4C1A7 !important;
            }

            /* Confirmation beneath the Library Editor */
            [data-testid="stSidebar"] .st-key-litlas_saved_confirmation {
                background-color: #C7AE91 !important;
                border: 1px solid #A98A6D !important;
                border-radius: 7px !important;
                padding: 12px 16px !important;
            }

            [data-testid="stSidebar"] .st-key-litlas_saved_confirmation p {
                color: #493626 !important;
                font-family: Georgia, serif !important;
                font-size: 14px !important;
                margin: 0 !important;
            }
            /* Keep the Library Editor's form lighter */
            [data-testid="stSidebar"] [data-testid="stForm"] {
                background-color: #F5EFE4 !important;
                border: 1px solid #D4C1A7 !important;
                border-radius: 7px !important;
            }

            /* Library Editor form — subtle parchment panel */
            [data-testid="stSidebar"] [data-testid="stForm"] {
                background-color: #F5EFE4 !important;
                border: 1px solid #D4C1A7 !important;
                border-radius: 7px !important;
            }

            /* Sidebar labels and headings */
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] label {
                color: #58412F !important;
            }

            /* Sidebar dividers */
            [data-testid="stSidebar"] hr {
                border-color: #D4C1A7 !important;
            }

            /* Litlas Library Editor — bronze Save button */
            [data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button {
                background: #8B634B !important;
                border: 1px solid #8B634B !important;
                color: #FFF9F1 !important;
                border-radius: 6px !important;
                font-family: Georgia, serif !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                box-shadow: none !important;
            }

            [data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button:hover {
                background: #6E4B3A !important;
                border-color: #6E4B3A !important;
                color: #FFF9F1 !important;
            }

            [data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button:focus-visible {
                outline: 2px solid #A47B43 !important;
                outline-offset: 2px !important;
            }

            .litlas-logo {
                position: absolute;
                top: -30px;
                right: 0;
                width: 178px;
                height: 178px;
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
                min-height: 140px;
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

            /* Litlas header — fixed within Streamlit's scroll area */
            [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
                position: relative;
            }

            /* Allow the header's Streamlit wrapper to remain sticky */
            [data-testid="stLayoutWrapper"]:has(
                > .st-key-litlas_sticky_header
            ) {
                position: sticky !important;
                top: 30px !important;
                z-index: 100 !important;
                background: #FAF7F1 !important;
            }

            /* Cover the gap above the sticky header */
            [data-testid="stLayoutWrapper"]:has(
                > .st-key-litlas_sticky_header
            )::before {
                content: "";
                position: absolute;
                top: -45px;
                left: 0;
                right: 0;
                height: 45px;
                background: #FAF7F1;
                pointer-events: none;
            }
            /* Header content and its positioned illustrations */
            .st-key-litlas_sticky_header {
                position: relative !important;
                background: #FAF7F1 !important;
                min-height: 140px;
                padding-bottom: 15px !important;
            }
            /* Literary chapter navigation */

            /* Navigation links */
            .st-key-litlas_sticky_header
            a[data-testid="stPageLink-NavLink"] {
                background: transparent !important;
                border: none !important;
                border-radius: 0 !important;
                padding: 0 !important;
                color: #96785D !important;
            }

            /* Visible labels */
            .st-key-litlas_sticky_header
            a[data-testid="stPageLink-NavLink"] p {
                color: #96785D !important;
                font-family: Georgia, serif !important;
                font-size: 13px !important;
                font-weight: 400 !important;
            }

            /* Hover */
            .st-key-litlas_sticky_header
            a[data-testid="stPageLink-NavLink"]:hover,
            .st-key-litlas_sticky_header
            a[data-testid="stPageLink-NavLink"]:hover p {
                color: #58412F !important;
                background: transparent !important;
            }

            /* Active chapter */
            .st-key-litlas_sticky_header
            a[data-testid="stPageLink-NavLink"][aria-current="page"],
            .st-key-litlas_sticky_header
            a[data-testid="stPageLink-NavLink"][aria-current="page"] p {
                color: #58412F !important;
                background: transparent !important;
                font-weight: 600 !important;
                text-decoration: underline !important;
                text-underline-offset: 4px;
            }
            /* Compact chapter links */
            .st-key-litlas_sticky_header
            a[data-testid="stPageLink-NavLink"] {
                width: auto !important;
                min-height: 0 !important;
                padding: 0 !important;
            }

            /* Ornamental separators */
            .st-key-litlas_sticky_header .litlas-chapter-separator {
                color: #B29A7C !important;
                font-family: Georgia, serif;
                font-size: 15px;
            }

            /* Remove default paragraph margins inside chapter navigation */
            .st-key-litlas_sticky_header
            [data-testid="stPageLink"] p,
            .st-key-litlas_sticky_header .litlas-chapter-separator {
                margin: 0 !important;
            }
            /* Current chapter */
            .st-key-litlas_sticky_header
            [data-testid="stPageLink"] a[aria-disabled="true"],
            .st-key-litlas_sticky_header
            [data-testid="stPageLink"] a[aria-disabled="true"] p {
                color: #58412F !important;
                font-weight: 700 !important;
                text-decoration: underline !important;
                text-underline-offset: 4px;
                opacity: 1 !important;
                background: transparent !important;
            }
            /* Hide Streamlit's sidebar and its expand/collapse controls */
            [data-testid="stSidebar"],
            [data-testid="stSidebarCollapsedControl"],
            [data-testid="stSidebarCollapseButton"] {
                display: none !important;
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


def render_chapter_navigation(active_page: str) -> None:
    """Render the centred literary chapter navigation."""

    pages = [
        ("Literary Atlas", "main.py", "/"),
        ("Reading Density", "pages/1_Reading_Density.py", "Reading_Density"),
        ("Reading Statistics", "pages/2_Reading_Statistics.py", "Reading_Statistics"),
        ("Library Management", "pages/3_Library_Management.py", "Library_Management"),
    ]

    active_route = next(
        route for label, _, route in pages if label == active_page
    )

    # Highlight the active page using its navigation URL.
    st.markdown(
        f"""
        <style>
        .st-key-litlas_sticky_header
        a[data-testid="stPageLink-NavLink"][href="{active_route}"],
        .st-key-litlas_sticky_header
        a[data-testid="stPageLink-NavLink"][href="{active_route}"] p {{
            color: #58412F !important;
            font-weight: 700 !important;
            text-decoration: underline !important;
            text-underline-offset: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(
        horizontal=True,
        horizontal_alignment="center",
        gap="small",
    ):
        for index, (label, path, _) in enumerate(pages):
            if index:
                st.markdown(
                    '<span class="litlas-chapter-separator">❦</span>',
                    unsafe_allow_html=True,
                )

            st.page_link(path, label=label)

def render_chapter_navigation_deprecated() -> None:
    """Render Litlas chapter navigation within the shared header."""

    pages = [
        ("Literary Atlas", "main.py"),
        ("Reading Density", "pages/1_Reading_Density.py"),
        ("Reading Statistics", "pages/2_Reading_Statistics.py"),
        ("Library Management", "pages/3_Library_Management.py"),
    ]

    columns = st.columns(
        [1.5, 0.15, 1.6, 0.15, 1.8, 0.15, 2.0],
        gap="small",
        vertical_alignment="center",
    )

    for index, (label, path) in enumerate(pages):
        with columns[index * 2]:
            st.page_link(path, label=label, use_container_width=True)

        if index < len(pages) - 1:
            with columns[index * 2 + 1]:
                st.markdown("❦")

def render_page_header(
    title: str,
    subtitle: str,
    illustration: str | None = None,
    illustration_size: int = 110,
    illustration_top: int = -45,
    illustration_left: int = 0,
    heading_gap: int = 5,
) -> None:
    """Render the shared sticky vintage Litlas heading."""

    logo_html = ""
    logo = load_logo_path()

    if logo:
        encoded = base64.b64encode(
            logo.read_bytes()
        ).decode("ascii")

        logo_html = (
            f'<img class="litlas-logo" '
            f'src="data:image/png;base64,{encoded}" '
            f'alt="Personal signature">'
        )

    image_html = ""
    left_padding = 0

    if illustration:
        image_path = load_illustration_path(illustration)

        if image_path:
            encoded = base64.b64encode(
                image_path.read_bytes()
            ).decode("ascii")

            image_html = (
                f'<img class="litlas-page-illustration" '
                f'src="data:image/png;base64,{encoded}" '
                f'style="width:{illustration_size}px;'
                f'height:{illustration_size}px;'
                f'top:{illustration_top}px;'
                f'left:{illustration_left}px;" '
                f'alt="">'
            )

            left_padding = (
                illustration_left
                + illustration_size
                + heading_gap
            )

    # Keep illustrations and heading in the same sticky container.
    with st.container(key="litlas_sticky_header"):
        st.markdown(
            f"""
            {logo_html}
            {image_html}

            <div class="litlas-heading"
                 style="padding-left:{left_padding}px;">
                <h1>{escape(title)}</h1>
                <p>{escape(subtitle)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_chapter_navigation(active_page=title)