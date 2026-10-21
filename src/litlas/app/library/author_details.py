
"""Find authors and check for possible duplicates."""

from difflib import SequenceMatcher
import pycountry
from html import escape
import streamlit as st

from litlas.processing.countries import (
    COUNTRY_DISPLAY_NAMES,
    country_name,
)
from litlas.db_backend import connect, is_postgres
from litlas.db_backend import get_repository

repository = get_repository()

add_author = repository.add_author
update_author_details = repository.update_author_details
delete_author = repository.delete_author
get_author_dependencies = repository.get_author_dependencies

def normalize_author_name(name: str) -> str:
    """Ignore differences in spacing and capitalization."""
    return " ".join(name.split()).casefold()


def find_author_matches(name: str):
    """Separate exact matches from possible duplicates."""

    normalized = normalize_author_name(name)

    if not normalized:
        return [], []

    with connect() as db:
        authors = db.execute(
            """
            SELECT id, name, country, iso3
            FROM authors
            ORDER BY LOWER(name), name
            """
        ).fetchall()

    exact = []
    possible = []

    for author in authors:
        existing_name = normalize_author_name(author["name"])

        if normalized == existing_name:
            exact.append(author)
        elif (
            SequenceMatcher(
                None, normalized, existing_name
            ).ratio() >= 0.80
        ):
            possible.append(author)

    return exact, possible


def render_author_details():
    """Find, add, correct, or safely delete authors."""

    # --------------------------------------------------
    # Persistent vintage confirmation
    # --------------------------------------------------
    def show_confirmation(message):
        st.markdown(
            f"""
            <div style="
                color:#6E4B3A;
                font-family:Georgia,serif;
                font-size:14px;
                padding:0;
                margin:0;
            ">
                ✓ {escape(message)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # After deletion, clear the search field BEFORE creating it.
    pending_name = st.session_state.pop(
        "author_details_pending_name", None
    )
    if pending_name is not None:
        st.session_state["author_details_name"] = pending_name

    # --------------------------------------------------
    # Remember which existing author is being edited.
    #
    # This is important: correcting an author's name
    # must not turn them into a new author.
    # --------------------------------------------------
    def author_name_changed():
        entered = st.session_state["author_details_name"]

        if not entered.strip():
            st.session_state["author_details_selected_id"] = None
        else:
            exact, _ = find_author_matches(entered)

            if exact:
                st.session_state["author_details_selected_id"] = (
                    int(exact[0]["id"])
                )
            # When there is no exact match, retain the
            # previously selected ID for name corrections.

        st.session_state.pop("author_deleted_message", None)

    name = st.text_input(
        "Author name",
        placeholder="Find or enter an author...",
        key="author_details_name",
        on_change=author_name_changed,
    ).strip()

    if not name:
        deleted_message = st.session_state.get(
            "author_deleted_message"
        )
        if deleted_message:
            show_confirmation(deleted_message)
        else:
            st.caption("Find an existing author or enter a new name.")
        return

    exact, possible = find_author_matches(name)

    selected_id = st.session_state.get(
        "author_details_selected_id"
    )

    # Recover exact matches, including on initial page load.
    if exact:
        selected_id = int(exact[0]["id"])
        st.session_state["author_details_selected_id"] = selected_id

    country_codes = sorted(
        {country.alpha_3 for country in pycountry.countries}
        | set(COUNTRY_DISPLAY_NAMES),
        key=lambda code: country_name(code).casefold(),
    )

    # --------------------------------------------------
    # EXISTING AUTHOR
    # --------------------------------------------------
    if selected_id is not None:

        placeholder = "%s" if is_postgres() else "?"

        with connect() as db:
            author = db.execute(
                f"""
                SELECT id, name, country, iso3
                FROM authors
                WHERE id = {placeholder}
                """,
                (selected_id,),
            ).fetchone()

        if author is None:
            st.session_state["author_details_selected_id"] = None
            st.warning("This author no longer exists.")
            return

        author_id = int(author["id"])
        books, works = get_author_dependencies(author_id)
        deletion_blocked = bool(books or works)

        st.caption("Existing author — edit details below.")

        # The search field above doubles as the editable
        # author name. No duplicate name field.
        current_iso3 = author["iso3"]
        country_index = (
            country_codes.index(current_iso3)
            if current_iso3 in country_codes
            else None
        )

        iso3 = st.selectbox(
            "Country",
            options=country_codes,
            index=country_index,
            format_func=country_name,
            placeholder="Select country...",
            key=f"author_country_{author_id}",
        )

        # Two actions, one compact row.
        save_col, delete_col = st.columns(
            2, gap="large"
        )

        with save_col:
            with st.form(
                f"save_author_form_{author_id}",
                border=False,
            ):
                save_submitted = st.form_submit_button(
                    "Save Changes",
                    type="secondary",
                    use_container_width=True,
                )

        with delete_col:
            with st.form(
                f"delete_request_form_{author_id}",
                border=False,
            ):
                delete_requested = st.form_submit_button(
                    "Delete Author",
                    type="secondary",
                    disabled=deletion_blocked,
                    use_container_width=True,
                    key="author_delete_button",
                )

        ## Show confirmation if author details were recently saved.
        saved = st.session_state.get("author_details_saved")

        if saved and saved[0] == author_id:
            st.markdown(
                f"""
                <div style="
                    color:#6E4B3A;
                    font-family:Georgia,serif;
                    font-size:14px;
                    margin-top:-18px;
                    margin-bottom:14px;
                    padding-left:6px;
                ">
                    ✓ Saved: {escape(saved[1])}
                </div>
                """,
                unsafe_allow_html=True,
            )


        # Save changes.
        if save_submitted:
            try:
                update_author_details(
                    author_id=author_id,
                    name=name,
                    country=country_name(iso3) if iso3 else "",
                    iso3=iso3 or "",
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state["author_details_saved"] = (
                    author_id,
                    " ".join(name.split()),
                )
                st.session_state.pop(
                    "author_delete_pending", None
                )
                st.rerun()

        # Explain disabled deletion in one small line.
        if deletion_blocked:
            st.caption(
                f"Deletion unavailable: {books} book(s) "
                f"and {works} work(s) are linked."
            )

        # --------------------------------------------------
        # DELETE CONFIRMATION — only for unlinked authors
        # --------------------------------------------------
        if delete_requested and not deletion_blocked:
            st.session_state["author_delete_pending"] = author_id

        if (
            not deletion_blocked
            and st.session_state.get("author_delete_pending")
            == author_id
        ):
            confirm_col, button_col = st.columns(
                2, gap="large", vertical_alignment="bottom"
            )

            with confirm_col:
                confirmed = st.checkbox(
                    f"Yes, permanently delete {author['name']}",
                    key=f"confirm_delete_{author_id}",
                )

            with button_col:
                with st.form(
                    f"confirm_delete_form_{author_id}",
                    border=False,
                ):
                    delete_submitted = st.form_submit_button(
                        "Confirm Deletion",
                        disabled=not confirmed,
                        type="secondary",
                        use_container_width=True,
                        key="author_confirm_delete_button",
                    )

            if delete_submitted:
                try:
                    deleted_name = delete_author(author_id)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.session_state["author_details_pending_name"] = ""
                    st.session_state["author_details_selected_id"] = None
                    st.session_state.pop("author_details_saved", None)
                    st.session_state.pop("author_delete_pending", None)
                    st.session_state["author_deleted_message"] = (
                        f"Deleted: {deleted_name}"
                    )
                    st.rerun()

        return

    # --------------------------------------------------
    # POSSIBLE DUPLICATE
    # --------------------------------------------------
    if possible:
        st.warning("Possible matching authors:")

        for author in possible:
            st.write(
                f"**{author['name']}** — "
                f"{author['country'] or 'Country unknown'}"
            )

        confirmed = st.checkbox(
            "I confirm this is a different author",
            key=f"confirm_author_{normalize_author_name(name)}",
        )
    else:
        st.caption("No matching author found.")
        confirmed = True

    # --------------------------------------------------
    # NEW AUTHOR
    # --------------------------------------------------
    iso3 = st.selectbox(
        "Country",
        options=country_codes,
        format_func=country_name,
        index=None,
        placeholder="Select country...",
        key="author_details_country",
    )

    with st.form("add_author_form", border=False):
        submitted = st.form_submit_button(
            "Add Author",
            type="secondary",
            disabled=not confirmed or iso3 is None,
            use_container_width=True,
        )

    if submitted:
        try:
            author_id = add_author(
                name=name,
                country=country_name(iso3),
                iso3=iso3,
                confirm_similar=bool(possible and confirmed),
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["author_details_selected_id"] = author_id
            st.session_state["author_details_saved"] = (
                author_id,
                name,
            )
            st.rerun()
