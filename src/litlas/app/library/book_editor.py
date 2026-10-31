
"""Sidebar editor for locally curated book metadata."""

import pandas as pd
import streamlit as st
from html import escape

from litlas.db_backend import get_repository

repository = get_repository()

get_editable_books = repository.get_editable_books
update_book_details = repository.update_book_details
delete_book = repository.delete_book

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

st.html("""
<style>
.st-key-compact_book_editor [data-testid="stVerticalBlock"] {
    gap: 0.3rem !important;
}
.st-key-compact_book_editor [data-testid="stCaptionContainer"] {
    margin-top: -6px !important;
}
/* Save to Litlas — warm brown */
div.st-key-book_save_area button[kind="secondary"] {
    background-color: #906A52 !important;
    border: 1px solid #906A52 !important;
    color: #FFFFFF !important;
    border-radius: 7px !important;
}

div.st-key-book_save_area button[kind="secondary"]:hover {
    background-color: #79533D !important;
    border-color: #79533D !important;
}

div.st-key-book_save_area button[kind="secondary"] p {
    color: #FFFFFF !important;
}

/* Delete remains a separate, small, darker text action. */
.st-key-book_delete_button button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #512D29 !important;
    min-height: 30px !important;
    padding: 2px 9px !important;
    font-size: 13px !important;
}
.st-key-book_delete_button button p {
    color: #512D29 !important;
    font-size: 13px !important;
}
.st-key-book_delete_button button:hover,
.st-key-book_delete_button button:hover p {
    color: #35201D !important;
    text-decoration: underline !important;
}

/* Compact Delete action, aligned to the right */
.st-key-book_delete_area {
    margin-top: -65px !important;
    margin-bottom: 0 !important;
}

.st-key-book_delete_area [data-testid="stButton"] {
    display: flex !important;
    justify-content: flex-end !important;
}

.st-key-book_delete_area button {
    width: auto !important;
    min-height: 28px !important;
    padding: 2px 8px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #512D29 !important;
    font-size: 13px !important;
}

.st-key-book_delete_area button:hover {
    color: #35201D !important;
    text-decoration: underline !important;
}
</style>
""")

def render_book_editor_contents(show_heading=True):
    """Render the searchable book editor in the current location."""

    if st.session_state.pop("reset_delete_confirmation", False):
        st.session_state.pop("confirm_delete_book_checkbox", None)
    if st.session_state.pop("reset_book_selection", False):
        st.session_state.pop("editor_book", None)

    if deleted := st.session_state.pop("book_deleted", None):
        st.success(f"Deleted: {deleted}")

    books = get_editable_books()
    if books.empty:
        st.info("No books available for editing.")
        return

    if show_heading:
        st.subheader("Library Editor")
        st.caption("Edit book titles, personal ratings, and page counts.")

    book_options = {
        str(row["goodreads_id"]): f'{row["display_title"]} — {row["author"]}'
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

    # Switching books cancels any pending deletion of the previous book.
    if st.session_state.get("book_editor_last_selected") != selected_id:
        st.session_state["book_editor_last_selected"] = selected_id
        st.session_state.pop("confirm_book_deletion", None)
        st.session_state.pop("confirm_delete_book_checkbox", None)

    row = books.loc[
        books["goodreads_id"].astype(str) == selected_id
    ].iloc[0]

    date_read = pd.to_datetime(row.get("date_read"), errors="coerce")
    if pd.notna(date_read):
        st.caption(f"Read on: {date_read.strftime('%d %B %Y')}")
    else:
        st.caption("Reading date not recorded")

    stored_rating = row["rating_override"]
    current_rating = (
        float(row["rating"]) if pd.isna(stored_rating)
        else float(stored_rating)
    )
    rating_labels = list(RATING_OPTIONS)
    current_label = next(
        (label for label, value in RATING_OPTIONS.items()
         if value == current_rating),
        "Unrated",
    )

    original_rating = float(row["rating"])
    original_pages = row["pages"]
    current_pages = row["effective_pages"]

    # Individual input keys ensure values refresh when another book is selected.
    with st.container(key="compact_book_editor"):
        form_col1, form_col2, form_col3 = st.columns(
            [2.2, 1, 1], gap="medium"
        )
        with form_col1:
            edited_title = st.text_input(
                "Book title",
                value=str(row["display_title"]),
                key=f"book_title_{selected_id}",
            )
            st.caption(f'Original title: {row["original_title"]}')

        with form_col2:
            rating_label = st.selectbox(
                "My rating",
                rating_labels,
                index=rating_labels.index(current_label),
                key=f"book_rating_{selected_id}",
            )
            st.caption(
                f"Original rating: {original_rating:g} ★"
                if original_rating else "Original rating: Unrated"
            )

        with form_col3:
            pages = st.number_input(
                "Number of pages",
                min_value=1,
                step=1,
                value=int(current_pages) if pd.notna(current_pages) else 1,
                key=f"book_pages_{selected_id}",
            )
            if pd.notna(original_pages):
                st.caption(f"Page count: {int(original_pages)}")
            else:
                st.caption("Page count: missing")

        # A single prominent Save button, visually separated from deletion.
        _, save_col, _ = st.columns([1, 1.25, 1], gap="small")
        with save_col:
            with st.form("book_save_form", border=False):
                submitted = st.form_submit_button(
                    "Save to Litlas",
                    use_container_width=True,
                )

    # Keep destructive action less prominent and away from Save.
    # Delete action — small and separate from Save
    with st.container(key="book_delete_area"):
        delete_clicked = st.button(
            "Delete book",
            key="book_delete_button",
            type="tertiary",
        )

    if submitted:
        selected_rating = RATING_OPTIONS[rating_label]
        rating_override = (
            selected_rating
            if (selected_rating != original_rating
                or pd.notna(row["rating_override"]))
            else None
        )
        pages_override = (
            int(pages)
            if (pd.isna(original_pages)
                or int(pages) != int(original_pages)
                or pd.notna(row["pages_override"]))
            else None
        )
        try:
            update_book_details(
                goodreads_id=selected_id,
                display_title=edited_title,
                rating_override=rating_override,
                pages_override=pages_override,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["book_editor_saved"] = (
                selected_id, edited_title
            )
            st.rerun()

    saved = st.session_state.get("book_editor_saved")
    if saved and saved[0] == selected_id:
        st.success(f"Saved: {saved[1]}")
        st.session_state.pop("book_editor_saved", None)

    if delete_clicked:
        st.session_state["confirm_book_deletion"] = selected_id

    if st.session_state.get("confirm_book_deletion") == selected_id:
        st.warning(
            f'Permanently delete "{row["display_title"]}" '
            f'by {row["author"]}?'
        )
        confirmed = st.checkbox(
            "I understand this cannot be undone.",
            key="confirm_delete_book_checkbox",
        )
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button(
                "Confirm Deletion",
                disabled=not confirmed,
                key="book_confirm_deletion",
                type="primary",
                use_container_width=True,
            ):
                try:
                    deleted_title = delete_book(selected_id)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.session_state.pop("confirm_book_deletion", None)
                    st.session_state["reset_delete_confirmation"] = True
                    st.session_state.pop("book_editor_saved", None)
                    st.session_state["book_deleted"] = deleted_title
                    st.session_state["reset_book_selection"] = True
                    st.rerun()
        with cancel_col:
            if st.button("Cancel", key="book_cancel_deletion",
                         use_container_width=True):
                st.session_state.pop("confirm_book_deletion", None)
                st.session_state["reset_delete_confirmation"] = True
                st.rerun()

def render_book_editor_contents_sidebar(show_heading=True):
    """Render the Library Editor inside Streamlit's sidebar."""

    if deleted := st.session_state.pop("book_deleted", None):
        st.success(f"Deleted: {deleted}")

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
            f"Original rating: {original_rating:g} ★"
            if original_rating
            else "Original rating: Unrated"
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
            width="stretch",
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