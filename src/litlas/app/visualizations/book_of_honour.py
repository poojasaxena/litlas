"""Antique Literary Book of Honour for Litlas."""

from html import escape

import streamlit as st
from textwrap import dedent

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
            width: min(1250px, 95vw);
            max-width: none;
            flex-shrink: 0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            background: #d6c0a0;
            border: 7px solid #7b5942;
            border-radius: 14px;
            box-shadow: 0 10px 24px rgba(65, 40, 22, 0.18);
            overflow: hidden;
        }

        .honour-page {
            position: relative;
            background:
                linear-gradient(
                    100deg,
                    #ead9bd 0%,
                    #faf1df 14%,
                    #f8efdc 84%,
                    #e6d3b2 100%
                );
            color: #58412F;
            font-family: Georgia, serif;
            padding: 18px 22px 20px;
        }

        .honour-page {
            min-height: 400px;
            box-sizing: border-box;
        }
                
        .honour-left-page {
            border-right: 2px solid #b79b74;
            box-shadow: inset -10px 0 16px rgba(120, 90, 55, 0.08);
        }

        .honour-right-page {
            box-shadow: inset 10px 0 16px rgba(120, 90, 55, 0.08);
        }

        .honour-page::before {
            content: "";
            position: absolute;
            inset: 10px;
            border: 1px solid rgba(164, 123, 67, 0.42);
            pointer-events: none;
        }

        .honour-page-inner {
            position: relative;
            z-index: 1;
            min-height: 490px;
            display: flex;
            flex-direction: column;
            justify-content: center;
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

        @media (max-width: 900px) {
            .honour-book {
                grid-template-columns: 1fr;
            }

            .honour-left-page {
                border-right: none;
                border-bottom: 2px solid #b79b74;
                box-shadow: inset 0 -8px 14px rgba(120, 90, 55, 0.08);
            }

            .honour-right-page {
                box-shadow: inset 0 8px 14px rgba(120, 90, 55, 0.08);
            }
        }

        @media (max-width: 700px) {
            .honour-right-columns {
                grid-template-columns: 1fr;
                gap: 14px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    html = f"""
    <div class="honour-book-wrap">
        <div class="honour-book">
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