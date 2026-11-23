"""
litlas.app.visualizations.unforgotten
Visualization of unforgettable literary characters.
"""

import base64
import html
import streamlit as st
from litlas.db_backend import get_repository

# =====================================================
# THE UNFORGOTTEN — LAYOUT CONTROLS
# =====================================================

# Card geometry
CARD_PADDING_X = 12          # Horizontal padding (px)
CARD_PADDING_Y = 8           # Vertical padding (px)
CARD_GAP = 10                # Space between cards (px)
CARD_RADIUS = 14             # Rounded corners (px)
CARD_MIN_HEIGHT = 0          # 0 = automatic height

# Ornament
ORNAMENT_STYLE = "vine"  # "antique" or "botanical" or "feather" or "vine"

ORNAMENT_WIDTH = 75      # Horizontal ornament width (px)
ORNAMENT_HEIGHT = 22     # Ornament height (px)
ICON_BOTTOM_GAP = 0      # Space below ornament (px)

# Character
NAME_SIZE = 18              # Character name font size (px)
NAME_BOTTOM_GAP = 3          # Space below name (px)

# Nickname and book
META_GAP = 3                 # Space below nickname (px)
META_BOTTOM_GAP = 6          # Space below book title (px)

# Reflection
DIVIDER_BOTTOM_GAP = 6       # Space below divider (px)
REFLECTION_SIZE = 16         # Reflection font size (px)
REFLECTION_LINE_HEIGHT = 1.3

# Section layout
SECTION_TOP_GAP = 0         # Space above heading (px)
HEADER_BOTTOM_GAP = 8        # Space below subtitle (px)
SUBTITLE_TOP_GAP = 4         # Space between title and subtitle (px)

# Optional scrolling
ENABLE_SCROLL = True        # Change to True to enable scrolling
SCROLL_HEIGHT = 400          # Maximum grid height when scrolling (px)

# Responsive layout
SINGLE_COLUMN_BREAKPOINT = 340  # Grid container width (px)


# =====================================================
# CHARACTER DATA
# =====================================================

UNFORGOTTEN = [
    {
        "name": "Augustus McCrae",
        "short": "Gus",
        "book": "Lonesome Dove",
        "reflection": (
            "He could make you laugh at life, "
            "even when life gave you every reason to weep."
        ),
    },
    {
        "name": "Billy Watson",
        "short": "Billy",
        "book": "The Lincoln Highway",
        "reflection": (
            "He saw a world full of stories, adventures, "
            "and possibilities where others saw only ordinary days."
        ),
    },
    {
        "name": "Jean Valjean",
        "short": "Valjean",
        "book": "Les Misérables",
        "reflection": (
            "A soul remade through mercy, carrying dignity "
            "through suffering and grace."
        ),
    },
    {
        "name": "John Galt",
        "short": "Galt",
        "book": "Atlas Shrugged",
        "reflection": (
            "A mind unwilling to surrender its clarity, "
            "purpose, or freedom."
        ),
    },
]


# =====================================================
# FEATHER ICON
# =====================================================

# =====================================================
# ANTIQUE FLOURISH ORNAMENT
# =====================================================

# =====================================================
# ORNAMENT COLLECTION
# =====================================================

ORNAMENTS = {

    # Original antique flourish — preserved unchanged
    "antique": """
    <svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 180 36"
         fill="none"
         stroke="#A47B43"
         stroke-width="1.4"
         stroke-linecap="round"
         stroke-linejoin="round">

        <path d="M15 18
                 C35 18 42 4 59 9
                 S72 29 90 18
                 S112 4 125 13
                 S151 18 165 18"/>

        <path d="M15 18 C32 18 39 31 53 26"/>
        <path d="M165 18 C148 18 141 31 127 26"/>

        <path d="M84 18 Q90 10 96 18 Q90 26 84 18Z"/>
    </svg>
    """,

    # New botanical tendril — curved stem and delicate leaves
    "botanical": """
    <svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 180 32"
         fill="none"
         stroke="#A47B43"
         stroke-width="1.25"
         stroke-linecap="round"
         stroke-linejoin="round">

        <path d="M22 22
                 C52 27 65 8 90 17
                 C115 26 128 7 158 12"/>

        <path d="M48 21 Q35 8 41 7 Q52 9 53 20"/>
        <path d="M70 15 Q65 5 72 5 Q82 8 75 16"/>
        <path d="M109 19 Q111 7 119 9 Q122 16 109 19"/>
        <path d="M139 13 Q143 4 150 5 Q151 12 139 13"/>

    </svg>
    """,

    # Slanted calligraphic feather
    "feather": """
    <svg xmlns="http://www.w3.org/2000/svg"
         viewBox="0 0 100 65"
         fill="none"
         stroke="#96785D"
         stroke-width="1.3"
         stroke-linecap="round"
         stroke-linejoin="round">

        <!-- Gently curved feather outline -->
        <path d="M28 53
                 C24 38 30 18 65 8
                 Q76 5 78 9
                 C75 27 60 44 32 48"/>

        <!-- Long diagonal quill -->
        <path d="M24 59 Q42 34 73 11"/>

        <!-- Fine feather barbs -->
        <path d="M40 36 L31 29"/>
        <path d="M48 29 L41 20"/>
        <path d="M57 22 L53 13"/>
        <path d="M45 36 L58 37"/>
        <path d="M55 26 L68 25"/>

    </svg>
    """,

    # Laurel vine — flowing stem with delicate leaves
    "vine": """
    <svg xmlns="http://www.w3.org/2000/svg"
         viewBox="25 10 95 38"
         fill="none"
         stroke="#96785D"
         stroke-width="1.2"
         stroke-linecap="round"
         stroke-linejoin="round">

        <!-- Graceful curved stem -->
        <path d="M29 43
                 C45 24 66 45 76 28
                 C83 18 97 18 109 25"/>

        <!-- First curved leaf -->
        <path d="M54 35
                 Q43 19 49 17
                 Q61 22 58 35"/>

        <!-- Second leaf -->
        <path d="M78 30
                 Q81 15 92 14
                 Q92 25 78 30"/>

        <!-- Third leaf -->
        <path d="M99 23
                 Q108 14 116 17
                 Q113 25 99 23"/>

    </svg>
    """,
}

ORNAMENT_ICON = ORNAMENTS[ORNAMENT_STYLE]

ORNAMENT_IMAGE = base64.b64encode(
    ORNAMENT_ICON.encode("utf-8")
).decode("ascii")

# =====================================================
# RENDER
# =====================================================

def render_unforgotten():
    """Render The Unforgotten as a compact literary card collection."""

    repo = get_repository()
    characters = repo.get_unforgotten_characters()

    min_height_css = (
        f"min-height: {CARD_MIN_HEIGHT}px;"
        if CARD_MIN_HEIGHT > 0
        else ""
    )

    scrolling_css = (
        f"""
        max-height: {SCROLL_HEIGHT}px;
        overflow-y: auto;
        overflow-x: hidden;
        padding-right: 4px;
        align-content: start;
        """
        if ENABLE_SCROLL
        else ""
    )

    # -------------------------------------------------
    # Styles
    # -------------------------------------------------

    st.html(
        f"""
        <style>

        .litlas-unforgotten-section {{
            margin-top: {SECTION_TOP_GAP}px;
            container-type: inline-size;
        }}

        .litlas-unforgotten-header {{
            text-align: left;
            margin-bottom: {HEADER_BOTTOM_GAP}px;
        }}

        .litlas-unforgotten-title {{
            font-family: "Cormorant Garamond", Georgia, serif;
            font-size: 32px;
            font-weight: 700;
            font-style: italic;
            color: #58412F;
            line-height: 1.2;
            margin: 0;
        }}

        .litlas-unforgotten-subtitle {{
            font-family: "Source Sans 3", sans-serif;
            font-size: 1.05rem;
            font-style: italic;
            color: #7A6858;
            line-height: 1.3;
            margin-top: {SUBTITLE_TOP_GAP}px;
        }}

        .litlas-unforgotten-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            grid-auto-rows: max-content;
            align-content: start;
            gap: {CARD_GAP}px;
            margin-top: 40px;
            {scrolling_css}
        }}

        .litlas-unforgotten-card {{
            background: #F8F3EA;
            border: 1px solid #DCCFBE;
            border-radius: {CARD_RADIUS}px;
            padding: {CARD_PADDING_Y}px {CARD_PADDING_X}px;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            box-shadow: none;
            box-sizing: border-box;
            min-width: 0;
            {min_height_css}
        }}

        .litlas-unforgotten-icon {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: {ICON_BOTTOM_GAP}px;
            line-height: 1;
        }}

        .litlas-unforgotten-icon img {{
            width: {ORNAMENT_WIDTH}px;
            height: {ORNAMENT_HEIGHT}px;
            object-fit: contain;
        }}

        .litlas-unforgotten-name {{
            font-family: "Source Serif Pro", Georgia, serif;
            font-size: {NAME_SIZE}px;
            font-weight: 700;
            color: #2F2A26;
            line-height: 1.15;
            margin: 0 0 {NAME_BOTTOM_GAP}px;
            overflow-wrap: break-word;
        }}

        .litlas-unforgotten-short {{
            font-size: 0.9rem;
            color: #7A6B5F;
            line-height: 1.2;
            margin: 0 0 {META_GAP}px;
        }}

        .litlas-unforgotten-book {{
            font-size: 0.85rem;
            font-style: italic;
            color: #9A8B7D;
            line-height: 1.2;
            margin: 0 0 {META_BOTTOM_GAP}px;
        }}

        .litlas-unforgotten-divider {{
            border-top: 1px solid #E4DACE;
            margin: 0 0 {DIVIDER_BOTTOM_GAP}px;
        }}

        .litlas-unforgotten-reflection {{
            font-size: {REFLECTION_SIZE}px;
            font-style: italic;
            line-height: {REFLECTION_LINE_HEIGHT};
            color: #3F3833;
            margin: 0;
            overflow-wrap: break-word;
        }}

        @container (max-width: {SINGLE_COLUMN_BREAKPOINT}px) {{
            .litlas-unforgotten-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        </style>
        """
    )

    # -------------------------------------------------
    # Character cards
    # -------------------------------------------------

    cards = []

    for item in characters:
        name = html.escape(item["name"])
        short = html.escape(item["familiar_name"] or "")
        book = html.escape(item["book"])
        reflection = html.escape(item["reflection"])

        card = f"""
        <div class="litlas-unforgotten-card">

            <div class="litlas-unforgotten-icon">
                <img
                    src="data:image/svg+xml;base64,{ORNAMENT_IMAGE}"
                    alt=""
                    width="{ORNAMENT_WIDTH}"
                    height="{ORNAMENT_HEIGHT}"
                    style="display:block;"
                >
            </div>

            <div class="litlas-unforgotten-name">
                {name}
            </div>

            <div class="litlas-unforgotten-short">
                {short}
            </div>

            <div class="litlas-unforgotten-book">
                {book}
            </div>

            <div class="litlas-unforgotten-divider"></div>

            <div class="litlas-unforgotten-reflection">
                {reflection}
            </div>

        </div>
        """

        cards.append(card)

    cards_html = "\n".join(cards)

    # -------------------------------------------------
    # Final section
    # -------------------------------------------------

    st.html(
        f"""
        <div class="litlas-unforgotten-section">

            <div class="litlas-unforgotten-header">
                <div class="litlas-unforgotten-title">
                    The Unforgotten
                </div>

                <div class="litlas-unforgotten-subtitle">
                    Some characters leave the page, but never leave us.
                </div>
            </div>

            <div class="litlas-unforgotten-grid">
                {cards_html}
            </div>

        </div>
        """
    )