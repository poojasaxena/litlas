"""Manual review of author birth countries."""

import pycountry
import streamlit as st

from litlas.processing.countries import country_name

from litlas.database.repository import (
    get_authors_for_review,
    get_author_books,
    verify_author_country,
)
from litlas.app.ui import apply_page_style, render_page_header, litlas_info

st.set_page_config(
    page_title="Author Review · Litlas",
    page_icon="📚",
    layout="wide",
)
apply_page_style()

render_page_header(
    "Author Review",
    "Discovering the people and places behind the stories...",
    illustration="reading_statistics",
    illustration_size=190,
    illustration_top=-35,
    illustration_left=0,
    heading_gap=20,
)

st.page_link("main.py", label="← Back to Literary Atlas")

include_provisional = st.checkbox(
    "Include provisional country assignments",
    value=False,
)

authors = get_authors_for_review(include_provisional=include_provisional)

if not authors:
    if include_provisional:
        st.success("All available author birthplaces have been reviewed.")
    else:
        litlas_info(
            "No authors have missing birth countries. "
            "Enable 'Include provisional country assignments' "
            "to review unverified birthplace matches."
        )
    st.stop()

st.metric("Authors awaiting review", len(authors))

# Authors currently eligible for review.
author_ids = [author["id"] for author in authors]
author_lookup = {author["id"]: author for author in authors}

# Keep the selected author valid when the review queue changes.
if st.session_state.get("review_author_id") not in author_ids:
    st.session_state.review_author_id = author_ids[0]

author_id = st.selectbox(
    "Select author",
    options=author_ids,
    format_func=lambda aid: (
        f"{author_lookup[aid]['name']} "
        f"({author_lookup[aid]['book_count']} books)"
    ),
    key="review_author_id",
)

author = author_lookup[author_id]
selected_index = author_ids.index(author_id)

st.subheader(author["name"])
st.write(f"**Current status:** {author['status']}")

if author["country"]:
    st.write(f"**Current country:** {author['country']}")

if author["wikidata_id"]:
    qid = author["wikidata_id"]
    st.markdown(f"[View Wikidata record](https://www.wikidata.org/wiki/{qid})")

with st.expander(
    f"Books in your library ({author['book_count']})",
    expanded=True,
):
    for book in get_author_books(author_id):
        rating = float(book["rating"])
        suffix = f" — {rating:g}★" if rating else ""
        st.write(f"• {book['title']}{suffix}")


countries = sorted(
    [(country_name(c.alpha_3), c.alpha_3) for c in pycountry.countries],
    key=lambda item: item[0].casefold(),
)

labels = ["Choose a country..."] + [f"{name} ({iso})" for name, iso in countries]

default = 0
for position, (name, iso) in enumerate(countries, start=1):
    if iso == author["iso3"]:
        default = position
        break

selected = st.selectbox(
    "Country of birth (present-day borders)",
    options=range(len(labels)),
    format_func=lambda i: labels[i],
    index=default,
    key=f"country_{author_id}",
)

left, right = st.columns(2)

with left:
    if st.button(
        "Save & Next",
        type="primary",
        disabled=(selected == 0),
        use_container_width=True,
    ):
        country, iso3 = countries[selected - 1]

        verify_author_country(author_id, country, iso3)

        # Advance to the next author in the remaining queue.
        remaining = [aid for aid in author_ids if aid != author_id]

        if remaining:
            next_index = min(selected_index, len(remaining) - 1)
            st.session_state.review_author_id = remaining[next_index]
        else:
            st.session_state.pop("review_author_id", None)

        st.rerun()

with right:
    if st.button("Skip", use_container_width=True):
        next_index = (selected_index + 1) % len(author_ids)
        st.session_state.review_author_id = author_ids[next_index]
        st.rerun()