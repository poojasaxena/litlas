"""On-demand, exportable reading postcard for a completed-book year."""

from functools import lru_cache
from io import BytesIO

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps, features
import streamlit as st

from litlas.processing.countries import (
    country_name,
    explored_country_codes,
    litlas_country_features,
)
from litlas.processing.paths import ASSETS_DIR, ILLUSTRATIONS_DIR, load_config, resolve_project_path


WIDTH = 1440
BODY_TOP = 265
FOOTER_TOP = BODY_TOP + 530
FOOTER_LABEL_Y = FOOTER_TOP + 22
FOOTER_VALUE_Y = FOOTER_TOP + 80
BASE_HEIGHT = FOOTER_TOP + 165
BOOK_LIMIT = 4
PAPER = "#f8f3e9"
INK = "#51392d"
MUTED = "#765d49"
GOLD = "#976338"
RULE = "#c9af91"
FIGURE_INK = "#6E4B3A"
FONT_DIR = ASSETS_DIR / "fonts"


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
    if style == "-Italic":
        try:
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/msttcorefonts/Georgia_Italic.ttf",
                size,
            )
        except OSError:
            pass

    try:
        return ImageFont.truetype(f"DejaVuSerif{style}.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


@lru_cache(maxsize=4)
def _heading_font(size):
    return ImageFont.truetype(FONT_DIR / "NotoSerifDisplay-BoldItalic.ttf", size)


@lru_cache(maxsize=8)
def _figure_font(size):
    for filename in ("georgiab.ttf", "Georgia Bold.ttf"):
        try:
            return ImageFont.truetype(filename, size), None
        except OSError:
            continue
    font = ImageFont.truetype(FONT_DIR / "NotoSerif-Numerals.ttf", size)
    return font, ["onum"] if features.check_feature("raqm") else None


def _draw_number(draw, position, value, size, *, anchor="rs"):
    font, font_features = _figure_font(size)
    draw.text(
        position, value, font=font, features=font_features,
        anchor=anchor, fill=FIGURE_INK,
    )


@lru_cache(maxsize=1)
def _title_art():
    configured_path = load_config().get("branding", {}).get("year_postcard_title")
    if not configured_path:
        return None
    path = resolve_project_path(configured_path)
    if not path.is_file():
        return None

    from resvg_py import svg_to_bytes

    svg = path.read_text(encoding="utf-8").replace("#000000", "#58412F")
    with Image.open(BytesIO(bytes(svg_to_bytes(svg_string=svg, width=1000)))) as source:
        title = source.convert("RGBA")
    bounds = title.getchannel("A").getbbox()
    if bounds is None:
        return None
    return ImageOps.contain(title.crop(bounds), (750, 61), Image.Resampling.LANCZOS)


@lru_cache(maxsize=2)
def _logo_art(path, size):
    with Image.open(path) as source:
        logo = source.convert("RGBA")
    logo = logo.crop(logo.getchannel("A").getbbox())
    return ImageOps.contain(logo, size, Image.Resampling.LANCZOS)


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


@lru_cache(maxsize=2)
def _paper(height):
    size = (WIDTH, height)
    image = Image.new("RGBA", size, PAPER)
    with Image.open(ILLUSTRATIONS_DIR / "about-literary-margins-muted.png") as source:
        wash = ImageOps.fit(source.convert("RGBA"), size, method=Image.Resampling.LANCZOS)
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
                (648 + (lon + 180) * 1.94, BODY_TOP + 205 - lat * 1.94)
                for lon, lat in polygon[0]
            ]
            if len(outline) >= 3:
                draw.polygon(outline, fill=color, outline=PAPER)


def _draw_length(draw, 
                 x, 
                 width, 
                 label, 
                 book):
    center = x + width / 2
    draw.text((center, FOOTER_LABEL_Y), label, anchor="mt", font=_font(17), fill=MUTED)
    title_font = _font(23, "-Italic")
    if book is None:
        draw.text((x, FOOTER_TOP + 61), "No page count recorded", anchor="ls", font=title_font, fill=INK)
        return

    title, pages = book
    page_text = f"{pages:,}"
    number_font, number_features = _figure_font(23)
    number_width = draw.textlength(page_text, font=number_font, features=number_features)
    unit_font = _font(20)
    separator = " · "
    suffix_width = (
        draw.textlength(separator, font=unit_font) + number_width
        + draw.textlength(" pages", font=unit_font)
    )
    lines = _wrap(title, title_font, width, 2)
    if lines and draw.textlength(lines[-1], font=title_font) + suffix_width > width:
        lines = _wrap(title, title_font, width - suffix_width, 2)

    baseline = FOOTER_VALUE_Y

    for line in lines[:-1]:
        draw.text((center, baseline), line, anchor="ms", font=title_font, fill=INK)
        baseline += 25

    last_line = lines[-1] if lines else ""
    title_width = draw.textlength(last_line, font=title_font)
    title_x = center - (title_width + suffix_width) / 2

    draw.text((title_x, baseline), last_line, anchor="ls", font=title_font, fill=INK)
    suffix_x = title_x + title_width
    draw.text((suffix_x, baseline), separator, anchor="ls", font=unit_font, fill=MUTED)
    number_x = suffix_x + draw.textlength(separator, font=unit_font)
    _draw_number(draw, (number_x, baseline), page_text, 23, anchor="ls")
    draw.text((number_x + number_width, baseline), " pages", anchor="ls", font=unit_font, fill=MUTED)

def _draw_rating_stars(draw, right, top, rating):
    size, gap = 17, 2
    star = Image.new("L", (size, size))
    ImageDraw.Draw(star).polygon(
        [(8, 0), (10, 6), (16, 6), (11, 10), (13, 16),
         (8, 12), (3, 16), (5, 10), (0, 6), (6, 6)],
        fill=255,
    )

    left = right - (5 * size + 4 * gap)
    for index in range(5):
        x = left + index * (size + gap)
        draw.bitmap((x, top), star, fill="#D8CDBC")

        filled = round(size * max(0, min(1, rating - index)))
        if filled:
            draw.bitmap(
                (x, top), star.crop((0, 0, filled, size)), fill="#BC861E"
            )


def render_postcard(
    year, count, first_countries, shortest, longest, books, note, *, selected_books=False
):
    """Draw the preview and downloadable PNG from the same source."""
    note_font = _font(24, "-Italic")
    note_lines = _wrap(f"“{note}”", note_font, 1260, 2) if note else []
    height = BASE_HEIGHT + (28 + 30 * len(note_lines) if note_lines else 0)
    image = _paper(height).copy()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, WIDTH - 24, height - 24), radius=8, outline=RULE, width=2)

    center = WIDTH // 2
    logo = _logo_art(ILLUSTRATIONS_DIR / "litlas_logo.png", (225, 175))
    image.paste(logo, (68, 42), logo)

    author_logo = _logo_art(ASSETS_DIR / "branding" / "author_logo.png", (155, 155))
    author_x = WIDTH - 68 - author_logo.width
    author_y = 42 + (logo.height - author_logo.height) // 2
    image.paste(author_logo, (author_x, author_y), author_logo)

    ## Render the header section with title and year
    header_shift = 16
    title = _title_art()

    if title is None:
        draw.text(
            (center, 53 + header_shift),
            "A Year in Books",
            anchor="mt",
            font=_heading_font(55),
            fill=INK,
        )
    else:
        title_x = (WIDTH - title.width) // 2
        title_y = 83 - title.height // 2 + header_shift
        image.paste(title, (title_x, title_y), title)

    rule_y = 129 + header_shift
    draw.line((center - 88, rule_y, center + 88, rule_y), fill=RULE, width=2)
    _draw_number(draw, (center, 150 + header_shift), str(year), 36, anchor="mt")
    # draw.line((center - 88, 129, center + 88, 129), fill=RULE, width=2)
    # _draw_number(draw, (center, 150), str(year), 36, anchor="mt")
    # draw.ellipse((1261, 44, 1345, 128), outline=RULE, width=2)
    # draw.ellipse((1267, 50, 1339, 122), outline=RULE, width=1)
    #_draw_number(draw, (1303, 86), str(year), 27, anchor="mm")
    draw.line((68, BODY_TOP - 15, WIDTH - 68, BODY_TOP - 15), fill=RULE, width=2)

    book_heading = "Books I’d Carry Forward" if selected_books else "Highest-Rated Reads"
    draw.text((68, BODY_TOP), book_heading, font=_heading_font(31), fill=INK)
    if not books:
        draw.text((68, BODY_TOP + 45), "No rated books recorded this year", font=_font(22), fill=MUTED)

    ## Render the list of books
    for index, (title, author, rating) in enumerate(books):
        y = BODY_TOP + 72 + index * 108
        title_lines = _wrap(title, _font(25, "-Italic"), 385, 2)

        if pd.notna(rating) and rating > 0:
            _draw_rating_stars(draw, 562, y + 4, rating)

        for line_no, line in enumerate(title_lines):
            draw.text((68, y + line_no * 26), line, font=_font(25, "-Italic"), fill=INK)
        for author_line in _wrap(author, _font(20), 490, 1):
            draw.text((68, y + len(title_lines) * 26 + 1), author_line, font=_font(20), fill=MUTED)

    draw.line((590, BODY_TOP + 2, 590, FOOTER_TOP - 20), fill=RULE, width=1)
    draw.text((752, BODY_TOP), "New Places on the Map", font=_heading_font(31), fill=INK)

    ## Render the map of new countries
    _draw_map(draw, set(first_countries["code"]))
    countries = [country_name(code) for code in first_countries["code"]]
    if 0 < len(countries) <= 3:
        map_labels = [
            _wrap(f"{name} · {title}", _font(20), 608, 1)[0]
            for name, title in zip(countries, first_countries["Display Title"])
        ]
    else:
        names = " · ".join(countries) if countries else "No first reads from new countries recorded"
        map_labels = _wrap(names, _font(20), 608, 2)
    for index, line in enumerate(map_labels):
        draw.text((752, BODY_TOP + 352 + index * 28), line, font=_font(20), fill=MUTED)

    draw.line((68, FOOTER_TOP, WIDTH - 68, FOOTER_TOP), fill=RULE, width=2)

    ## Render the footer statistics
    for x, label, value in (
        (158, "BOOKS FINISHED", count),
        (345, "NEW COUNTRIES", len(countries)),
    ):
        draw.text((x, FOOTER_LABEL_Y), label, anchor="mt", font=_font(17), fill=MUTED)
        _draw_number(draw, (x, FOOTER_VALUE_Y), f"{value:,}", 30, anchor="ms")

    _draw_length(draw, 433, 430, "LONGEST READ", longest)
    _draw_length(draw, 901, 471, "SHORTEST READ", shortest)

    if note_lines:
        draw.line((68, BASE_HEIGHT - 17, WIDTH - 68, BASE_HEIGHT - 17), fill=RULE, width=1)
        for index, line in enumerate(note_lines):
            draw.text((center, BASE_HEIGHT - 4 + index * 30), line, anchor="mt", font=note_font, fill=INK)

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def reading_lengths(page_details, year):
    lengths = page_details.loc[page_details["year"].astype(str).eq(str(year)), ["title", "pages"]].copy()
    lengths["pages"] = pd.to_numeric(lengths["pages"], errors="coerce")
    lengths = lengths.loc[lengths["pages"].gt(0)].sort_values("title", kind="stable")
    lengths = lengths.reset_index(drop=True)
    if lengths.empty:
        return None, None

    shortest = lengths.loc[lengths["pages"].idxmin()]
    longest = lengths.loc[lengths["pages"].idxmax()]
    return (str(shortest["title"]), int(shortest["pages"])), (str(longest["title"]), int(longest["pages"]))


def highest_rated_books(books):
    ratings = pd.to_numeric(books["My Rating"], errors="coerce")
    rated = books.loc[ratings.gt(0)].assign(rating=ratings)
    ranked = rated.sort_values(["rating", "finished"], ascending=False)
    return list(
        ranked.head(BOOK_LIMIT)[["Display Title", "Author", "rating"]]
        .itertuples(index=False, name=None)
    )

@st.dialog("A Year in Books", width=780)
def show_year_postcard(read_books, page_details):
    dated = dated_books(read_books)
    years = sorted(dated["finished"].dt.year.unique().tolist(), reverse=True)
    if not years:
        st.info("No books with a recorded finish date yet.")
        return

    year = st.selectbox("Reading year", years, index=years.index(2025) if 2025 in years else 0)
    books = dated[dated["finished"].dt.year.eq(year)].copy()
    first = new_countries(dated, year)

    shortest, longest = reading_lengths(page_details, year)
    preview = st.empty()
    download = st.empty()

    rated_options = books.assign(
        rating=pd.to_numeric(books["My Rating"], errors="coerce")
    )
    options = {
        str(book_id): (str(title), str(author), rating)
        for book_id, title, author, rating in rated_options[
            ["Book Id", "Display Title", "Author", "rating"]
        ].itertuples(index=False, name=None)
    }
    drafts = st.session_state.setdefault("litlas_postcard_drafts", {})
    previous_choices, previous_note = drafts.get(year, ([], ""))

    with st.expander("Personalize the postcard"):
        chosen = st.multiselect(
            "Books you’d carry forward",
            list(options),
            default=[book_id for book_id in previous_choices if book_id in options][:BOOK_LIMIT],
            max_selections=BOOK_LIMIT,
            format_func=lambda book_id: " · ".join(options[book_id][:2]),
            key=f"litlas_postcard_books_{year}",
        )
        note = st.text_input(
            "A line to remember",
            value=previous_note,
            max_chars=120,
            key=f"litlas_postcard_note_{year}",
        ).strip()
    drafts[year] = (chosen, note)

    entries = [options[book_id] for book_id in chosen] if chosen else highest_rated_books(books)
    png = render_postcard(
        year, len(books), first, shortest, longest, entries, note, selected_books=bool(chosen)
    )
    preview.image(png, width="stretch")
    download.download_button(
        "Download PNG",
        png,
        file_name=f"litlas-{year}-year-in-books.png",
        mime="image/png",
        on_click="ignore",
    )
