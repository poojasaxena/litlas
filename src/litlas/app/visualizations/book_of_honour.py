"""Antique Literary Book of Honour for Litlas."""

from html import escape

import streamlit as st
from textwrap import dedent
import base64
from litlas.processing.paths import ILLUSTRATIONS_DIR
from litlas.processing.paths import HONOUR_BOOK_BACKGROUND

def render_book_of_honour(authors):
    """Render the curated literary author collection as an antique open book."""

    categories = {
        1: ("❦", "Exceptional"),
        2: ("♥", "Favourites"),
        3: ("ღ", "Good authors"),
    }

    grouped = {
        tier: [
            escape(str(row["name"]))
            for row in authors
            if int(row["favourite_tier"]) == tier
        ]
        for tier in categories
    }

    def author_rows(tier):
        names = grouped[tier]

        if not names:
            return '<div class="honour-empty">No authors yet</div>'

        return "".join(
            f'<div class="honour-author">{name}</div>'
            for name in names
        )

    exceptional_count = len(grouped[1])
    favourites_count = len(grouped[2])
    good_count = len(grouped[3])

    st.markdown(
        """
        <style>
        .honour-book-wrap {
            display: flex;
            justify-content: center;
            margin: 12px 0 30px;
        }

        .honour-book {
            width: min(1000px, 95vw);
            max-width: none;
            flex-shrink: 0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            background: transparent;
            border: none;
            border-radius: 0;
            box-shadow: none;
            overflow: hidden;
        }

        .honour-page {
            position: relative;
            background:transparent;
            color: #58412F;
            font-family: Georgia, serif;
            padding: 18px 22px 20px;
        }

        .honour-page {
            min-height: 420px;
            box-sizing: border-box;
        }
                
        .honour-left-page {
            border-right: none;
            box-shadow: none;
        }

        .honour-right-page {
            box-shadow: none;
        }

        .honour-page::before {
            display: none;
        }

        .honour-page-inner {
            position: relative;
            z-index: 1;
            min-height: 480px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        /* Align Exceptional with the headings on the right page */
        .honour-left-page .honour-page-inner {
            transform: translateY(-30px);
        }
        .honour-symbol {
            text-align: center;
            font-size: 21px;
            color: #A47B43;
            margin-bottom: 2px;
        }

        .honour-heading {
            text-align: center;
            font-style: italic;
            font-size: 22px;
            color: #70472F;
            margin-bottom: 2px;
        }

        .honour-count {
            text-align: center;
            font-size: 12px;
            color: #8A735B;
            margin-bottom: 12px;
        }

        .honour-author {
            text-align: center;
            font-size: 15px;
            line-height: 1.45;
            color: #58412F;
            padding: 1px 0;
        }

        .honour-divider {
            text-align: center;
            color: #A47B43;
            margin: 12px 0 6px;
            letter-spacing: 5px;
            font-size: 12px;
        }

        .honour-empty {
            text-align: center;
            font-style: italic;
            color: #96785D;
            font-size: 14px;
            padding-top: 8px;
        }

        .honour-right-columns {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            align-items: start;
        }

        .honour-column {
            min-width: 0;
        }

        .honour-subheading {
            text-align: center;
            font-style: italic;
            font-size: 18px;
            color: #70472F;
            margin-bottom: 2px;
        }

        .honour-subcount {
            text-align: center;
            font-size: 11px;
            color: #8A735B;
            margin-bottom: 10px;
        }

        .honour-column .honour-author {
            font-size: 14px;
            line-height: 1.42;
        }


/* =====================================================
   MOBILE BOOK OF HONOUR — desktop remains unchanged
   ===================================================== */

/* Desktop is the default */
.honour-desktop {
    display: flex;
}

.honour-mobile {
    display: none;
}

@media screen and (max-width: 640px) {

    /* Show only the mobile book */
    .honour-desktop {
        display: none !important;
    }

    .honour-mobile {
        display: flex !important;
        justify-content: center;
        margin: 8px 0 16px;
    }

    /* Fixed two-page book */
    .honour-mobile .honour-book {
        width: min(430px, 96vw) !important;
        height: min(60vw, 260px) !important;

        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        grid-template-rows: minmax(0, 1fr) !important;

        overflow: hidden !important;
    }

    /* Both pages */
    .honour-mobile .honour-page {
        height: 100% !important;
        min-height: 0 !important;
        padding: 28px 12px 12px !important;
        box-sizing: border-box;
        overflow: hidden;
    }

    .honour-mobile .honour-page-inner {
        height: 100% !important;
        min-height: 0 !important;
        padding: 0 !important;
        transform: none !important;

        display: flex;
        flex-direction: column;
        justify-content: flex-start !important;
    }

    /* Right page — stack the categories naturally */
    .honour-mobile .honour-right-page .honour-page-inner {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        gap: 14px !important;
    }

    /* Each author category */
    .honour-mobile .honour-mobile-group {
        display: flex;
        flex-direction: column;
        min-height: 0;
        flex: 0 0 auto;
        overflow: hidden;
    }

    /* Symbol and heading share a single row */
    .honour-mobile .honour-mobile-title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        margin-bottom: 3px !important;
        flex-shrink: 0;
    }

    .honour-mobile .honour-mobile-symbol {
        font-size: 12px;
        line-height: 1;
        color: #A47B43;
    }

    .honour-mobile .honour-mobile-heading {
        font-family: Georgia, serif;
        font-size: 13px;
        font-style: italic;
        font-weight: 400;
        line-height: 1.2;
        color: #70472F;
    }

    /* Author counts */
    .honour-mobile .honour-count,
    .honour-mobile .honour-subcount {
        font-family: Georgia, serif;
        font-size: 10px !important;
        line-height: 1.2;
        color: #8A735B;
        text-align: center;
        margin-bottom: 5px !important;
        flex-shrink: 0;
    }

    /* Individual author names */
    .honour-mobile .honour-author {
        font-family: Georgia, serif;
        font-size: 9px !important;
        line-height: 1.3 !important;
        padding: 1px 0 !important;
        margin: 0 !important;
        color: #58412F;
        text-align: center;
    }

    /* All author lists scroll independently */
    .honour-mobile .honour-mobile-list {
        min-height: 0;
        overflow-y: auto;
        overflow-x: hidden;
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;

        scrollbar-width: thin;
        scrollbar-color: #D4C1A7 transparent;
    }

    /* Exceptional: use the available left-page space */
    .honour-mobile .honour-left-page .honour-mobile-list {
        flex: 1 1 auto;
    }

    /* Favourites + Good authors: exactly three visible rows */
    .honour-mobile .honour-right-page .honour-mobile-list {
        height: 42px !important;
        max-height: 42px !important;
        flex: 0 0 42px !important;
    }

}
        </style>
        """,
        unsafe_allow_html=True,
    )



    ## Load book background image and encode it as base64
    book_background = base64.b64encode(
        HONOUR_BOOK_BACKGROUND.read_bytes()).decode("ascii")


    html = f"""
    <div class="honour-book-wrap honour-desktop">
        <div class="honour-book" style="
            background-image: url('data:image/png;base64,{book_background}');
            background-size: 100% 100%;
            background-position: center;
            background-repeat: no-repeat;
        ">
            <div class="honour-page honour-left-page">
                <div class="honour-page-inner">
                    <div class="honour-symbol">❦</div>
                    <div class="honour-heading">Exceptional</div>
                    <div class="honour-count">{exceptional_count} author{"s" if exceptional_count != 1 else ""}</div>
                    {author_rows(1)}
                    <div class="honour-divider">✦ ❧ ✦</div>
                </div>
            </div>

            <div class="honour-page honour-right-page">
                <div class="honour-page-inner">
                    <div class="honour-right-columns">

                        <div class="honour-column">
                            <div class="honour-symbol">♥</div>
                            <div class="honour-subheading">Favourites</div>
                            <div class="honour-subcount">{favourites_count} author{"s" if favourites_count != 1 else ""}</div>
                            {author_rows(2)}
                            <div class="honour-divider">✦ ❧ ✦</div>
                        </div>

                        <div class="honour-column">
                            <div class="honour-symbol">ღ</div>
                            <div class="honour-subheading">Good authors</div>
                            <div class="honour-subcount">{good_count} author{"s" if good_count != 1 else ""}</div>
                            {author_rows(3)}
                            <div class="honour-divider">✦ ❧ ✦</div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    </div>
    """

    mobile_html = f"""
    <div class="honour-book-wrap honour-mobile">
        <div class="honour-book" style="
            background-image: url('data:image/png;base64,{book_background}');
            background-size: 100% 100%;
            background-position: center;
            background-repeat: no-repeat;
        ">

            <div class="honour-page honour-left-page">
                <div class="honour-page-inner">

                    <div class="honour-mobile-group">
                        <div class="honour-mobile-title-row">
                            <span class="honour-mobile-symbol">❦</span>
                            <span class="honour-mobile-heading">Exceptional</span>
                        </div>

                        <div class="honour-count">
                            {exceptional_count} authors
                        </div>

                        <div class="honour-mobile-list">
                            {author_rows(1)}
                            <div class="honour-divider">✦ ❧ ✦</div>
                        </div>
                    </div>

                </div>
            </div>

            <div class="honour-page honour-right-page">
                <div class="honour-page-inner">

                    <div class="honour-mobile-group">
                        <div class="honour-mobile-title-row">
                            <span class="honour-mobile-symbol">♥</span>
                            <span class="honour-mobile-heading">Favourites</span>
                        </div>

                        <div class="honour-subcount">
                            {favourites_count} authors
                        </div>

                        <div class="honour-mobile-list">
                            {author_rows(2)}
                        </div>
                    </div>

                    <div class="honour-mobile-group">
                        <div class="honour-mobile-title-row">
                            <span class="honour-mobile-symbol">ღ</span>
                            <span class="honour-mobile-heading">Good authors</span>
                        </div>

                        <div class="honour-subcount">
                            {good_count} authors
                        </div>

                        <div class="honour-mobile-list">
                            {author_rows(3)}
                        </div>
                    </div>

                </div>
            </div>

        </div>
    </div>
    """

    st.html(dedent(html) + dedent(mobile_html))