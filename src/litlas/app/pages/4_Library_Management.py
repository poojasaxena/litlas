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
    ("Edit a Book", "📖"),
    ("Add a Book", "📚"),
    ("Favourites", "🤎"),
    ("Author Details", "✒️"),
    ("Goodreads", "📜"),
]


st.markdown(
    """
    <style>
    /* Library Management buttons */
    div[data-testid="stButton"] button[kind="secondary"] {
        background: #F5EFE4;
        border: 1px solid #D4C1A7;
        border-radius: 8px;
        height: 20px !important;
        min-height: 100px !important;
        width: 100%;
        box-shadow: none;
    }

    /* Stack the inner icon-and-label wrapper vertically */
    div[data-testid="stButton"] button[kind="secondary"]
    span[data-has-shortcut="false"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 22px !important;
    }

    /* Enlarge the emoji itself */
    div[data-testid="stButton"] button[kind="secondary"]
    span[data-has-shortcut="false"] > span:first-child,
    div[data-testid="stButton"] button[kind="secondary"]
    span[data-has-shortcut="false"] > span:first-child span {
        font-size: 55px !important;
        line-height: 1 !important;
    }
    /* Button label */
    div[data-testid="stButton"] button[kind="secondary"] p {
        font-family: Georgia, serif !important;
        font-size: 17px !important;
        color: #58412F !important;
        margin: 0 !important;
        text-align: center;
        transform: translateY(1px);
    }

    /* Hover */
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: #EDE3D4;
        border-color: #A47B43;
    }

    /* Establish a positioning reference */
    div[data-testid="stButton"] button[kind="secondary"] {
        position: relative !important;
    }

    /* Position the label near the bottom */
    div[data-testid="stButton"] button[kind="secondary"]
    [data-testid="stMarkdownContainer"] p {
        position: absolute !important;
        bottom: 2px !important;
        left: 0 !important;
        width: 100% !important;
        margin: 0 !important;
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "library_tool" not in st.session_state:
    st.session_state.library_tool = None

## Five buttons for Library Management tools in a single row
columns = st.columns(5, gap="small")

for column, (name, symbol) in zip(columns, TOOLS):
    with column:
        if st.button(
            name,
            icon=symbol,
            key=f"tool_{name}",
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
