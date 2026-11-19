"""On-demand, exportable reading postcard for a completed-book year."""

from functools import lru_cache
from io import BytesIO

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps
import streamlit as st

from litlas.processing.countries import (
    country_name,
    explored_country_codes,
    litlas_country_features,
)
from litlas.processing.paths import ILLUSTRATIONS_DIR


SIZE = (1440, 1060)
PAPER = "#f8f3e9"
INK = "#51392d"
MUTED = "#765d49"
GOLD = "#976338"
RULE = "#c9af91"


def dated_books(books):
    dates = pd.to_datetime(
        books["Date Read"].astype("string").str.strip().str.replace("/", "-", regex=False),
        format="%Y-%m-%d",
        errors="coerce",
    )
    return books.loc[dates.notna()].assign(finished=dates).sort_values("finished", kind="stable")


def new_countries(dated, year):
    first = dated.assign(code=dated["ISO3"].fillna("").str.strip().str.upper())
    first = first[first["code"].isin(explored_country_codes(first["code"]))]
    first = first.drop_duplicates("code")
    return first.loc[first["finished"].dt.year.eq(year), ["code", "Display Title"]]


@lru_cache(maxsize=24)
def _font(size, style=""):
    try:
        return ImageFont.truetype(f"DejaVuSerif{style}.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def _wrap(text, font, width, max_lines):
    lines = []
    remaining = " ".join(text.split())
    while remaining and len(lines) < max_lines:
        if font.getlength(remaining) <= width:
            lines.append(remaining)
            break
        end = 1
        while end < len(remaining) and font.getlength(remaining[:end + 1]) <= width:
            end += 1
        cut = remaining.rfind(" ", 0, end + 1)
        if cut > 0:
            end = cut
        line = remaining[:end]
        remaining = remaining[end:].lstrip()
        if len(lines) == max_lines - 1 and remaining:
            while font.getlength(line + "…") > width:
                line = line[:-1]
            line += "…"
        lines.append(line)
    return lines


@lru_cache(maxsize=1)
def _paper():
    image = Image.new("RGBA", SIZE, PAPER)
    with Image.open(ILLUSTRATIONS_DIR / "about-literary-margins-muted.png") as source:
        wash = ImageOps.fit(source.convert("RGBA"), SIZE, method=Image.Resampling.LANCZOS)
    wash.putalpha(wash.getchannel("A").point(lambda value: round(value * 0.26)))
    image.alpha_composite(wash)
    return image.convert("RGB")


def _draw_map(draw, codes):
    # The postcard uses the same country outlines and territory merges as Litlas.
    for feature in litlas_country_features():
        geometry = feature["geometry"]
        code = feature["properties"].get("ISO3166-1-Alpha-3")
        color = GOLD if code in codes else "#d7c8b2"
        polygons = geometry["coordinates"]
        if geometry["type"] == "Polygon":
            polygons = [polygons]
        for polygon in polygons:
            outline = [
                (782 + (lon + 180) * 1.48, 707 - lat * 1.48)
                for lon, lat in polygon[0]
            ]
            if len(outline) >= 3:
                draw.polygon(outline, fill=color, outline=PAPER)


def render_postcard(
    year, count, first_countries, longest, books, note, *, selected_books=False
):
    """Draw the preview and downloadable PNG from the same source."""
    image = _paper().copy()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, 1412, 1032), radius=8, outline=RULE, width=2)
    draw.text((80, 77), "LITLAS  /  A PERSONAL LITERARY ATLAS", font=_font(20), fill=MUTED)
    draw.ellipse((1225, 58, 1353, 186), outline=RULE, width=3)
    draw.ellipse((1234, 67, 1344, 177), outline=RULE, width=1)
    draw.text((1289, 122), str(year), anchor="mm", font=_font(29, "-Bold"), fill=GOLD)
    draw.text((720, 141), "A Year in Books", anchor="mt", font=_font(76, "-Italic"), fill=INK)
    draw.line((624, 248, 816, 248), fill=RULE, width=2)

    if note:
        lines = _wrap(f"“{note}”", _font(39, "-Italic"), 1060, 3)
        for index, line in enumerate(lines):
            draw.text((720, 295 + index * 53), line, anchor="mt", font=_font(39, "-Italic"), fill=INK)
    else:
        draw.text((720, 318), str(year), anchor="mt", font=_font(44), fill=MUTED)

    draw.line((80, 464, 1360, 464), fill=RULE, width=2)
    book_heading = "Books I’d Carry Forward" if selected_books else "Last Reads of the Year"
    draw.text((85, 506), book_heading, font=_font(37, "-Italic"), fill=INK)
    for index, (title, author) in enumerate(books):
        y = 569 + index * 85
        title_lines = _wrap(title, _font(27, "-Italic"), 620, 2)
        for line_no, line in enumerate(title_lines):
            draw.text((85, y + line_no * 27), line, font=_font(27, "-Italic"), fill=INK)
        author_line = _wrap(author, _font(20), 620, 1)
        if author_line:
            draw.text(
                (85, y + len(title_lines) * 27 + 2),
                author_line[0],
                font=_font(20),
                fill=MUTED,
            )

    draw.line((732, 506, 732, 863), fill=RULE, width=1)
    draw.text((778, 506), "New Places on the Map", font=_font(37, "-Italic"), fill=INK)
    _draw_map(draw, set(first_countries["code"]))
    countries = [country_name(code) for code in first_countries["code"]]
    if 0 < len(countries) <= 3:
        map_labels = [
            _wrap(f"{name} · {title}", _font(21), 565, 1)[0]
            for name, title in zip(countries, first_countries["Display Title"])
        ]
    else:
        names = " · ".join(countries) if countries else "No first reads from new countries recorded"
        map_labels = _wrap(names, _font(21), 565, 2)
    for index, line in enumerate(map_labels):
        draw.text((778, 814 + index * 22), line, font=_font(21), fill=MUTED)

    draw.line((80, 888, 1360, 888), fill=RULE, width=2)
    longest_title = "No page count recorded"
    if longest:
        title, pages = longest
        longest_title = f"{title} · {pages:,} pages"
    stats = [
        (85, "BOOKS FINISHED", str(count), 220),
        (332, "NEW COUNTRIES", str(len(countries)), 222),
        (582, "LONGEST READ", longest_title, 765),
    ]
    for x, label, value, width in stats:
        draw.text((x, 910), label, font=_font(17), fill=MUTED)
        draw.text((x, 944), _wrap(value, _font(28), width, 1)[0], font=_font(28), fill=INK)

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


@st.dialog("A Year in Books", width="large")
def show_year_postcard(read_books, page_details):
    dated = dated_books(read_books)
    years = sorted(dated["finished"].dt.year.unique().tolist(), reverse=True)
    if not years:
        st.info("No books with a recorded finish date yet.")
        return

    year = st.selectbox("Reading year", years, index=years.index(2025) if 2025 in years else 0)
    books = dated[dated["finished"].dt.year.eq(year)].copy()
    first = new_countries(dated, year)

    lengths = page_details[page_details["year"].astype(str).eq(str(year))].copy()
    lengths["pages"] = pd.to_numeric(lengths["pages"], errors="coerce")
    lengths = lengths[lengths["pages"].gt(0)].sort_values(
        ["pages", "title"], ascending=[False, True]
    )
    longest = (str(lengths.iloc[0]["title"]), int(lengths.iloc[0]["pages"])) if not lengths.empty else None

    options = {
        str(book_id): (str(title), str(author))
        for book_id, title, author in books[["Book Id", "Display Title", "Author"]].itertuples(index=False, name=None)
    }
    drafts = st.session_state.setdefault("litlas_postcard_drafts", {})
    previous_choices, previous_note = drafts.get(year, ([], ""))
    with st.expander("Personalize the postcard"):
        chosen = st.multiselect(
            "Books you’d carry forward",
            list(options),
            default=[book_id for book_id in previous_choices if book_id in options],
            max_selections=3,
            format_func=lambda book_id: " · ".join(options[book_id]),
            key=f"litlas_postcard_books_{year}",
        )
        note = st.text_input(
            "A line to remember",
            value=previous_note,
            max_chars=120,
            key=f"litlas_postcard_note_{year}",
        ).strip()
    drafts[year] = (chosen, note)

    entries = [options[book_id] for book_id in chosen] if chosen else list(options.values())[-3:][::-1]
    png = render_postcard(
        year, len(books), first, longest, entries, note, selected_books=bool(chosen)
    )
    st.image(png, width="stretch", caption=f"Litlas · {year}")
    st.download_button(
        "Download PNG",
        png,
        file_name=f"litlas-{year}-year-in-books.png",
        mime="image/png",
        on_click="ignore",
    )
