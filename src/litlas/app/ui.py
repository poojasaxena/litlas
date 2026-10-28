"""Shared Streamlit styling for Litlas."""


import base64
from pathlib import Path
from html import escape
import streamlit as st

from litlas.processing.paths import load_config, HEADER_DIR, HEADER_FILES

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
/* ============================================================
   LITLAS — SHARED THEME
   One definition per component; desktop first, mobile last.
   Requires HTML classes: litlas-home-heading, litlas-section-heading,
   litlas-svg-title, litlas-eyebrow, litlas-home-tagline,
   litlas-home-ornament.
   ============================================================ */

/* App background and Streamlit chrome */
[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
}

.block-container {
    padding-top: 0.7rem !important;
    padding-bottom: 1rem !important;
    max-width: 1550px;
}

.stApp { background-color: #FAF7F1 !important; }
#MainMenu, footer { visibility: hidden; }
h1 { margin-top: 0 !important; padding-top: 0 !important; padding-bottom: 0.2rem !important; }

/* Vintage alerts */
div[data-testid="stAlert"] {
    background-color: #F0E6D7 !important;
    border: 1px solid #D4C1A7 !important;
    border-radius: 8px !important;
}
div[data-testid="stAlert"] > div,
div[data-testid="stAlert"] [data-baseweb="notification"] {
    background-color: transparent !important;
    border-color: transparent !important;
}
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] svg {
    color: #58412F !important;
    fill: #58412F !important;
}
div[data-testid="stAlert"] [data-testid="stIconMaterial"] {
    color: #A47B43 !important;
    font-size: 25px !important;
}

/* Header illustration and personal signature */
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
.litlas-page-illustration {
    position: absolute;
    top: -45px;
    left: 0;
    object-fit: contain;
    pointer-events: none;
    z-index: 2;
}

/* Shared SVG title: no browser Vivaldi font is needed */
.litlas-heading { min-height: 110px; }
.litlas-heading .litlas-svg-title {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0 !important;
}
.litlas-heading .litlas-svg-title img {
    display: block;
    height: 85px;
    width: auto;
    max-width: 100%;
    object-fit: contain;
}
/* Fallback h1 when an SVG is missing */
.litlas-heading h1:not(.litlas-svg-title) {
    font-family: Georgia, serif;
    font-size: 3rem;
    color: #58412F;
    font-weight: 400;
    margin: 0;
}

/* Ordinary section headers keep their long, beloved underline */
.litlas-section-heading .litlas-svg-title::after,
.litlas-section-heading h1:not(.litlas-svg-title)::after {
    content: "";
    display: block;
    width: 570px;
    max-width: 100%;
    height: 2px;
    margin: 5px 0 0 10px;
    background: #B29A7C;
}
.litlas-section-heading p {
    margin: 7px 0 0;
    padding-left: 10px;
    font-family: Georgia, serif;
    font-size: 0.95rem;
    font-style: italic;
    color: #81776E;
}

/* Home-page identity: eyebrow / wordmark / tagline / short line */
.litlas-home-heading {
    min-height: 155px;
    width: min(650px, 58%);
    margin: 0 auto;
    padding: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    text-align: center;
    gap: 2px;
    position: relative;
    top: -25px;
    margin-bottom: -20px;
}
.litlas-eyebrow {
    font-family: Georgia, serif;
    font-size: 11px;
    letter-spacing: 0.7px;
    color: #A47B63;
}
.litlas-home-heading .litlas-svg-title img {
    height: var(--title-height, 90px);
}
.litlas-home-tagline {
    font-family: Georgia, serif;
    font-size: 16px;
    font-style: italic;
    color: #81776E;
}
.litlas-home-ornament {
    width: min(100%, var(--ornament-width, 170px));
    height: 1px;
    background: #B29A7C;
    margin-top: 2px;
}

/* Sticky header shell */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
    position: relative;
}
[data-testid="stLayoutWrapper"]:has(> .st-key-litlas_sticky_header) {
    position: sticky !important;
    top: 30px !important;
    z-index: 100 !important;
    background: #FAF7F1 !important;
}
[data-testid="stLayoutWrapper"]:has(> .st-key-litlas_sticky_header)::before {
    content: "";
    position: absolute;
    top: -45px;
    left: 0;
    right: 0;
    height: 45px;
    background: #FAF7F1;
    pointer-events: none;
}
.st-key-litlas_sticky_header {
    position: relative !important;
    background: #FAF7F1 !important;
    min-height: 100px;
    padding-bottom: 15px !important;
}

/* Chapter navigation */
.st-key-litlas_sticky_header a[data-testid="stPageLink-NavLink"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
    width: auto !important;
    color: #96785D !important;
}
.st-key-litlas_sticky_header a[data-testid="stPageLink-NavLink"] p {
    color: #96785D !important;
    font-family: Georgia, serif !important;
    font-size: 13px !important;
    font-weight: 400 !important;
}
.st-key-litlas_sticky_header a[data-testid="stPageLink-NavLink"]:hover,
.st-key-litlas_sticky_header a[data-testid="stPageLink-NavLink"]:hover p {
    color: #58412F !important;
    background: transparent !important;
}
.st-key-litlas_sticky_header a[data-testid="stPageLink-NavLink"][aria-current="page"],
.st-key-litlas_sticky_header a[data-testid="stPageLink-NavLink"][aria-current="page"] p,
.st-key-litlas_sticky_header [data-testid="stPageLink"] a[aria-disabled="true"],
.st-key-litlas_sticky_header [data-testid="stPageLink"] a[aria-disabled="true"] p {
    color: #58412F !important;
    font-weight: 700 !important;
    text-decoration: underline !important;
    text-underline-offset: 4px;
    opacity: 1 !important;
    background: transparent !important;
}
.st-key-litlas_sticky_header .litlas-chapter-separator {
    color: #B29A7C !important;
    font-family: Georgia, serif;
    font-size: 15px;
}
.st-key-litlas_sticky_header [data-testid="stPageLink"] p,
.st-key-litlas_sticky_header .litlas-chapter-separator {
    margin: 0 !important;
}

/* Hide sidebar and mobile-only navigation on desktop */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] { display: none !important; }
.st-key-litlas_mobile_nav { display: none !important; }

/* ============================================================
   MOBILE — <= 640px
   ============================================================ */
@media screen and (max-width: 640px) {
    .stApp .block-container {
        padding-top: 0 !important;
        padding-left: 8px !important;
        padding-right: 8px !important;
    }
    [data-testid="stLayoutWrapper"]:has(> .st-key-litlas_sticky_header) {
        position: relative !important;
        top: 0 !important;
    }
    [data-testid="stLayoutWrapper"]:has(> .st-key-litlas_sticky_header)::before {
        display: none !important;
    }


    .st-key-litlas_sticky_header {
        min-height: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
    }

    /* Compact spacing between the header and page content */
    .stApp [data-testid="stMainBlockContainer"]
    > [data-testid="stVerticalBlock"] {
        gap: 0.75rem !important;
    }
    /* Mobile header illustration */
    .st-key-litlas_sticky_header .litlas-page-illustration {
        width: 90px !important;
        height: 90px !important;
        top: 0 !important;
        left: 0 !important;
        transform: none !important;
    }

    /* Hide personal signature on mobile */
    .st-key-litlas_sticky_header .litlas-logo {
        display: none !important;
    }

    /* Heading group occupies the space beside the illustration */
    .st-key-litlas_sticky_header .litlas-heading.litlas-home-heading {
        box-sizing: border-box;
        width: calc(100% - 100px);
        min-height: 100px !important;
        margin: 0 0 0 100px !important;
        padding: 0 !important;
        top: 0 !important;
        transform: none !important;
        display: flex;
        flex-direction: column;
        align-items: center !important;
        justify-content: center;
        text-align: center !important;
        gap: 3px;
    }

    /* Eyebrow */
    .st-key-litlas_sticky_header .litlas-eyebrow {
        order: 0;
        font-size: 8px;
        text-align: center;
        transform: translateX(-45px);
    }

    /* Vivaldi SVG heading */
    .st-key-litlas_sticky_header .litlas-home-heading .litlas-svg-title {
        order: 1;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .st-key-litlas_sticky_header .litlas-home-heading .litlas-svg-title img {
        width: min(100%, 190px);
        height: auto;
    }

    /* Line between title and subtitle */
    .st-key-litlas_sticky_header .litlas-home-ornament {
        order: 2;
        width: 120px !important;
        margin: 3px auto 5px !important;
        transform: translateX(-35px);
    }

    /* Subtitle */
    .st-key-litlas_sticky_header .litlas-home-tagline {
        order: 3;
        max-width: 280px;
        font-size: 12px;
        line-height: 1.3;
        text-align: center !important;
        transform: translateX(-35px);
    }


    /* All other chapter headings */
    .st-key-litlas_sticky_header .litlas-section-heading .litlas-svg-title img {
        width: min(100%, 260px);
        height: auto;
    }
    .st-key-litlas_sticky_header .litlas-section-heading .litlas-svg-title::after,
    .st-key-litlas_sticky_header .litlas-section-heading h1:not(.litlas-svg-title)::after {
        width: 100%;
        margin: 6px 0 0;
    }
    .st-key-litlas_sticky_header .litlas-section-heading p {
        font-size: 0.65rem !important;
        line-height: 1.3 !important;
        padding-left: 0 !important;
        margin: 8px 0 0 !important;
        text-align: left !important;
    }
    .st-key-litlas_sticky_header .litlas-heading h1:not(.litlas-svg-title) {
        font-size: clamp(2rem, 9vw, 2.6rem) !important;
        line-height: 1.1 !important;
        white-space: normal !important;
    }

    /* Streamlit content typography */
    .stApp h2 { font-size: 1.55rem !important; line-height: 1.2 !important; }
    .stApp h3 { font-size: 1.4rem !important; line-height: 1.2 !important; }
    .stApp p, .stApp li { font-size: 0.85rem; line-height: 1.4; }
    .stApp [data-testid="stHeading"] h3 {
        font-size: 1.5rem !important;
        line-height: 1.15 !important;
    }
    .stApp [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    .stApp [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }

    /* Replace desktop navigation with popover */
    .st-key-litlas_desktop_nav { display: none !important; }
    .st-key-litlas_mobile_nav { display: block !important; }
    .st-key-litlas_mobile_nav button {
        background-color: #F5EFE4 !important;
        color: #58412F !important;
        border: 1px solid #D4C1A7 !important;
        font-family: Georgia, serif !important;
    }
    div[data-baseweb="popover"]:has(a[data-testid="stPageLink-NavLink"]) > div {
        background-color: #FAF7F1 !important;
    }
    [data-testid="stPopoverBody"]:has(a[data-testid="stPageLink-NavLink"]) {
        background: #FAF7F1 !important;
        border: 1px solid #D4C1A7 !important;
        border-radius: 10px !important;
        color: #58412F !important;
        width: 200px !important;
        min-width: 0 !important;
        max-width: calc(100vw - 32px) !important;
        box-sizing: border-box !important;
    }
    [data-testid="stPopoverBody"] a[data-testid="stPageLink-NavLink"],
    [data-testid="stPopoverBody"] a[data-testid="stPageLink-NavLink"] p {
        color: #58412F !important;
    }
    
}
@media screen and (max-width: 640px) {
    .st-key-litlas_sticky_header .litlas-home-heading {
        margin-bottom: 0;
    }
}

/* Hide Streamlit Community Cloud controls on mobile */
@media screen and (max-width: 640px) {
    [data-testid="stToolbar"],
    #GithubIcon {
        display: none !important;
    }
}

</style>
""",
        unsafe_allow_html=True,
    )

st.html("""
<style>
.st-key-litlas_enter_atlas button {
    background-color: #F5EFE4 !important;
    color: #58412F !important;
    border: 1px solid #B29A7C !important;
    border-radius: 6px !important;
    font-family: Georgia, serif !important;
    font-size: 14px !important;
}

.st-key-litlas_enter_atlas button:hover {
    background-color: #EDE2D2 !important;
    color: #58412F !important;
    border-color: #96785D !important;
}

.st-key-litlas_enter_atlas button p {
    color: #58412F !important;
    font-family: Georgia, serif !important;
}
</style>
""")

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
        ("Litlas", "main.py", ""),
        ("Reading Density", "pages/1_Reading_Density.py", "Reading_Density"),
        ("Reading Statistics", "pages/2_Reading_Statistics.py", "Reading_Statistics"),
        ("Library Management", "pages/3_Library_Management.py", "Library_Management"),
        ("Ink & Verse", "pages/4_My_Books.py", "My_Books"),
        ("About Litlas", "pages/5_About_Litlas.py", "About_Litlas"),
    ]

    active_route = next(
        (
            route for label, _, route in pages
            if label == active_page
            or (label == "Litlas" and active_page == "Literary Atlas")
        ),
        None,
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

    # Existing desktop navigation
    with st.container(
        key="litlas_desktop_nav",
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


    # New mobile navigation
    with st.container(key="litlas_mobile_nav"):
        with st.popover("☰ Menu"):
            for label, path, _ in pages:
                st.page_link(path, label=label)


def render_header_title(title: str) -> str:
    """Return the Vivaldi SVG heading, falling back to text."""

    filename = HEADER_FILES.get(title)

    if not filename:
        return f"<h1>{escape(title)}</h1>"

    svg_path = HEADER_DIR / filename

    # print(
    #     f"HEADER DEBUG: title={title!r}, "
    #     f"filename={filename!r}, "
    #     f"path={svg_path}, "
    #     f"exists={svg_path.is_file()}"
    # )

    if not svg_path.is_file():
        return f"<h1>{escape(title)}</h1>"

    svg_content = svg_path.read_text(encoding="utf-8")
    svg_content = svg_content.replace("#000000", "#58412F")

    encoded = base64.b64encode(
        svg_content.encode("utf-8")
    ).decode("ascii")

    return (
        '<h1 class="litlas-svg-title">'
        f'<img src="data:image/svg+xml;base64,{encoded}" '
        f'alt="{escape(title, quote=True)}">'
        '</h1>'
    )

def render_page_header(
    title: str,
    subtitle: str,
    illustration: str | None = None,
    illustration_size: int = 110,
    illustration_top: int = -45,
    illustration_left: int = 0,
    heading_gap: int = 5,
    title_height: int = 90,
    ornament_width: int = 170,
) -> None:
    """Render the shared sticky vintage Litlas heading."""

    logo_html = ""
    logo = load_logo_path()    
    
    if logo:
        encoded = base64.b64encode(
            logo.read_bytes()
        ).decode("ascii")

        mime_type = "image/svg+xml" if logo.suffix.lower() == ".svg" else "image/png"

        logo_html = (
            f'<img class="litlas-logo" '
            f'src="data:{mime_type};base64,{encoded}" '
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

    title_html = render_header_title(title)

    tagline = subtitle

    heading_html = (
        '<div class="litlas-heading litlas-home-heading" '
        f'style="--title-height:{title_height}px; '
        f'--ornament-width:{ornament_width}px;">'
        '<div class="litlas-eyebrow">'
        '✦ A PERSONAL LITERARY ATLAS ✦'
        '</div>'
        f'{title_html}'
        f'<div class="litlas-home-tagline">{escape(tagline)}</div>'
        '<div class="litlas-home-ornament"></div>'
        '</div>'
    )

    header_html = "\n".join([
        logo_html,
        image_html,
        heading_html,
    ])

    with st.container(key="litlas_sticky_header"):
        st.markdown(
            header_html,
            unsafe_allow_html=True,
        )

        render_chapter_navigation(active_page=title)