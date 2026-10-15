"""Library Management workspace for Litlas."""

import streamlit as st
import base64
from pathlib import Path

from litlas.app.book_add import render_add_book
from litlas.app.ui import apply_page_style, render_page_header
from litlas.app.book_editor import render_book_editor_contents
from pathlib import Path

ADD_BOOK_ICON = "/home/pooja-saxena/PoojaVault/Personal/Life/Creative/ImageBank/Inspiration/vintage/stack_antique_books-transparent.png"

def image_to_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")

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
    /* ==========================================
       1. LIBRARY MANAGEMENT NAVIGATION
       ========================================== */

    div[data-testid="stButton"] button:is([kind="secondary"], [kind="primary"]) {
        position: relative !important;
        background: #E8DCC9;
        border: 1px solid #C5AA87;
        border-radius: 8px;
        height: 100px !important;
        min-height: 100px !important;
        width: 100%;
        box-shadow: none;
    }

    /* Icon above the label */
    div[data-testid="stButton"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 22px !important;
    }

    /* Large navigation icons */
    div[data-testid="stButton"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] > span:first-child,
    div[data-testid="stButton"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] > span:first-child span {
        font-size: 55px !important;
        line-height: 1 !important;
    }

    /* Navigation labels */
    div[data-testid="stButton"]
    button:is([kind="secondary"], [kind="primary"])
    [data-testid="stMarkdownContainer"] p {
        position: absolute !important;
        bottom: 2px !important;
        left: 0 !important;
        width: 100% !important;
        margin: 0 !important;
        text-align: center !important;
        font-family: Georgia, serif !important;
        font-size: 17px !important;
        color: #58412F !important;
    }

    /* Hover */
    div[data-testid="stButton"]
    button:is([kind="secondary"], [kind="primary"]):hover {
        background: #DDC9AE !important;
        border-color: #A47B43 !important;
    }

    /* Selected navigation card */
    div[data-testid="stButton"] button[kind="primary"] {
        background: #D6C0A3 !important;
        border-color: #A47B43 !important;
        color: #58412F !important;
    }


    /* ==========================================
       2. VINTAGE EDITOR CARD
       ========================================== */

    .st-key-litlas_editor_card {
        background: #F7F0E4 !important;
        border: 1px solid #D4C1A7 !important;
        border-radius: 10px !important;
        padding: 16px 20px 28px !important;
    }


    /* ==========================================
       3. INPUT FIELDS
       ========================================== */

    /* Selectboxes */
    .st-key-litlas_editor_card
    [data-testid="stSelectbox"]
    .react-aria-ComboBox [role="group"] {
        background: #FFFCF7 !important;
        border: 1px solid #D4C1A7 !important;
        border-radius: 7px !important;
    }

    .st-key-litlas_editor_card
    [data-testid="stSelectbox"]
    .react-aria-ComboBox input,
    .st-key-litlas_editor_card
    [data-testid="stSelectbox"]
    .react-aria-ComboBox button {
        background: transparent !important;
        color: #58412F !important;
    }

    .st-key-litlas_editor_card
    [data-testid="stSelectbox"]
    .react-aria-ComboBox [role="group"]:focus-within {
        border-color: #A47B43 !important;
        box-shadow: 0 0 0 1px #A47B43 !important;
    }

    /* Number of pages */
    .st-key-litlas_editor_card
    [data-testid="stNumberInputContainer"] {
        background: #FFFCF7 !important;
        border: 1px solid #D4C1A7 !important;
        border-radius: 7px !important;
        overflow: hidden;
    }

    .st-key-litlas_editor_card
    [data-testid="stNumberInput"] input,
    .st-key-litlas_editor_card
    [data-testid="stNumberInput"] button {
        background: #FFFCF7 !important;
        color: #58412F !important;
    }

    .st-key-litlas_editor_card
    [data-testid="stNumberInputContainer"]:focus-within {
        border-color: #A47B43 !important;
        box-shadow: 0 0 0 1px #A47B43 !important;
    }

    /* Book title — React Aria text input */
    .st-key-litlas_editor_card
    [data-testid="stTextInputRootElement"] {
        background: #FFFCF7 !important;
        border: 1px solid #D4C1A7 !important;
        border-radius: 7px !important;
        box-shadow: none !important;
        outline: none !important;
    }

    .st-key-litlas_editor_card
    [data-testid="stTextInputField"] {
        background: transparent !important;
        color: #58412F !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Bronze focus for Book title */
    .st-key-litlas_editor_card
    [data-testid="stTextInputRootElement"]:focus-within {
        border-color: #A47B43 !important;
        outline: none !important;
        box-shadow: 0 0 0 1px #A47B43 !important;
    }

    .st-key-litlas_editor_card
    [data-testid="stTextInputField"]::placeholder {
        color: #81776E !important;
    }


    /* ==========================================
       4. DROPDOWN LISTS
       ========================================== */

    div[role="listbox"] {
        background: #FFFCF7 !important;
        border: 1px solid #D4C1A7 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 14px rgba(88, 65, 47, 0.10) !important;
    }

    div[role="option"] {
        background: #FFFCF7 !important;
        color: #58412F !important;
        font-family: Georgia, serif !important;
        font-size: 16px !important;
        padding: 10px 14px !important;
    }

    div[role="option"]:hover,
    div[role="option"][data-focused="true"],
    div[role="option"][aria-selected="true"] {
        background: #F0E6D7 !important;
    }

    div[role="listbox"]::-webkit-scrollbar {
        width: 10px;
    }

    div[role="listbox"]::-webkit-scrollbar-thumb {
        background: #D4C1A7;
        border-radius: 8px;
    }


    /* ==========================================
       5. SAVE BUTTON
       ========================================== */

    [data-testid="stForm"] {
        padding-bottom: 12px !important;
    }

    [data-testid="stFormSubmitButton"] {
        display: flex;
        justify-content: center;
    }

    [data-testid="stFormSubmitButton"] button {
        background: #8B634B !important;
        border: 1px solid #8B634B !important;
        color: #FFF9F1 !important;
        font-family: Georgia, serif !important;
        font-size: 15px !important;
        border-radius: 6px !important;
        width: 200px !important;
        min-height: 42px !important;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        background: #6E4B3A !important;
        border-color: #6E4B3A !important;
        color: #FFF9F1 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

add_book_icon_b64 = image_to_base64(ADD_BOOK_ICON)

st.markdown(
    f"""
    <style>
    /* Vintage stacked books on the Add a Book button */
    .st-key-tool_add_book
    span[data-has-shortcut="false"] > span:first-child {{
        font-size: 0 !important;
        display: block !important;
        width: 70px !important;
        height: 65px !important;
        background-image: url("data:image/png;base64,{add_book_icon_b64}") !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-size: contain !important;
    }}

    .st-key-tool_add_book
    span[data-has-shortcut="false"] > span:first-child span {{
        visibility: hidden !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if "library_tool" not in st.session_state:
    st.session_state.library_tool = None


columns = st.columns(5, gap="small")

for column, (name, symbol) in zip(columns, TOOLS):
    with column:
        selected = st.session_state.library_tool == name

        if st.button(
            name,
            icon=symbol,
            key="tool_add_book" if name == "Add a Book" else f"tool_{name}",
            type="primary" if selected else "secondary",
            use_container_width=True,
        ):
            st.session_state.library_tool = None if selected else name
            st.rerun()

selected_tool = st.session_state.library_tool

if selected_tool:
    st.markdown(
        "<hr style='margin: 8px 0 12px; border: none; "
        "border-top: 1px solid #D4C1A7;'>",
        unsafe_allow_html=True,
    )


    if selected_tool == "Edit a Book":
        st.subheader("Edit a Book")
        st.caption("Revise your personal book ratings and page counts.")

        editor_col, _ = st.columns([2, 1], gap="large")

        with editor_col:
            with st.container(
                border=True,
                key="litlas_editor_card",
            ):
                render_book_editor_contents(show_heading=False)

    elif selected_tool == "Add a Book":
        st.subheader("Add a Book")
        st.caption("Add books directly to your literary collection.")

        editor_col, _ = st.columns([2, 1], gap="large")

        with editor_col:
            with st.container(
                border=True,
                key="litlas_editor_card",
            ):
                render_add_book()

    else:
        st.subheader(selected_tool)
        st.caption(
            f"The {selected_tool} workspace will appear here."
        )
