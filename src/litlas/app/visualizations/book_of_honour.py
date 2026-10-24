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

@media (max-width: 700px) {

    .honour-book-wrap {
        margin: 8px 0 20px;
    }

    .honour-book {
        width: min(430px, 96vw);
        max-width: none;
        grid-template-columns: 1fr 1fr !important;
        background-size: 100% 100% !important;
        background-position: center top !important;
        background-repeat: no-repeat !important;
    }

    .honour-page {
        padding: 14px 12px 16px !important;
        min-height: 0 !important;
    }

    .honour-page-inner {
        min-height: 0 !important;
        justify-content: flex-start !important;
    }

    /* Move Exceptional onto the left page a bit more cleanly */
    .honour-left-page .honour-page-inner {
        transform: translateX(-8px) translateY(20px) !important;
    }

    .honour-symbol {
        font-size: 14px !important;
        margin-bottom: 0 !important;
    }

    .honour-heading {
        font-size: 16px !important;
        margin-bottom: 2px !important;
    }

    .honour-count {
        font-size: 10px !important;
        margin-bottom: 8px !important;
    }

    .honour-author {
        font-size: 8px !important;
        line-height: 1.22 !important;
        padding: 0 !important;
    }

    .honour-divider {
        font-size: 8px !important;
        letter-spacing: 2px !important;
        margin: 7px 0 3px !important;
    }

    /* Right page: stack the two categories vertically */
    .honour-right-columns {
        grid-template-columns: 1fr !important;
        gap: 10px !important;
        align-items: start !important;
    }

    .honour-subheading {
        font-size: 14px !important;
        margin-bottom: 2px !important;
    }

    .honour-subcount {
        font-size: 9px !important;
        margin-bottom: 6px !important;
    }

    .honour-column .honour-author {
        font-size: 8px !important;
        line-height: 1.18 !important;
    }
}
        /* Compact Book of Honour on mobile only */
        @media screen and (max-width: 640px) {

            .honour-book-wrap {
                margin: 8px 0 16px;
            }

            .honour-page {
                min-height: 0;
                padding: 45px 20px 24px;
            }

            .honour-page-inner {
                min-height: 0;
                justify-content: flex-start;
            }

            .honour-left-page .honour-page-inner {
                transform: none;
            }

            .honour-right-columns {
                gap: 24px;
            }
        }

        /* Desktop: retain the original Book of Honour */
.honour-desktop {
    display: flex;
}

.honour-mobile {
    display: none;
}

/* Mobile: use the two-page continuation layout */
@media screen and (max-width: 640px) {

    .honour-desktop {
        display: none !important;
    }

    .honour-mobile {
        display: flex !important;
    }

    .honour-mobile .honour-book {
        width: min(430px, 96vw);
        grid-template-columns: 1fr 1fr !important;
    }

    .honour-mobile .honour-page {
        min-height: 0 !important;
        padding: 20px 12px !important;
    }

    .honour-mobile .honour-page-inner {
        min-height: 0 !important;
        transform: none !important;
        justify-content: flex-start !important;
    }

    /* Move Exceptional and left-page content slightly downward */
        .honour-mobile .honour-left-page {
            padding-top: 22px !important;
        }

    .honour-mobile .honour-author {
        font-size: 8px !important;
        line-height: 1.22 !important;
        padding: 0 !important;
    }

    .honour-mobile-favourites {
        margin-top: 4px;
    }

    .honour-mobile-continuation {
        margin-top: 3px;
    }

    .honour-mobile-good {
        margin-top: 0;
    }
}

.honour-mobile-title-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-bottom: 4px;
}

.honour-mobile-symbol {
    font-size: 14px;
    color: #A47B43;
    line-height: 1;
}

.honour-mobile-heading {
    font-style: italic;
    font-size: 12px;
    color: #70472F;
    line-height: 0.5;
}

/* Compact heading, count and author list */
.honour-mobile .honour-mobile-title-row {
    margin-bottom: 0 !important;
}

.honour-mobile .honour-count,
.honour-mobile .honour-subcount {
    margin-bottom: 2px !important;
}
/* Keep decorative stars close to the author lists */
.honour-mobile .honour-divider {
    margin-top: 1px !important;
    margin-bottom: 2px !important;
    padding: 0 !important;
    line-height: 1 !important;
}

/* Fixed-size, scrollable two-page mobile book */
@media screen and (max-width: 640px) {

    .honour-mobile .honour-book {
        width: min(430px, 96vw) !important;
        height: min(60vw, 260px) !important;
        grid-template-columns: 1fr 1fr !important;
        grid-template-rows: minmax(0, 1fr) !important;
    }

    .honour-mobile .honour-page {
        height: 100% !important;
        min-height: 0 !important;
        padding: 28px 12px 12px !important;
        overflow: hidden;
    }

    .honour-mobile .honour-page-inner {
        height: 100% !important;
        min-height: 0 !important;
        padding: 0 !important;
        transform: none !important;
        display: flex;
        flex-direction: column;
    }

    /* Left page: Exceptional */
    .honour-mobile .honour-left-page .honour-page-inner {
        justify-content: flex-start !important;
    }

    /* Right page: two equally allocated sections */
    .honour-mobile .honour-right-page .honour-page-inner {
        display: grid;
        grid-template-rows: minmax(0, 1fr) minmax(0, 1fr);
        gap: 6px;
    }

    .honour-mobile .honour-mobile-group {
        display: flex;
        flex-direction: column;
        min-height: 0;
        flex: 1;
        overflow: hidden;
    }

    /* Only the author lists scroll */
    .honour-mobile .honour-mobile-list {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        overflow-x: hidden;
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        scrollbar-color: #D4C1A7 transparent;
    }

    .honour-mobile .honour-author {
        font-size: 9px !important;
        line-height: 1.3 !important;
        padding: 1px 0 !important;
    }

    .honour-mobile .honour-mobile-title-row {
        flex-shrink: 0;
        margin-bottom: 3px !important;
    }

    .honour-mobile .honour-mobile-heading {
        font-size: 13px !important;
        line-height: 1.2 !important;
    }

    .honour-mobile .honour-count,
    .honour-mobile .honour-subcount {
        flex-shrink: 0;
        margin-bottom: 5px !important;
    }
    }

    @media (max-width: 900px) {

    .honour-page-inner.honour-mobile-right-page {
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        gap: 8px;
        min-height: 100%;
    }

    .honour-mobile-panel {
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        flex: 1 1 0;
        min-height: 0;
    }

    .honour-inline-heading {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        font-style: italic;
        font-size: 18px;
        color: #70472F;
        margin-bottom: 2px;
        line-height: 1.1;
    }

    .honour-inline-heading span {
        display: inline-block;
    }

    .honour-subcount {
        text-align: center;
        font-size: 11px;
        color: #8A735B;
        margin-bottom: 6px;
    }

    .honour-mobile-scroll {
        width: 100%;
        max-width: 140px;
        height: 20px;          /* main control: ~3 author lines visible */
        overflow-y: auto;
        overflow-x: hidden;
        text-align: center;
        padding-right: 2px;
        box-sizing: border-box;
    }

    .honour-mobile-scroll .honour-author {
        font-size: 12px;
        line-height: 1.3;
        padding: 0;
        margin: 0;
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
                    <div class="honour-page-inner honour-mobile-right-page">

                        <div class="honour-mobile-panel">
                            <div class="honour-inline-heading">♥ <span>Favourites</span></div>
                            <div class="honour-subcount">{favourites_count} authors</div>
                            <div class="honour-mobile-scroll">
                                {author_rows(2)}
                            </div>
                        </div>

                        <div class="honour-mobile-panel">
                            <div class="honour-inline-heading">ღ <span>Good authors</span></div>
                            <div class="honour-subcount">{good_count} authors</div>
                            <div class="honour-mobile-scroll">
                                {author_rows(3)}
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