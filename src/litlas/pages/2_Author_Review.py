"""Manual review of author birth countries."""

import pycountry
import streamlit as st

from litlas.database.repository import (
    get_authors_for_review,
    get_author_books,
    verify_author_country,
)
from litlas.ui import apply_page_style

st.set_page_config(
    page_title="Author Review · Litlas",
    page_icon="📚",
    layout="centered",
)
apply_page_style()
st.title("📚 Author Birthplace Review")
st.caption("Verify an author's country of birth and save it to SQLite.")

st.page_link("app.py", label="← Back to Literary Atlas")

include_provisional = st.checkbox(
    "Include provisional country assignments",
    value=False,
)

authors = get_authors_for_review(include_provisional=include_provisional)

if not authors:
    st.success("No authors awaiting review in this category.")
    st.stop()

st.metric("Authors awaiting review", len(authors))

# Remember position between Streamlit reruns.
if "review_index" not in st.session_state:
    st.session_state.review_index = 0

index = min(st.session_state.review_index, len(authors) - 1)

author_ids = [author["id"] for author in authors]
author_lookup = {author["id"]: author for author in authors}

author_id = st.selectbox(
    "Select author",
    options=author_ids,
    index=index,
    format_func=lambda aid: (
        f"{author_lookup[aid]['name']} " f"({author_lookup[aid]['book_count']} books)"
    ),
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

# Supported present-day countries with ISO3 codes.
COUNTRY_NAMES = {
    "KOR": "South Korea",
    "PRK": "North Korea",
    "USA": "United States",
    "GBR": "United Kingdom",
    "RUS": "Russia",
    "IRN": "Iran",
    "CZE": "Czechia",
    "TWN": "Taiwan",
}

countries = sorted(
    [(COUNTRY_NAMES.get(c.alpha_3, c.name), c.alpha_3) for c in pycountry.countries],
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

        # The saved author disappears from the review queue.
        st.session_state.review_index = selected_index
        st.rerun()

with right:
    if st.button("Skip", use_container_width=True):
        st.session_state.review_index = (selected_index + 1) % len(authors)
        st.rerun()
