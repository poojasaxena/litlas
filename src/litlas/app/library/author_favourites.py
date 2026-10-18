
"""Manage personal literary favourites in Litlas."""

import streamlit as st

from litlas.database.repository import (
    get_authors_for_favourites,
    set_author_favourite,
    get_favourite_authors,
)

FAVOURITE_TIERS = {
    0: "Not selected",
    1: "❦  Exceptional",
    2: "♥  Favourites",
    3: "ღ  Good authors",
}


def render_author_favourites():
    """Select an author and assign a literary category."""

    authors = get_authors_for_favourites()

    if not authors:
        st.info("No authors available.")
        return

    author_options = {
        int(row["id"]): {
            "name": row["name"],
            "tier": int(row["favourite_tier"]),
        }
        for row in authors
    }

    if "favourite_tier_editor" not in st.session_state:
        st.session_state["favourite_tier_editor"] = 0

    def load_author_category():
        author_id = st.session_state["favourite_author_editor"]

        st.session_state["favourite_tier_editor"] = (
            author_options[author_id]["tier"]
            if author_id is not None
            else 0
        )

        st.session_state.pop("favourite_saved", None)

    # Outside the form: selecting an author updates the category.
    author_id = st.selectbox(
        "Author",
        options=list(author_options),
        format_func=lambda value: author_options[value]["name"],
        index=None,
        placeholder="Find an author...",
        key="favourite_author_editor",
        on_change=load_author_category,
    )

    if author_id is None:
        return

    with st.form("favourite_author_form", border=False):
        st.selectbox(
            "Literary category",
            options=list(FAVOURITE_TIERS),
            format_func=lambda tier: FAVOURITE_TIERS[tier],
            key="favourite_tier_editor",
        )

        submitted = st.form_submit_button(
            "Save Category",
            type="secondary",
            use_container_width=True,
        )

    if submitted:
        tier = st.session_state["favourite_tier_editor"]

        try:
            set_author_favourite(author_id, tier)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["favourite_saved"] = (
                author_id,
                author_options[author_id]["name"],
                FAVOURITE_TIERS[tier],
            )
            st.rerun()

    saved = st.session_state.get("favourite_saved")

    if saved and saved[0] == author_id:
        st.success(
            f"Saved: {saved[1]} — {saved[2]}"
        )

def render_favourite_collection():
    """Display all three literary categories compactly."""

    import html

    authors = get_favourite_authors()

    categories = {
        tier: tuple(label.split(maxsplit=1))
        for tier, label in FAVOURITE_TIERS.items()
        if tier != 0
    }
    sections = []

    for tier, (symbol, title) in categories.items():
        names = [
            " ".join(row["name"].split())
            for row in authors
            if row["favourite_tier"] == tier
        ]

        names_html = (
            " · ".join(html.escape(name) for name in names)
            if names
            else "No authors yet"
        )

        sections.append(f"""
            <div style="
                padding: 10px 0 12px;
                border-bottom: 1px solid #D4C1A7;
            ">
                <div style="
                    display: flex;
                    align-items: baseline;
                    gap: 12px;
                    margin-bottom: 6px;
                ">
                    <span style="
                        font-family: Georgia, serif;
                        font-size: 19px;
                        font-weight: bold;
                        color: #58412F;
                    ">{symbol} {title}</span>

                    <span style="
                        font-size: 12px;
                        color: #81776E;
                    ">{len(names)} authors</span>
                </div>

                <div style="
                    font-size: 15px;
                    line-height: 1.65;
                    color: #58412F;
                ">{names_html}</div>
            </div>
        """)

    st.markdown(
        " ".join(" ".join(section.split()) for section in sections),
        unsafe_allow_html=True,
    )