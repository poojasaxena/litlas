
"""Sidebar editor for locally curated book metadata."""

import pandas as pd
import streamlit as st

from litlas.database.repository import (
    get_editable_books,
    update_book_details,
)


RATING_OPTIONS = {
    "Unrated": 0.0,
    "1 ★": 1.0,
    "2 ★": 2.0,
    "3 ★": 3.0,
    "3.5 ★": 3.5,
    "4 ★": 4.0,
    "4.5 ★": 4.5,
    "5 ★": 5.0,
}


def render_book_editor():
    """Render the Library Editor inside Streamlit's sidebar."""

    with st.sidebar:
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
            title = st.text_input(
                "Display title",
                value=str(row["display_title"]),
            )

            rating_label = st.selectbox(
                "My rating",
                rating_labels,
                index=rating_labels.index(current_label),
            )

            original_rating = float(row["rating"])
            st.caption(
                f"Goodreads rating: {original_rating:g} ★"
                if original_rating
                else "Goodreads rating: Unrated"
            )

            use_rating_override = st.checkbox(
                "Save rating as my Litlas correction",
                value=rating_is_override,
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

            use_pages_override = st.checkbox(
                "Save pages as my Litlas correction",
                value=pd.notna(row["pages_override"]),
            )

            submitted = st.form_submit_button(
                "Save changes",
                use_container_width=True,
            )

        if submitted:
            rating_override = (
                RATING_OPTIONS[rating_label]
                if use_rating_override
                else None
            )

            pages_override = (
                int(pages)
                if use_pages_override
                else None
            )

            try:
                update_book_details(
                    goodreads_id=selected_id,
                    display_title=title,
                    rating_override=rating_override,
                    pages_override=pages_override,
                )

            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("Book details saved.")
                st.rerun()
