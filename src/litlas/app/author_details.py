
"""Find authors and check for possible duplicates."""

from difflib import SequenceMatcher
import pycountry
from html import escape
from litlas.database.repository import (
    add_author,
    update_author_details,
)
from litlas.processing.countries import (
    COUNTRY_NAMES,
    country_name,
)
import streamlit as st

from litlas.database.connection import connect


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
            ORDER BY name COLLATE NOCASE
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
    """Find, add, or correct authors."""

    # Apply a corrected name before the search widget is created.
    pending_name = st.session_state.pop(
        "author_details_pending_name", None
    )
    if pending_name is not None:
        st.session_state["author_details_name"] = pending_name

    name = st.text_input(
        "Author name",
        placeholder="Find or enter an author...",
        key="author_details_name",
    ).strip()

    if not name:
        st.caption("Enter an author's name to find or add them.")
        return

    exact, possible = find_author_matches(name)

    country_codes = sorted(
        {country.alpha_3 for country in pycountry.countries}
        | set(COUNTRY_NAMES),
        key=lambda code: country_name(code).casefold(),
    )

    # EXISTING AUTHOR: allow corrections.
    if exact:
        author = exact[0]
        author_id = int(author["id"])

        st.caption("Existing author — edit details below.")

        with st.form(
            f"edit_author_form_{author_id}",
            border=False,
        ):
            col1, col2 = st.columns(2, gap="large")

            with col1:
                corrected_name = st.text_input(
                    "Correct author name",
                    value=author["name"],
                )

            with col2:
                current_iso3 = author["iso3"]
                country_index = (
                    country_codes.index(current_iso3)
                    if current_iso3 in country_codes
                    else None
                )

                corrected_iso3 = st.selectbox(
                    "Country",
                    options=country_codes,
                    index=country_index,
                    format_func=country_name,
                    placeholder="Select country...",
                )

            submitted = st.form_submit_button(
                "Save Changes",
                type="secondary",
                use_container_width=True,
            )

        if submitted:
            try:
                update_author_details(
                    author_id=author_id,
                    name=corrected_name,
                    country=country_name(corrected_iso3)
                    if corrected_iso3 else "",
                    iso3=corrected_iso3 or "",
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                saved_name = " ".join(corrected_name.split())

                st.session_state["author_details_pending_name"] = saved_name
                st.session_state["author_details_saved"] = (
                    author_id,
                    saved_name,
                )
                st.rerun()

        # Outside 'if submitted' — persists after rerun.
        saved = st.session_state.get("author_details_saved")

        if saved and saved[0] == author_id:
            st.markdown(
                f"""
                <div style="
                    background:#E8DCC8;
                    border:1px solid #CDAE86;
                    border-radius:8px;
                    padding:12px 16px;
                    margin-top:14px;
                    font-family:Georgia,serif;
                    font-size:15px;
                    color:#6E4B3A;
                ">
                    ✓ Saved: {escape(saved[1])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        return

    # POSSIBLE DUPLICATE: require explicit confirmation.
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

    # NEW AUTHOR
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
            st.session_state["author_details_saved"] = (
                author_id,
                name,
            )
            st.rerun()
