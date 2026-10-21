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
    "A little corner of my literary world, written in my own words...",
    illustration="book_author",
    illustration_size=200,
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

    @media (max-width: 650px) {
        .litlas-gallery-grid {
            grid-template-columns: 242px;
            gap: 35px;
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
