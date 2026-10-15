"""Library Management workspace for Litlas."""

import streamlit as st

from litlas.app.ui import apply_page_style, render_page_header


st.set_page_config(
    page_title="Library Management · Litlas",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_page_style()

render_page_header(
    "Library Management",
    "A home for the books, authors, and stories behind the atlas...",
    illustration="reading_statistics",
    illustration_size=175,
    illustration_top=-35,
    illustration_left=0,
    heading_gap=20,
)


# ---------------------------------------------------------
# Library Management tools
# ---------------------------------------------------------

TOOLS = [
    ("📖", "Edit a Book", "Ratings, pages and titles"),
    ("⊕", "Add a Book", "Independent of Goodreads"),
    ("♡", "Favourite Authors", "Your personal selections"),
    ("⌾", "Author Details", "Birthplaces and countries"),
    ("↻", "Goodreads Import", "Refresh source records"),
]

st.markdown(
    """
    <style>
    /* Library Management bricks */
    div[data-testid="stButton"] button[kind="secondary"] {
        background:#F5EFE4;
        border:1px solid #D4C1A7;
        color:#58412F;
        border-radius:8px;
        min-height:72px;
        width:100%;
        font-family:Georgia,serif;
        font-size:21px;
        font-weight:500;
        box-shadow:none;
    }

    /* Larger symbols and consistent button typography */
    div[data-testid="stButton"] button[kind="secondary"] p {
        font-family:Georgia,serif;
        font-size:21px;
        line-height:1.3;
        color:#58412F;
    }

    /* Hover */
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background:#EDE3D4;
        border-color:#A47B43;
        color:#58412F;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background:#EDE3D4;
        border-color:#A47B43;
        color:#58412F;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "library_tool" not in st.session_state:
    st.session_state.library_tool = None

for start in range(0, len(TOOLS), 2):
    columns = st.columns(2, gap="small")

    for column, (symbol, name, description) in zip(
        columns, TOOLS[start:start + 2]
    ):
        with column:
            if st.button(
                f"{symbol}  {name}\n{description}",
                key=f"tool_{start}_{name}",
                use_container_width=True,
            ):
                st.session_state.library_tool = (
                    None
                    if st.session_state.library_tool == name
                    else name
                )

selected_tool = st.session_state.library_tool

if selected_tool:
    st.divider()
    st.subheader(selected_tool)

    st.caption(
        f"The {selected_tool} workspace will appear here."
    )
