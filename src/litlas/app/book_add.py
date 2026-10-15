
"""Form for adding books independently of Goodreads."""

import streamlit as st

from litlas.database.connection import connect
from litlas.database.repository import add_book
from litlas.app.book_editor import RATING_OPTIONS


def render_add_book():
    """Render the Add a Book workspace."""

    with connect() as db:
        authors = db.execute(
            "SELECT id, name FROM authors ORDER BY name COLLATE NOCASE"
        ).fetchall()

    author_options = {
        int(row["id"]): row["name"]
        for row in authors
    }

    with st.form("add_book_form", clear_on_submit=True, border=False):

        col1, col2 = st.columns(2, gap="large")

        with col1:
            title = st.text_input(
                "Book title",
                placeholder="Enter book title...",
            )

        with col2:
            author_id = st.selectbox(
                "Author",
                options=list(author_options),
                format_func=lambda value: author_options[value],
                index=None,
                placeholder="Find an author...",
            )

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
            include_date = st.checkbox(
                "Include reading date",
                value=False,
            )

            date_read = (
                st.date_input("Date read", value="today")
                if include_date
                else None
            )

        submitted = st.form_submit_button(
            "Add to Litlas",
            type="secondary",
            use_container_width=True,
        )

    if submitted:
        if not title.strip():
            st.error("Please enter a book title.")
            return

        if author_id is None:
            st.error("Please select an author.")
            return

        shelf = {
            "Read": "read",
            "Currently reading": "currently-reading",
            "To read": "to-read",
        }[shelf_label]

        # A completion date is meaningful only for books marked read.
        if shelf != "read":
            date_read = None

        try:
            book_id = add_book(
                author_id=author_id,
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

    if "added_book" in st.session_state:
        st.success(
            f"Added to Litlas: {st.session_state.pop('added_book')}"
        )
