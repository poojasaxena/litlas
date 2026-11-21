
"""About Litlas — the story behind a personal literary atlas."""

import base64
from html import escape

import streamlit as st

from litlas.app.ui import apply_page_style, load_logo_path, render_page_header, is_mobile_browser
from litlas.processing.paths import ILLUSTRATIONS_DIR

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
is_mobile = is_mobile_browser()

render_page_header(
    "About Litlas",
    "A personal journey through stories" if is_mobile else "A personal journey through stories and the world",

    illustration="about_litlas",
    illustration_size=230,
    illustration_top=-42,

    illustration_left=0,
    heading_gap=5,
    title_height=90,
    ornament_width=290,
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
    mobile_eyebrow_offset_y=-14,  # Move the eyebrow up 9 px
    mobile_title_width=360,      # Large decorative page title (Literary Atlas here)
    mobile_title_offset_x=17,
    mobile_title_offset_y=-12,  # Move the large Litlas lettering up 12 px
    mobile_ornament_width=120,   # Thin decorative line
    mobile_ornament_offset_x=12,
    mobile_ornament_offset_y=-14,  # Move the line up
    mobile_subtitle_offset_x=13,
    mobile_subtitle_offset_y=-14,
    mobile_header_bottom_gap=-32,  # Pull the mobile navigation up toward the header
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
    box-sizing: border-box;
    max-width: 1130px;
    margin: 0 auto 12px;
    padding: 8px 0 24px;
    color: #58412F;
    font: 16px/1.65 Georgia, serif;
}

.litlas-about-reading-page {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    padding: clamp(24px, 4vw, 52px) 0;
}

.litlas-about-watercolor {
    position: absolute;
    z-index: -1;
    top: 50%;
    left: 0;
    width: 100%;
    height: auto;
    transform: translateY(-50%);
    pointer-events: none;
}

.litlas-about-story {
    width: min(47%, 520px);
    margin: 0 auto;
    text-align: center;
}

.litlas-about .litlas-about-title {
    margin: 0 0 13px;
    padding: 0;
    color: #76563E;
    font: 400 14px/1.4 Georgia, serif;
    letter-spacing: 0.06em;
    text-align: center;
}

.litlas-about-story p {
    margin: 0;
    font: inherit;
}

.litlas-about-story p + p {
    margin-top: 0.85em;
}

.litlas-about-signoff {
    margin: 30px 0 0;
    text-align: center;
}

.litlas-about-signoff::before {
    display: block;
    width: 64px;
    height: 1px;
    margin: 0 auto 10px;
    background: #B29A7C;
    content: "";
}

.litlas-about-personal-logo {
    display: block;
    width: 132px;
    height: 132px;
    margin: 0 auto 5px;
    object-fit: contain;
}

.litlas-about-signature {
    color: #7B5B45;
    font-style: italic;
}
.litlas-about-established {
    display: block;
    margin-top: 0;
    font-size: 0.9em;
    line-height: 1.2;
    color: #7B5B45;
    font-style: normal;
    letter-spacing: 0.03em;
}

.litlas-about-links {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0 18px;
    margin-top: 7px;
}

.litlas-about-links a {
    color: #795740;
    font-size: 14px;
    text-decoration-color: #B29A7C;
    text-underline-offset: 3px;
}

/* Media query for large screens */
@media screen and (width > 840px) {
    [data-testid="stMain"]:has(.litlas-about) {
        overflow-x: clip;
    }

    .litlas-about {
        position: relative;
        isolation: isolate;
        margin-bottom: 0;
        padding-bottom: 8px;
    }

    .litlas-about-reading-page {
        position: static;
        isolation: auto;
        overflow: visible;
        padding: clamp(18px, 4vh, 34px) 5px 12px;
    }

    .litlas-about-watercolor {
        top: 8px;
        left: 50%;
        width: 100vw;
        max-width: none;
        height: calc(100% - 8px);
        transform: translateX(-50%);
        object-fit: cover;
        mask-image: linear-gradient(180deg, transparent, #000 9%, #000 86%, transparent);
    }

    .litlas-about-signoff {
        margin-top: clamp(10px, 2vh, 18px);
    }

    .litlas-about-personal-logo {
        width: clamp(84px, 12vh, 112px);
        height: clamp(84px, 12vh, 112px);
    }

.litlas-about-story {
    position: relative;
    isolation: isolate;
}

.litlas-about-story::before {
    content: "";
    position: absolute;
    inset: -12px auto 6% 50%;
    width: 100vw;
    transform: translateX(-50%);

    background:
        radial-gradient(
            ellipse 17% 37% at 19% 50%,
            rgba(191, 148, 76, 0.10),
            rgba(191, 148, 76, 0.035) 55%,
            transparent 100%
        ),
        radial-gradient(
            ellipse 17% 37% at 81% 58%,
            rgba(176, 145, 111, 0.09),
            rgba(176, 145, 111, 0.03) 55%,
            transparent 100%
        );
    z-index: -1;
    pointer-events: none;
}

}
.litlas-about-story p {
    text-align: center;
}

.litlas-drop-cap {
    float: left;
    margin: 0.06em 0.12em 0 0;
    color: #6E4B3A;
    font: bold 3em/0.85 Georgia, serif;
}

@media screen and (width > 840px) and (max-height: 780px) {
    .litlas-about-reading-page {
        padding-block: 16px 8px;
    }

    .litlas-about-story {
        line-height: 1.5;
    }

    .litlas-about-signoff {
        margin-top: 9px;
    }

    .litlas-about-signoff::before {
        margin-bottom: 6px;
    }
}

@media screen and (max-width: 840px) {
    .litlas-about-story {
        width: min(calc(100% - 36px), 520px);
        text-align: left;
    }

    .litlas-about-watercolor {
        opacity: 0.23;
        mask-image: linear-gradient(90deg, #000, transparent 12%, transparent 88%, #000);
    }
}

/* Mobile styles */
@media screen and (max-width: 640px) {
    .litlas-about {
        font-size: 15px;
        line-height: 1.3;
        padding-top: 0;
        margin-top: -22px !important;
    }

    .litlas-about-watercolor {
        top: auto;
        left: auto;
        right: -12px;
        bottom: 6px;
        width: min(170%, 850px);
        max-width: none;
        height: auto;
        transform: none;
        opacity: 0.78;
        mask-image: linear-gradient(
            to right,
            transparent 52%,
            rgba(0, 0, 0, 0.35) 64%,
            #000 78%
        );
    }

    .litlas-about-reading-page {
        padding: 0 0 0;
    }

    .litlas-about-signoff {
        margin-top: 2px;
    }

    .litlas-about-personal-logo {
        width: 108px;
        height: 108px;
    }

    .litlas-about-signature {
        font-size: 12px;
    }
}
</style>
""")


# -------------------------------------------------
# Personal links and signature
# -------------------------------------------------

goodreads_link = (
    f'<a href="{escape(GOODREADS_URL, quote=True)}" '
    f'target="_blank" rel="noopener noreferrer"><span style="color: #6E4B3A;">♣︎</span> Goodreads</a>'
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
        f'alt="" class="litlas-about-personal-logo">'
    )

# -------------------------------------------------
# About Litlas — story and signature
# -------------------------------------------------

#watercolor_path = ILLUSTRATIONS_DIR / "about-literary-margins.png"
watercolor_path = ILLUSTRATIONS_DIR / "about-literary-margins-muted.png"
#watercolor_path = ILLUSTRATIONS_DIR / "about-literary-margins-desktop.png"
watercolor_src = base64.b64encode(watercolor_path.read_bytes()).decode("ascii")

st.html(f"""
<section class="litlas-about" aria-labelledby="litlas-about-title">
    <div class="litlas-about-reading-page">
        <img class="litlas-about-watercolor" src="data:image/png;base64,{watercolor_src}" alt="">
        <div class="litlas-about-story">
            <h2 id="litlas-about-title" class="litlas-about-title">The Stories I Carry</h2>
            <p>
                <span class="litlas-drop-cap">I</span> am an enthusiastic reader with a curiosity for
                literature from around the world. I love discovering
                unfamiliar writers, exploring different cultures,
                and occasionally finding a book that stays with me
                long after I've turned its last page.
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
    </div>

    <figure class="litlas-about-signoff">
        {logo_html}
        <figcaption class="litlas-about-signature">
            {name_html}
            <span class="litlas-about-established">
                <time datetime="2026-10">October 2026</time>
            </span>
        </figcaption>
    </figure>
    <div class="litlas-about-links">{links_html}</div>
</section>
""")
