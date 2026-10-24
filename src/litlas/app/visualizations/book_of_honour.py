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
        transform: translateX(-8px) translateY(-6px) !important;
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
        </style>
        """,
        unsafe_allow_html=True,
    )



    ## Load book background image and encode it as base64
    book_background = base64.b64encode(
        HONOUR_BOOK_BACKGROUND.read_bytes()).decode("ascii")


    html = f"""
    <div class="honour-book-wrap">
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

    st.html(dedent(html))