import streamlit as st

from litlas.app.visualizations.year_postcard import show_year_postcard
from litlas.db_backend import get_repository


st.set_page_config(page_title="Postcard preview", layout="wide")


@st.cache_data(ttl=300)
def load_preview_data():
    repo = get_repository()
    return repo.load_read_books(), repo.get_constellation_book_details()


show_year_postcard(*load_preview_data())