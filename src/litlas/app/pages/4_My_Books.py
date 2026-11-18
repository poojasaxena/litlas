"""Published writing — a personal corner of the Litlas literary world."""

from html import escape

import streamlit as st
import base64
from pathlib import Path
from textwrap import dedent

from litlas.app.ui import apply_page_style, render_page_header
from litlas.processing.paths import (
    JINDAGI_COVER,
    LIFE_ENDLESS_EBB_COVER,
)

st.set_page_config(
    page_title="Ink & Verse · Litlas",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_page_style()

render_page_header(
    "Ink & Verse",
    "My literary world, in my own words",
    illustration="book_author",
    illustration_size=230,
    illustration_top=-42,

    illustration_left=0,
    heading_gap=5,
    title_height=90,
    ornament_width=230,
    ornament_offset_y=-6,
    subtitle_offset_y=-6,

    # Mobile
    mobile_illustration_size=100,
    mobile_illustration_top=0,

    # Mobile layout of the text group
    mobile_heading_gap=0,         # Gap between the illustration and text columns
    mobile_heading_offset_x=-45, # Move the entire text group left 45 px

    # Individual elements, from top to bottom
    mobile_eyebrow_offset_x=12,   # Move the eyebrow right 2 px
    mobile_eyebrow_offset_y=-15,  # Move the eyebrow up 9 px
    mobile_title_width=290,      # Large decorative page title (Literary Atlas here)
    mobile_title_offset_x=17,
    mobile_title_offset_y=-12,  # Move the large Litlas lettering up 12 px
    mobile_ornament_width=120,   # Thin decorative line
    mobile_ornament_offset_x=12,
    mobile_ornament_offset_y=-14,  # Move the line up
    mobile_subtitle_offset_x=13, # Where stories meet the world
    mobile_subtitle_offset_y=-14,  # Move “Where stories meet the world” up
    mobile_header_bottom_gap=-14,  # Pull the mobile navigation up toward the header
)


# For now, publication information stays with this small presentation page.
# When the collection grows, move these records into a separate data file.
BOOKS = [
    {
        "title": "Jindagi Sarakti Rahi",
        "language": "Hindi",
        "genre": "Poetry collection",
        "description": "A collection of my poetry in Hindi.",
        "cover": JINDAGI_COVER,
        "url": "https://www.amazon.com/dp/B0DP4HCBHK",
    },
    {
        "title": "Life's Endless Ebb",
        "language": "English",
        "genre": "Poetry collection",
        "description": "A collection of my poetry in English.",
        "cover": LIFE_ENDLESS_EBB_COVER,
        "url": "https://www.amazon.com/dp/B0DKBG3273",
    },
]

st.markdown(
    """
    <style>
    .litlas-books-intro {
        font-family: Georgia, serif;
        font-style: italic;
        color: #96785D;
        font-size: 1.05rem;
        margin: 0.5rem 0 1.5rem;
    }

    .litlas-gallery-title {
        font-family: "Cormorant Garamond", Georgia, serif !important;
        font-style: italic;
        font-size: 1.85rem;
        font-weight: 600;
        line-height: 1.1;
        color: #704D36;
        margin: 14px 0 7px;
    }
    .litlas-gallery-meta {
        font-family: Georgia, serif;
        font-size: 0.9rem;
        color: #96785D;
        margin-bottom: 8px;
    }

    .litlas-gallery-link {
        font-family: Georgia, serif;
        font-size: 0.88rem;
        color: #94704D !important;
        text-decoration: none;
    }

    .litlas-gallery-link:hover {
        text-decoration: underline;
    }
    .litlas-books-intro {
        text-align: center;
    }

    .litlas-gallery-title {
        margin-top: 10px;
    }

    .litlas-gallery-grid {
        display: grid;
        grid-template-columns: repeat(2, 242px);
        gap: 68px;
        justify-content: center;
        align-items: start;
        margin: 25px auto 0;
    }

    .litlas-gallery-book {
        width: 242px;
    }

    .litlas-gallery-image {
        display: block;
        width: 242px;
        height: 385px;
        object-fit: cover;
        margin: 0;

        box-shadow:
            12px 12px 12px rgba(35, 30, 25, 0.30),
            3px 4px 3px rgba(35, 30, 25, 0.22);
    }

/* Mobile: two poetry collections side by side */
@media screen and (max-width: 650px) {
    .litlas-gallery-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        width: 90%;
        max-width: 350px;
        margin: 18px auto 0;
    }

    .litlas-gallery-book {
        width: 100%;
        min-width: 0;
    }

    .litlas-gallery-image {
        width: 100%;
        height: auto;
        aspect-ratio: 242 / 385;
        object-fit: cover;
        box-shadow:
            5px 6px 8px rgba(35, 30, 25, 0.24);
    }

    .litlas-gallery-title {
        font-size: 1rem;
        line-height: 1.2;
        margin: 15px 0 5px;
    }

    .litlas-gallery-meta {
        font-size: 0.75rem;
        line-height: 1.3;
    }

    .litlas-gallery-link {
        font-size: 0.75rem;
        line-height: 1.4;
        overflow-wrap: anywhere;
    }

    .litlas-books-intro {
        font-size: 0.9rem;
        margin-bottom: 12px;
    }
    .litlas-gallery-title {
        font-size: 0.80rem !important;
        line-height: 1.2;
        margin: 8px 0 3px !important;
    }

    .litlas-gallery-meta {
    margin-bottom: 3px !important;
    }
}

    /* Slightly quieter titles */
    .litlas-gallery-title {
        font-size: 1.2rem;
        margin: 28px 0 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="litlas-books-intro">'
    'Two languages, two poetry collections, a shared thread of thoughts and feelings...'
    '</p>',
    unsafe_allow_html=True,
)

# A compact, centred gallery rather than full-page columns.
gallery_html = []

for book in BOOKS:
    cover_path = Path(book["cover"])
    encoded = base64.b64encode(cover_path.read_bytes()).decode("ascii")
    mime = "image/png" if cover_path.suffix.lower() == ".png" else "image/jpeg"

    gallery_html.append(
        dedent(f"""
            <div class="litlas-gallery-book">
                <img
                    class="litlas-gallery-image"
                    src="data:{mime};base64,{encoded}"
                    alt="{escape(book['title'], quote=True)}"
                >
                <div class="litlas-gallery-title">
                    {escape(book["title"])}
                </div>
                <div class="litlas-gallery-meta">
                    {escape(book["language"])} · Poetry
                </div>
                <a class="litlas-gallery-link"
                href="{escape(book["url"], quote=True)}"
                target="_blank"
                rel="noopener noreferrer">
                    View published edition ↗
                </a>
            </div>
        """).strip()
    )

st.markdown(
    '<div class="litlas-gallery-grid">'
    + "".join(gallery_html)
    + "</div>",
    unsafe_allow_html=True,
)
