
"""Sidebar editor for locally curated book metadata."""

import pandas as pd
import streamlit as st
from html import escape

from litlas.db_backend import get_repository

repository = get_repository()

get_editable_books = repository.get_editable_books
update_book_details = repository.update_book_details


RATING_OPTIONS = {
    "Unrated": 0.0,
    "1 ★": 1.0,
    "1.5 ★": 1.5,
    "2 ★": 2.0,
    "2.5 ★": 2.5,
    "3 ★": 3.0,
    "3.5 ★": 3.5,
    "4 ★": 4.0,
    "4.5 ★": 4.5,
    "5 ★": 5.0,
}

st.markdown(
    """
    <style>
    /* Compact book editor */
    .st-key-compact_book_editor [data-testid="stVerticalBlock"] {
        gap: 0.45rem !important;
    }

    /* Reduce excessive whitespace around captions */
    .st-key-compact_book_editor [data-testid="stCaptionContainer"] {
        margin-top: -5px !important;
    }

    /* Keep the Save button close to the fields */
    .st-key-compact_book_editor [data-testid="stFormSubmitButton"] {
        margin-top: 0 !important;
    }

    /* Reduce spacing between search, reading date and form */
    .st-key-compact_book_editor [data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }

    /* Bring the small metadata captions closer to their fields */
    .st-key-compact_book_editor [data-testid="stCaptionContainer"] {
        margin-top: -12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def render_book_editor_contents(show_heading=True):
    """Render the book editor in the current location."""

    books = get_editable_books()

    if books.empty:
        st.info("No books available for editing.")
        return

    if show_heading:
        st.subheader("Library Editor")
        st.caption("Edit your personal reading records.")


    # Search all books directly by title or author.
    book_options = {
        str(row["goodreads_id"]): (
            f'{row["display_title"]} — {row["author"]}'
        )
        for _, row in books.iterrows()
    }

    selected_id = st.selectbox(
        "Find a book",
        options=list(book_options),
        format_func=lambda book_id: book_options[book_id],
        index=None,
        placeholder="Search by title or author...",
        key="editor_book",
    )

    if selected_id is None:
        return

    row = books.loc[
        books["goodreads_id"].astype(str) == selected_id
    ].iloc[0]

    
    # Reading date supplied by the database.
    date_read = pd.to_datetime(
        row.get("date_read"),
        errors="coerce",
    )

    if pd.notna(date_read):
        st.caption(f"Read on: {date_read.strftime('%-d %B %Y')}")
    else:
        st.caption("Reading date not recorded")

    stored_rating = row["rating_override"]

    if pd.isna(stored_rating):
        current_rating = float(row["rating"])
    else:
        current_rating = float(stored_rating)

    rating_labels = list(RATING_OPTIONS)

    current_label = next(
        (
            label
            for label, value in RATING_OPTIONS.items()
            if value == current_rating
        ),
        "Unrated",
    )

    current_pages = row["effective_pages"]
    original_rating = float(row["rating"])
    original_pages = row["pages"]

    # -------------------------------------------------
    # Row 2: rating + pages + save
    # -------------------------------------------------
    with st.form(
            "edit_book_form",
            clear_on_submit=False,
            border=False,
            enter_to_submit=False,
        ):
        
        with st.container(key="compact_book_editor"):
            form_col1, form_col2 = st.columns(2, gap="large")
            

            with form_col1:
                rating_label = st.selectbox(
                    "My rating",
                    rating_labels,
                    index=rating_labels.index(current_label),
                )

                st.caption(
                    f"Original Goodreads rating: {original_rating:g} ★"
                    if original_rating
                    else "Original Goodreads rating: Unrated"
                )

            with form_col2:
                pages = st.number_input(
                    "Number of pages",
                    min_value=1,
                    step=1,
                    value=int(current_pages) if pd.notna(current_pages) else 1,
                )

                if pd.notna(original_pages):
                    st.caption(f"Imported page count: {int(original_pages)}")
                else:
                    st.caption("Imported page count: missing")

            submitted = st.form_submit_button(
                "Save to Litlas",
                type="secondary",
                use_container_width=True,
            )



    saved = st.session_state.get("book_editor_saved")

    if saved and saved[0] == selected_id:
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
                ✓ Saved: {escape(str(row["display_title"]))}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if submitted:
        selected_rating = RATING_OPTIONS[rating_label]

        rating_override = (
            selected_rating
            if (
                selected_rating != float(row["rating"])
                or pd.notna(row["rating_override"])
            )
            else None
        )

        pages_override = (
            int(pages)
            if (
                pd.isna(original_pages)
                or int(pages) != int(original_pages)
                or pd.notna(row["pages_override"])
            )
            else None
        )

        try:
            update_book_details(
                goodreads_id=selected_id,
                display_title=str(row["display_title"]),
                rating_override=rating_override,
                pages_override=pages_override,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["book_editor_saved"] = (
                selected_id,
                book_options[selected_id],
            )
            st.rerun()


def render_book_editor_contents_sidebar(show_heading=True):
    """Render the Library Editor inside Streamlit's sidebar."""

    if show_heading:
        st.subheader("Library Editor")
        st.caption("Edit your personal reading records.")

    books = get_editable_books()

    if books.empty:
        st.info("No books available for editing.")
        return

    # Choose an author first to keep the book list manageable.
    authors = sorted(books["author"].dropna().unique())

    selected_author = st.selectbox(
        "Author",
        authors,
        index=None,
        placeholder="Find an author...",
        key="editor_author",
    )

    if selected_author is None:
        return

    author_books = books[
        books["author"] == selected_author
    ].copy()

    book_options = {
        str(row["goodreads_id"]): (
            f'{row["display_title"]}'
        )
        for _, row in author_books.iterrows()
    }

    selected_id = st.selectbox(
        "Book",
        options=list(book_options),
        format_func=lambda book_id: book_options[book_id],
        index=None,
        placeholder="Select a book...",
        key="editor_book",
    )

    if selected_id is None:
        return

    row = author_books[
        author_books["goodreads_id"] == selected_id
    ].iloc[0]

    # Preserve the distinction between a missing override
    # and an explicitly chosen unrated (0-star) value.
    stored_rating = row["rating_override"]

    if pd.isna(stored_rating):
        current_rating = float(row["rating"])
        rating_is_override = False
    else:
        current_rating = float(stored_rating)
        rating_is_override = True

    rating_labels = list(RATING_OPTIONS)

    current_label = next(
        (
            label
            for label, value in RATING_OPTIONS.items()
            if value == current_rating
        ),
        "Unrated",
    )


    with st.form(
        "edit_book_form",
        clear_on_submit=False,
    ):
        rating_label = st.selectbox(
            "My rating",
            rating_labels,
            index=rating_labels.index(current_label),
        )

        original_rating = float(row["rating"])
        st.caption(
            f"Original Goodreads rating: {original_rating:g} ★"
            if original_rating
            else "Original Goodreads rating: Unrated"
        )

        current_pages = row["effective_pages"]

        pages = st.number_input(
            "Number of pages",
            min_value=1,
            step=1,
            value=(
                int(current_pages)
                if pd.notna(current_pages)
                else 1
            ),
        )

        submitted = st.form_submit_button(
            "Save to Litlas",
            type="secondary",
            use_container_width=True,
        )

    if submitted:
        # Save only values that differ from Goodreads.
        # Existing overrides remain in place when unchanged.
        selected_rating = RATING_OPTIONS[rating_label]

        rating_override = (
            selected_rating
            if (
                selected_rating != float(row["rating"])
                or pd.notna(row["rating_override"])
            )
            else None
        )

        original_pages = row["pages"]

        pages_override = (
            int(pages)
            if (
                pd.isna(original_pages)
                or int(pages) != int(original_pages)
                or pd.notna(row["pages_override"])
            )
            else None
        )

        try:
            update_book_details(
                goodreads_id=selected_id,
                display_title=str(row["display_title"]),
                rating_override=rating_override,
                pages_override=pages_override,
            )

        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["book_editor_saved"] = (
                selected_id,
                str(row["display_title"]),
            )
            st.rerun()

def render_book_editor():
    """Render the editor in the Reading Statistics sidebar."""
    with st.sidebar:
        render_book_editor_contents(show_heading=True)