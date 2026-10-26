
"""About Litlas — the story behind a personal literary atlas."""

from html import escape

import streamlit as st

from litlas.app.ui import apply_page_style, render_page_header
import base64
from litlas.app.ui import load_logo_path

# -------------------------------------------------
# Page configuration
# -------------------------------------------------

st.set_page_config(
    page_title="About Litlas",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_page_style()

render_page_header(
    "About Litlas",
    "A personal journey through stories and the world...",
    illustration="about_litlas",
    illustration_size=220,
)

# -------------------------------------------------
# Personal details
# Replace the example URLs with your actual links
# -------------------------------------------------

PUBLIC_NAME = "Pooja Saxena"
GOODREADS_URL = "https://www.goodreads.com/user/show/22058002-pooja"
GITHUB_URL = "https://github.com/poojasaxena"


# -------------------------------------------------
# About page styling
# -------------------------------------------------

st.html("""
<style>

.litlas-about {
    max-width: 1100px;
    margin: 0 auto 12px;
    padding: 22px 42px 24px;
    background: #FAF7F1;
    border: 1px solid #D4C1A7;
    border-radius: 12px;
    color: #58412F;
    font-family: Georgia, serif;
    box-shadow: 0 5px 22px rgba(88, 65, 47, 0.06);
    box-sizing: border-box;
}

.litlas-about-kicker {
    text-align: center;
    font-size: 11px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #9B8063;
}

.litlas-about-title {
    text-align: center;
    font-family: Georgia, serif;
    font-style: italic;
    font-size: 32px;
    font-weight: 400;
    margin: 10px 0;
    color: #58412F;
}

.litlas-about-rule {
    width: 145px;
    height: 1px;
    background: #B29A7C;
    margin: 16px auto;
}

.litlas-about-opening {
    text-align: center;
    font-style: italic;
    font-size: 18px;
    line-height: 1.5;
    color: #7B5B45;
    margin: 16px auto 20px;
    max-width: 100%;
}

.litlas-about-section {
    margin-top: 16px;
}

.litlas-about-section h3 {
    font-family: Georgia, serif;
    font-weight: 400;
    font-size: 20px;
    font-style: italic;
    color: #76563E;
    margin: 0 0 10px;
}

.litlas-about-section p {
    font-size: 15px;
    line-height: 1.65;
    margin: 0 0 12px;
}

.litlas-about-signature {
    text-align: center;
    font-style: italic;
    font-size: 14px;
    color: #896A50;
    margin-top: 12px;
}

.litlas-about-links {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 28px;
    margin-top: 12px;
}

.litlas-about-links a {
    color: #795740;
    font-family: Georgia, serif;
    font-size: 14px;
    text-decoration: none;
}

.litlas-about-links a:hover {
    text-decoration: underline;
    text-underline-offset: 4px;
}

.litlas-about-personal-logo {
    display: block;
    width: 115px;
    height: 115px;
    object-fit: contain;
    margin: 0 auto 6px;
}

.litlas-about-opening strong {
    font-weight: 600;
    font-style: italic;
}

.litlas-opening-ornament {
    color: #B29A7C;
    font-style: normal;
    font-size: 18px;
    margin: 0 12px;
}


/* -------------------------------------------------
   Mobile version
   ------------------------------------------------- */

@media screen and (max-width: 640px) {

    .litlas-about {
        margin: 5px 0 20px;
        padding: 20px 18px 24px;
        border-radius: 8px;
    }

    .litlas-about-kicker {
        font-size: 9px;
        letter-spacing: 1.4px;
    }

    .litlas-about-title {
        font-size: 27px;
    }

    .litlas-about-rule {
        margin: 14px auto;
    }

    .litlas-about-opening {
        font-size: 16px;
        line-height: 1.5;
        margin: 14px auto 18px;
    }

    .litlas-about-section {
        margin-top: 14px;
    }

    .litlas-about-section h3 {
        font-size: 20px;
    }

    .litlas-about-section p {
        font-size: 14px;
        line-height: 1.65;
        margin-bottom: 12px;
    }

    .litlas-about-links {
        gap: 22px;
        flex-wrap: wrap;
    }

    .litlas-about-links a {
        font-size: 13px;
    }
}
@media screen and (max-width: 640px) {
    .litlas-about-card {
        max-width: 100%;
    }

    .litlas-about-personal-logo {
        width: 100px;
        height: 100px;
    }
}
</style>
""")


# -------------------------------------------------
# Personal links and signature
# -------------------------------------------------

goodreads_link = (
    f'<a href="{escape(GOODREADS_URL, quote=True)}" '
    f'target="_blank" rel="noopener noreferrer">♧ Goodreads</a>'
    if GOODREADS_URL else ""
)

github_link = (
    f'<a href="{escape(GITHUB_URL, quote=True)}" '
    f'target="_blank" rel="noopener noreferrer">'
    f'<img src="https://github.githubassets.com/favicons/favicon.svg" '
    f'alt="" width="15" height="15" '
    f'style="vertical-align:-2px; margin-right:5px; '
    f'filter: brightness(0) saturate(100%) invert(25%) sepia(15%) '
    f'saturate(1050%) hue-rotate(344deg) brightness(95%);">'
    f'GitHub</a>'
    if GITHUB_URL else ""
)

links_html = "\n".join(
    link for link in (goodreads_link, github_link) if link
)

name_html = (
    f"Created &amp; curated by {escape(PUBLIC_NAME)}"
    if PUBLIC_NAME
    else "Created with a love of books"
)

## Personal logo
logo_path = load_logo_path()

logo_html = ""

if logo_path:
    mime = "image/svg+xml" if logo_path.suffix.lower() == ".svg" else "image/png"
    logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")

    logo_html = (
        f'<img src="data:{mime};base64,{logo_data}" '
        f'alt="Personal logo" class="litlas-about-personal-logo">'
    )

# -------------------------------------------------
# About Litlas — single integrated card
# -------------------------------------------------

st.html(f"""
<div class="litlas-about">

    <div class="litlas-about-kicker">
        A PERSONAL COLLECTION OF WORLD LITERATURE 
        <!-- MY JOURNEY THROUGH WORLD LITERATURE -->
    </div>

    <h2 class="litlas-about-title">
        The Story Behind Litlas
    </h2>

    <div class="litlas-about-rule"></div>

    <div class="litlas-about-opening">
        <span class="litlas-opening-ornament">✧</span>
        Every book opens a world; these are the worlds I've wandered through.
        <span class="litlas-opening-ornament">✧</span>
    </div>

    <div class="litlas-about-section">

        <h3>A Note from the Creator</h3>

        <p>
            I'm an enthusiastic reader with a curiosity for
            literature from around the world. I love discovering
            unfamiliar writers, exploring different cultures,
            and occasionally finding a book that stays with me
            long after I've turned its last page...
        </p>

        <p>
            I created Litlas to bring my reading life together
            in one place: part personal library, part literary
            world map, and always a book in progress.
        </p>

        <p>
            You're welcome to explore my collection and see
            where the stories have taken me.
        </p>

    </div>

    <div class="litlas-about-rule"></div>

    <div class="litlas-about-signature">
        {logo_html}
        <div>{name_html}</div>
    </div>

    <div class="litlas-about-links">
        {links_html}
    </div>

</div>
""")
