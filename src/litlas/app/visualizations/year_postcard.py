"""On-demand, exportable reading postcard for a completed-book year."""

from functools import lru_cache
from io import BytesIO

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps, features
import streamlit as st

from litlas.app.ui import is_mobile_browser
from litlas.processing.countries import (
    explored_country_codes,
    litlas_country_features,
)
from litlas.processing.paths import ASSETS_DIR, ILLUSTRATIONS_DIR, load_config, resolve_project_path

# Preview and PNG dimensions.
DIALOG_WIDTH = 658
WIDTH = 1500
HEIGHT = 1680
CENTER_X = WIDTH // 2
CONTENT_MARGIN = 68
CONTENT_WIDTH = WIDTH - 2 * CONTENT_MARGIN

# Header artwork, yearly totals, and map.
LITLAS_LOGO_SIZE = (270, 200)
AUTHOR_LOGO_SIZE = (200, 200)
TITLE_ART_SIZE = (800, 100)
TITLE_FALLBACK_FONT_SIZE = 64
YEAR_FONT_SIZE = 62
HEADER_RULE_Y = 265
STATS_LABEL_Y = 299
STATS_VALUE_Y = 354
STATS_LABEL_SIZE = 32
STATS_VALUE_SIZE = 67
MAP_HEADING_Y = 443
MAP_TOP = 513
MAP_SCALE_X = 3.70
MAP_SCALE_Y = 3.75
MAP_MOVE_RIGHT = 0
MAP_MOVE_DOWN = 0

# Reading grid and footer.
BOOK_HEADING_Y = 1063
SECTION_HEADING_SIZE = 44
BOOK_HEADING_SIZE = SECTION_HEADING_SIZE
BOOK_TITLE_SIZE = 29
BOOK_AUTHOR_SIZE = 23
BOOK_COVER_SIZE = (270, 280)
BOOK_COVER_GAP = 82
BOOK_COVER_TOP = BOOK_HEADING_Y + 66
FOOTER_RULE_Y = 1483
FOOTER_RULE_WITH_NOTE_Y = 1460
FOOTER_LABEL_SIZE = 27
FOOTER_BOOK_SIZE = 33
FOOTER_UNIT_SIZE = 27
NOTE_FONT_SIZE = 21
NOTE_TOP = 1600
NOTE_LINE_SPACING = 23

## Book
BOOK_DATE_FONT_SIZE =23

BOOK_LIMIT = 4
PAPER = "#f5f1e6"
INK = "#533c30"
MUTED = "#6f5647"
GOLD = "#976338"
RULE = "#cdb699"
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
    filenames = {
        "": "NotoSerif-Regular.ttf",
        "-Italic": "NotoSerif-Italic.ttf",
        "-Bold": "NotoSerif-Bold.ttf",
    }

    filename = filenames.get(style)
    if filename is None:
        raise ValueError(f"Unsupported font style: {style}")

    return ImageFont.truetype(str(FONT_DIR / filename), size)

@lru_cache(maxsize=12)
def _devanagari_font(size):
    if not features.check("raqm"):
        raise RuntimeError(
            "RAQM is required for correct Devanagari rendering"
        )

    return ImageFont.truetype(
        str(FONT_DIR / "NotoSerifDevanagari-Regular.ttf"),
        size,
        layout_engine=ImageFont.Layout.RAQM,
    )

def _book_font(text, size, style=""):
    if any("\u0900" <= char <= "\u097f" for char in text):
        return _devanagari_font(size)
    return _font(size, style)

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
    return ImageOps.contain(title.crop(bounds), TITLE_ART_SIZE, Image.Resampling.LANCZOS)


@lru_cache(maxsize=3)
def _logo_art(path, size, *, alpha_threshold=0):
    with Image.open(path) as source:
        logo = source.convert("RGBA")
    alpha = logo.getchannel("A")
    if alpha_threshold:
        alpha = alpha.point(lambda value: 255 if value > alpha_threshold else 0)
    bounds = alpha.getbbox()
    if bounds:
        logo = logo.crop(bounds)
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
def _paper():
    size = (WIDTH, HEIGHT)
    image = Image.new("RGBA", size, PAPER)

    with Image.open(ILLUSTRATIONS_DIR / "about-literary-margins-muted.png") as source:
        wash = ImageOps.contain(
            source.convert("RGBA"),
            size,
            method=Image.Resampling.LANCZOS,
        )

    background_lift = 30
    wash.putalpha(wash.getchannel("A").point(lambda value: round(value * 0.28)))
    image.alpha_composite(
        wash,
        dest=(0, HEIGHT - wash.height - background_lift),
    )
    return image.convert("RGB")


def _draw_map(draw, codes):
    # The postcard uses the same country outlines and territory merges as Litlas.
    for feature in litlas_country_features():
        geometry = feature["geometry"]
        code = feature["properties"].get("ISO3166-1-Alpha-3")
        if code == "ATA":
            continue
        color = GOLD if code in codes else "#d7c8b2"
        polygons = geometry["coordinates"]
        if geometry["type"] == "Polygon":
            polygons = [polygons]
        for polygon in polygons:
            outline = [
                (
                    CENTER_X + MAP_MOVE_RIGHT + lon * MAP_SCALE_X,
                    MAP_TOP + MAP_MOVE_DOWN + (84 - lat) * MAP_SCALE_Y,
                )
                for lon, lat in polygon[0]
            ]
            if len(outline) >= 3:
                draw.polygon(outline, fill=color, outline=PAPER)


def _draw_length(draw, center, width, top, label, book):
    draw.text(
        (center, top), label,
        anchor="mt",
        font=_font(FOOTER_LABEL_SIZE),
        fill=MUTED,
    )

    if book is None:
        draw.text(
            (center, top + 48), "No page count recorded",
            anchor="mt",
            font=_font(FOOTER_UNIT_SIZE),
            fill=MUTED,
        )
        return

    title, author, pages = book

    title_font = _book_font(title, FOOTER_BOOK_SIZE, "-Italic")
    lines = _wrap(title, title_font, width, 2)

    for index, line in enumerate(lines):
        draw.text(
            (center, top + 38 + index * 34),
            line,
            anchor="mt",
            font=title_font,
            fill=INK,
        )

    next_y = top + 38 + len(lines) * 34 + 6

    if author:
        author_font = _book_font(author, 23)
        author_line = _wrap(author, author_font, width, 1)
        if author_line:
            draw.text(
                (center, next_y),
                author_line[0],
                anchor="mt",
                font=author_font,
                fill=MUTED,
            )
        next_y += 34

    draw.text(
        (center, next_y),
        f"{pages:,} pages",
        anchor="mt",
        font=_font(FOOTER_UNIT_SIZE),
        fill=MUTED,
    )

def _draw_rating_stars(draw, center, top, rating):
    size, gap = 21, 3
    star = Image.new("L", (17, 17))
    ImageDraw.Draw(star).polygon(
        [(8, 0), (10, 6), (16, 6), (11, 10), (13, 16),
        (8, 12), (3, 16), (5, 10), (0, 6), (6, 6)],
        fill=255,
    )
    star = star.resize((size, size), Image.Resampling.LANCZOS)

    left = round(center - (5 * size + 4 * gap) / 2)
    for index in range(5):
        x = left + index * (size + gap)
        draw.bitmap((x, top), star, fill="#D8CDBC")

        filled = round(size * max(0, min(1, rating - index)))
        if filled:
            draw.bitmap(
                (x, top), star.crop((0, 0, filled, size)), fill="#BC861E"
            )


def _draw_header(image, draw, year):
    logo = _logo_art(ILLUSTRATIONS_DIR / "litlas_logo.png", LITLAS_LOGO_SIZE)
    image.paste(logo, (CONTENT_MARGIN, 42), logo)

    author_logo = _logo_art(ASSETS_DIR / "branding" / "author_logo.png", AUTHOR_LOGO_SIZE)
    author_x = WIDTH - CONTENT_MARGIN - author_logo.width
    author_y = 42 + (logo.height - author_logo.height) // 2
    image.paste(author_logo, (author_x, author_y), author_logo)

    title = _title_art()
    if title is None:
        draw.text(
            (CENTER_X, 75), "A Year in Books", anchor="mt",
            font=_heading_font(TITLE_FALLBACK_FONT_SIZE), fill=INK,
        )
    else:
        image.paste(title, ((WIDTH - title.width) // 2, 106 - title.height // 2), title)

    draw.line((CENTER_X - 88, 158, CENTER_X + 88, 158), fill=RULE, width=2)
    _draw_number(draw, (CENTER_X, 187), str(year), YEAR_FONT_SIZE, anchor="mt")
    draw.line(
        (CONTENT_MARGIN, HEADER_RULE_Y, WIDTH - CONTENT_MARGIN, HEADER_RULE_Y),
        fill=RULE, width=2,
    )


def _draw_totals(draw, count, country_count, pages_read):
    label_font = _font(STATS_LABEL_SIZE)
    for filename in ("Georgia.ttf", "georgia.ttf"):
        try:
            value_font = ImageFont.truetype(filename, STATS_VALUE_SIZE)
            break
        except OSError:
            continue
    totals = (
        ("Books finished", count),
        ("New countries", country_count),
        ("Pages read", pages_read),
    )
    for index, (label, value) in enumerate(totals):
        center = CONTENT_MARGIN + CONTENT_WIDTH * (index + 0.5) / len(totals)
        draw.text((center, STATS_LABEL_Y), label, anchor="mt", font=label_font, fill=MUTED)
        _draw_number(
            draw,
            (center, STATS_VALUE_Y),
            f"{value:,}" if value is not None else "—",
            STATS_VALUE_SIZE,
            anchor="mt",
        )


def _draw_books(image, draw, books, selected_books):
    heading = "Books I’d Carry Forward" if selected_books else "Treasured Reads"
    draw.text(
        (CENTER_X, BOOK_HEADING_Y), heading, anchor="mt",
        font=_heading_font(BOOK_HEADING_SIZE), fill=INK,
    )
    entries = books[:BOOK_LIMIT]
    if not entries:
        draw.text(
            (CENTER_X, BOOK_COVER_TOP), "No rated books recorded this year",
            anchor="mt", font=_font(BOOK_AUTHOR_SIZE), fill=MUTED,
        )
        return

    outline_path = ILLUSTRATIONS_DIR / "book_outline.png"
    cover = (
        _logo_art(outline_path, BOOK_COVER_SIZE, alpha_threshold=16)
        if outline_path.is_file() else None
    )
    cover_width, cover_height = cover.size if cover is not None else (184, BOOK_COVER_SIZE[1])
    row_width = len(entries) * cover_width + (len(entries) - 1) * BOOK_COVER_GAP
    row_left = (WIDTH - row_width) // 2
    text_width = cover_width - 26
    author_step = BOOK_AUTHOR_SIZE + 2

    for index, (title, author, rating, finished) in enumerate(entries):
        left = row_left + index * (cover_width + BOOK_COVER_GAP)
        cover_center = left + cover_width / 2
        text_center = cover_center + 4
        if cover is not None:
            image.paste(cover, (left, BOOK_COVER_TOP), cover)
        else:
            draw.rounded_rectangle(
                (left, BOOK_COVER_TOP, left + cover_width, BOOK_COVER_TOP + cover_height),
                radius=8, outline=RULE, width=2,
            )

        for title_size in (BOOK_TITLE_SIZE, BOOK_TITLE_SIZE - 3, BOOK_TITLE_SIZE - 6):
            title_font = _book_font(title, title_size, "-Italic")
            title_lines = _wrap(title, title_font, text_width, 4)
            if " ".join(title_lines) == " ".join(title.split()):
                break
        title_step = title_size + 3
        author_font = _book_font(author, BOOK_AUTHOR_SIZE)
        author_lines = _wrap(author, author_font, text_width, 2)
        gap = 16 if title_lines and author_lines else 0
        author_date_gap = 4
        
        text_height = len(title_lines) * title_step + gap + len(author_lines) * author_date_gap

        date_text = finished.strftime("%d %b %Y").lstrip("0") if pd.notna(finished) else ""
        date_font = _font(BOOK_DATE_FONT_SIZE)
        author_date_gap = 22

        if date_text:
            text_height += author_date_gap + date_font.size

        y = BOOK_COVER_TOP + (cover_height - text_height) / 2
        for line in title_lines:
            draw.text((text_center, y), line, anchor="mt", font=title_font, fill=INK)
            y += title_step
        y += gap

        for line in author_lines:
            draw.text((text_center, y), line, anchor="mt", font=author_font, fill=MUTED)
            y += author_date_gap

        if date_text:
            draw.text(
                (text_center, y + author_date_gap),
                date_text,
                anchor="mt",
                font=date_font,
                fill=MUTED,
            )

        if pd.notna(rating) and rating > 0:
            _draw_rating_stars(draw, cover_center, BOOK_COVER_TOP + cover_height + 9, rating)


def render_postcard(
    year, count, first_countries, shortest, longest, books, note, *,
    selected_books=False, pages_read=None, year_countries=None,
):
    """Draw the preview and downloadable PNG at the same fixed aspect ratio."""
    image = _paper().copy()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, WIDTH - 24, HEIGHT - 24), radius=8, outline=RULE, width=2)

    _draw_header(image, draw, year)
    _draw_totals(draw, count, len(first_countries), pages_read)
    draw.text(
        (CENTER_X, MAP_HEADING_Y), "Litlas Landscapes", anchor="mt",
        font=_heading_font(SECTION_HEADING_SIZE), fill=INK,
    )
    _draw_map(draw, year_countries if year_countries is not None else set(first_countries["code"]))
    _draw_books(image, draw, books, selected_books)

    note_font = _font(NOTE_FONT_SIZE, "-Italic")
    note_lines = _wrap(f"“{note}”", note_font, CONTENT_WIDTH, 2) if note else []
    footer_width = CONTENT_WIDTH // 2
    footer_top = FOOTER_RULE_WITH_NOTE_Y if note_lines else FOOTER_RULE_Y
    draw.line((CONTENT_MARGIN, footer_top, WIDTH - CONTENT_MARGIN, footer_top), fill=RULE, width=2)
    for center, label, book in (
        (CENTER_X - footer_width / 2, "Longest read", longest),
        (CENTER_X + footer_width / 2, "Shortest read", shortest),
    ):
        _draw_length(draw, center, footer_width - 32, footer_top + 17, label, book)
    for index, line in enumerate(note_lines):
        draw.text(
            (CENTER_X, NOTE_TOP + index * NOTE_LINE_SPACING), line,
            anchor="mt", font=note_font, fill=INK,
        )

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _reading_page_summary(page_details, year):
    lengths = page_details.loc[page_details["year"].astype(str).eq(str(year)), ["title", "pages"]].copy()
    lengths["pages"] = pd.to_numeric(lengths["pages"], errors="coerce")
    lengths = lengths.loc[lengths["pages"].gt(0) & lengths["pages"].lt(float("inf"))]
    lengths = lengths.sort_values("title", kind="stable").reset_index(drop=True)
    if lengths.empty:
        return None, None, None

    shortest = lengths.loc[lengths["pages"].idxmin()]
    longest = lengths.loc[lengths["pages"].idxmax()]
    return (
        (str(shortest["title"]), int(shortest["pages"])),
        (str(longest["title"]), int(longest["pages"])),
        int(lengths["pages"].sum()),
    )


def reading_lengths(page_details, year):
    shortest, longest, _ = _reading_page_summary(page_details, year)
    return shortest, longest


def highest_rated_books(books):
    ratings = pd.to_numeric(books["My Rating"], errors="coerce")
    rated = books.loc[ratings.gt(0)].assign(rating=ratings)
    ranked = rated.sort_values(
        ["rating", "finished"],
        ascending=[False, True],
    )
    return list(
        ranked.head(BOOK_LIMIT)[["Display Title", "Author", "rating", "finished"]]
        .itertuples(index=False, name=None)
    )


@st.dialog("A Year in Books", width=DIALOG_WIDTH)
def show_year_postcard(read_books, page_details):
    dated = dated_books(read_books)
    years = sorted(dated["finished"].dt.year.unique().tolist(), reverse=True)
    if not years:
        st.info("No books with a recorded finish date yet.")
        return

    mobile = is_mobile_browser()
    controls = st.container(key="litlas_postcard_controls")
    year_col, personalize_col, download_col = controls.columns(
        3,
        gap="small",
        vertical_alignment="bottom",
    )

    year = year_col.selectbox(
        "Reading year",
        years,
        index=years.index(2025) if 2025 in years else 0,
        key="litlas_postcard_year",
        label_visibility="collapsed",
    )

    books = dated[dated["finished"].dt.year.eq(year)].copy()
    first = new_countries(dated, year)
    year_countries = explored_country_codes(books["ISO3"])

    shortest, longest, pages_read = _reading_page_summary(page_details, year)
    authors_by_title = {}

    for _, row in books.iterrows():
        author = row.get("Author")

        if pd.isna(author):
            continue

        for column in ("Display Title", "Title"):
            if column in books.columns and pd.notna(row[column]):
                key = " ".join(str(row[column]).split()).casefold()
                authors_by_title[key] = str(author)


    def add_author(book):
        if book is None:
            return None

        title, pages = book
        key = " ".join(title.split()).casefold()

        return title, authors_by_title.get(key, ""), pages


    shortest = add_author(shortest)
    longest = add_author(longest)

    preview = st.empty()
  

    rated_options = books.assign(
        rating=pd.to_numeric(books["My Rating"], errors="coerce")
    )
    options = {
        str(book_id): (str(title), str(author), rating, finished)
        for book_id, title, author, rating, finished in rated_options[
            ["Book Id", "Display Title", "Author", "rating", "finished"]
        ].itertuples(index=False, name=None)
    }
    drafts = st.session_state.setdefault("litlas_postcard_drafts", {})
    previous_choices, previous_note = drafts.get(year, ([], ""))

    with personalize_col.popover(
        "Personalize" if mobile else "Personalize the postcard",
        width="stretch",
    ):
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
        year, len(books), first, shortest, longest, entries, note,
        selected_books=bool(chosen),
        pages_read=pages_read,
        year_countries=year_countries,
    )
    preview.image(png, width="stretch")
    download_col.download_button(
        "Download" if mobile else "Download PNG",
        png,
        file_name=f"litlas-{year}-year-in-books.png",
        mime="image/png",
        on_click="ignore",
        width="stretch",
    )
