
"""Form for adding books independently of Goodreads."""

import streamlit as st
import pycountry
from html import escape

from litlas.app.library.book_editor import RATING_OPTIONS
from litlas.app.library.author_details import find_author_matches
from litlas.processing.countries import COUNTRY_DISPLAY_NAMES, country_name
from litlas.db_backend import connect, get_repository

add_book = get_repository().add_book

def render_add_book():
    """Render the Add a Book workspace."""

    with connect() as db:
        authors = db.execute(
            "SELECT id, name FROM authors ORDER BY LOWER(name), name"
        ).fetchall()

    author_options = {
        " ".join(row["name"].split()): int(row["id"])
        for row in authors
    }

    # -------------------------------------------------
    # Row 1: title + searchable author
    # -------------------------------------------------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        title = st.text_input(
            "Book title",
            placeholder="Enter book title...",
            key="add_book_title",
        )

    with col2:
        author_name = st.selectbox(
            "Author",
            options=list(author_options),
            index=None,
            placeholder="Find or add an author...",
            accept_new_options=True,
            key="add_book_author",
        )

    normalized_name = (
        " ".join(author_name.split()) if author_name else ""
    )

    existing_name = next(
        (
            name for name in author_options
            if name.casefold() == normalized_name.casefold()
        ),
        None,
    )

    new_author = bool(normalized_name and existing_name is None)

    author_id = (
        author_options[existing_name]
        if existing_name is not None
        else None
    )

    iso3 = None
    confirm_similar = False

    # -------------------------------------------------
    # New author: country and duplicate protection
    # -------------------------------------------------
    if new_author:
        st.caption(f"New author: {normalized_name}")

        exact, possible = find_author_matches(normalized_name)

        if possible:
            st.warning(
                "Possible matching authors: "
                + ", ".join(row["name"] for row in possible)
            )

            confirm_similar = st.checkbox(
                "I confirm this is a different author",
                key="add_book_confirm_similar",
            )

        country_codes = sorted(
            {country.alpha_3 for country in pycountry.countries}
            | set(COUNTRY_DISPLAY_NAMES),
            key=lambda code: country_name(code).casefold(),
        )

        iso3 = st.selectbox(
            "Country of birth",
            options=country_codes,
            index=None,
            format_func=country_name,
            placeholder="Select country...",
            key="add_book_country",
        )

    # -------------------------------------------------
    # Book details
    # -------------------------------------------------
    with st.form(
        "add_book_form",
        clear_on_submit=False,
        border=False,
    ):
        col3, col4 = st.columns(2, gap="large")

        with col3:
            rating_label = st.selectbox(
                "My rating",
                list(RATING_OPTIONS),
                index=0,
            )

        with col4:
            pages = st.number_input(
                "Number of pages",
                min_value=0,
                value=0,
                step=1,
                help="Leave at 0 if unknown.",
            )

        col5, col6 = st.columns(2, gap="large")

        with col5:
            shelf_label = st.selectbox(
                "Reading status",
                ["Read", "Currently reading", "To read"],
            )

        with col6:
            date_read = st.date_input(
                "Date read (optional)",
                value=None,
                max_value="today",
                format="DD.MM.YYYY",
                key="add_book_date",
            )

        submitted = st.form_submit_button(
            "Add to Litlas",
            type="secondary",
            use_container_width=True,
        )

    if "added_book" in st.session_state:
        added_title = st.session_state.pop("added_book")

        st.markdown(
            f"""
            <div style="
                position:relative;
                margin-top:-45px;
                margin-left:calc(50% + 115px);
                margin-bottom:25px;
                color:#6E4B3A;
                font-family:Georgia,serif;
                font-size:14px;
                white-space:nowrap;
            ">
                ✓ Added: {escape(added_title)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------
    # Validation and saving
    # -------------------------------------------------
    if submitted:
        if not title.strip():
            st.error("Please enter a book title.")
            return

        if not normalized_name:
            st.error("Please select or enter an author.")
            return

        if new_author and iso3 is None:
            st.error("Please select the author's country of birth.")
            return

        if new_author and possible and not confirm_similar:
            st.error("Please confirm that this is a different author.")
            return

        shelf = {
            "Read": "read",
            "Currently reading": "currently-reading",
            "To read": "to-read",
        }[shelf_label]

        if shelf != "read":
            date_read = None

        try:
            add_book(
                author_id=author_id,
                new_author_name=normalized_name if new_author else None,
                new_author_iso3=iso3 if new_author else None,
                confirm_similar=confirm_similar,
                title=title,
                rating=RATING_OPTIONS[rating_label],
                pages=int(pages) if pages else None,
                shelf=shelf,
                date_read=(
                    date_read.strftime("%Y/%m/%d")
                    if date_read is not None
                    else None
                ),
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["added_book"] = title.strip()
            st.rerun()

