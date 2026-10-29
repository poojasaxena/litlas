"""
litlas.app.pages.3_Library_Management
Library Management workspace for Litlas.
"""

import streamlit as st
import base64
from pathlib import Path
import pandas as pd
from textwrap import dedent

from html import escape
from litlas.db_backend import is_postgres

from litlas.app.library.author_favourites import (
    render_author_favourites,
    render_favourite_collection,
)
from textwrap import dedent
from litlas.app.library.author_details import render_author_details
from litlas.app.library.book_add import render_add_book
from litlas.app.ui import apply_page_style, render_page_header
from litlas.app.library.book_editor import render_book_editor_contents
from litlas.database.importer import (
    preview_goodreads_import,
    resolve_goodreads_date_conflict,
)
from litlas.processing.paths import illustration_path

ADD_BOOK_ICON = str(illustration_path("add_book"))


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
    "A home for the books, authors, and stories behind the atlas",
    illustration="lib_management",
    illustration_size=185,
    illustration_top=-35,
    illustration_left=0,
    heading_gap=20,
    title_height=90,
    ornament_width=290,
)

# Local SQLite: preserve existing Library Management access.
# Cloud PostgreSQL: require authenticated owner access.
if is_postgres():
    auth_config = st.secrets.get("auth", {})
    admin_email = str(st.secrets.get("admin_email", "")).strip().casefold()

    if not auth_config or not admin_email:
        st.error("Library Management authentication is not configured.")
        st.stop()

    if not getattr(st.user, "is_logged_in", False):
        st.markdown(
            dedent("""
            <div style="font-family: Georgia, serif; color: #58412F; margin-top: 20px;">
                <div style="font-size: 26px; font-weight: bold; margin-bottom: 18px;">
                    Owner's Library
                </div>
                <p style="font-size: 17px; line-height: 1.7; color: #8B634B;">
                    This section is reserved for the owner of Litlas.
                    Books, authors, ratings and literary collections are managed here.
                </p>
                <p style="font-size: 14px; color: #81776E; margin-top: 22px;">
                    🔒 Owner authentication required.
                </p>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.button("Log in with Google", on_click=st.login)
        st.stop()

    user_email = str(st.user.get("email", "")).strip().casefold()
    email_verified = st.user.get("email_verified") is True

    if not email_verified or user_email != admin_email:
        st.markdown(
            dedent("""
            <div style="font-family: Georgia, serif; color: #58412F; margin-top: 20px;">
                <div style="font-size: 26px; font-weight: bold; margin-bottom: 18px;">
                    Owner's Library
                </div>
                <p style="font-size: 17px; line-height: 1.7; color: #8B634B;">
                    Library Management is reserved for the owner of Litlas.
                    This account does not have permission to manage the literary collection.
                </p>
                <p style="font-size: 14px; color: #81776E; margin-top: 22px;">
                    🔒 Owner access only.
                </p>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.button("Log out", on_click=st.logout)
        st.stop()

# ---------------------------------------------------------
# Library Management tools
# ---------------------------------------------------------

TOOLS = [
    ("Add a Book", "📚"),
    ("Edit a Book", "📖"),
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

    div[class*="st-key-tool_"]
        button:is([kind="secondary"], [kind="primary"]) {
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
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 22px !important;
    }

    /* Large navigation icons */
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] > span:first-child,
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] > span:first-child span {
        font-size: 55px !important;
        line-height: 1 !important;
    }

    /* Navigation labels */
    div[class*="st-key-tool_"]
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
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"]):hover {
        background: #DDC9AE !important;
        border-color: #A47B43 !important;
    }

    /* Selected navigation card */
    div[class*="st-key-tool_"] button[kind="primary"] {
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
        padding: 16px 20px 8px !important;
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

    /* Date read — match the other Litlas fields */
    .st-key-add_book_date [data-testid="stDateInputField"] {
        background: #FFFCF7 !important;
        color: #58412F !important;
    }

    .st-key-add_book_date [data-testid="stDateInputRootElement"],
    .st-key-add_book_date .react-aria-DateField [role="group"],
    .st-key-add_book_date .react-aria-DatePicker [role="group"] {
        background: #FFFCF7 !important;
        border: 1px solid #D4C1A7 !important;
        border-radius: 7px !important;
        box-shadow: none !important;
    }

    .st-key-add_book_date input {
        background: transparent !important;
        color: #58412F !important;
    }

    /* All text inputs — vintage ivory styling */
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

    /* Bronze focus for all text inputs */
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

    /* Browser autofill — preserve the vintage ivory background */
    .st-key-litlas_editor_card
    [data-testid="stTextInputField"]:is(:-webkit-autofill, :autofill) {
        -webkit-box-shadow: 0 0 0 1000px #FFFCF7 inset !important;
        -webkit-text-fill-color: #58412F !important;
        caret-color: #58412F !important;
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

    /* Destructive action — Delete Author */
    .st-key-author_delete_button button {
        background: #653B35 !important;
        border-color: #653B35 !important;
        color: #FFF9F1 !important;
    }

    .st-key-author_delete_button button:hover {
        background: #4E2B27 !important;
        border-color: #4E2B27 !important;
    }

    /* Both destructive actions use the darker burgundy */
    .st-key-author_delete_button button,
    .st-key-author_confirm_delete_button button {
        background: #653B35 !important;
        border-color: #653B35 !important;
        color: #FFF9F1 !important;
    }

    .st-key-author_delete_button button:hover,
    .st-key-author_confirm_delete_button button:hover {
        background: #4E2B27 !important;
        border-color: #4E2B27 !important;
    }

    /* Keep disabled confirmation visually distinct */
    .st-key-author_confirm_delete_button button:disabled {
        opacity: 0.45 !important;
    }
    /* Reduce space between Literary Collection heading and author list */
    .st-key-literary_collection {
        gap: 0 !important;
    }

    .st-key-literary_collection [data-testid="stMarkdown"] h3 {
        margin-bottom: 0 !important;
    }

    /* Compact Goodreads action */
    .st-key-goodreads_check_changes button {
        width: 190px !important;
        min-width: 190px !important;
        height: 38px !important;
        min-height: 38px !important;
        padding: 6px 14px !important;

        background: #8B634B !important;
        border: 1px solid #8B634B !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }

    .st-key-goodreads_check_changes button,
    .st-key-goodreads_check_changes button * {
        color: #FFF9F1 !important;
        font-family: Georgia, serif !important;
        font-size: 14px !important;
        font-weight: 400 !important;
    }

    .st-key-goodreads_check_changes button:hover {
        background: #6E4B3A !important;
        border-color: #6E4B3A !important;
    }

/* ==========================================
   LIBRARY NAVIGATION — MOBILE ONLY
   ========================================== */

@media screen and (max-width: 640px) {

    /* Keep all five Streamlit columns in one row */
    .st-key-litlas_library_navigation
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
        gap: 5px !important;
    }

    .st-key-litlas_library_navigation
    [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: none !important;
    }

    /* Compact navigation buttons */
    .st-key-litlas_library_navigation
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"]) {
        height: 72px !important;
        min-height: 72px !important;
        padding: 5px 2px !important;
        overflow: hidden !important;
    }

    /* Smaller icons, closer to their labels */
    .st-key-litlas_library_navigation
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] {
        gap: 5px !important;
    }

    .st-key-litlas_library_navigation
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] > span:first-child,
    .st-key-litlas_library_navigation
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"])
    span[data-has-shortcut="false"] > span:first-child span {
        font-size: 25px !important;
    }

    /* Labels fit into narrow cards */
    .st-key-litlas_library_navigation
    div[class*="st-key-tool_"]
    button:is([kind="secondary"], [kind="primary"])
    [data-testid="stMarkdownContainer"] p {
        font-size: 10px !important;
        line-height: 1.15 !important;
        bottom: 5px !important;
        padding: 0 2px !important;
        white-space: normal !important;
    }

    /* Scale down the custom Add a Book illustration */
    .st-key-litlas_library_navigation
    .st-key-tool_add_book
    span[data-has-shortcut="false"] > span:first-child {
        width: 33px !important;
        height: 30px !important;
        background-size: contain !important;
    }
}
/* Add a Book — mobile spacing only */
@media screen and (max-width: 640px) {

    .st-key-litlas_editor_card
    [data-testid="stVerticalBlock"] {
        gap: 10px !important;
    }

    .st-key-litlas_editor_card
    [data-testid="stHorizontalBlock"] {
        gap: 8px !important;
    }

    .st-key-litlas_editor_card
    [data-testid="stWidgetLabel"] {
        margin-bottom: 3px !important;
    }
}

/* ==========================================
   ADD A BOOK — COMPACT MOBILE FORM
   ========================================== */

@media screen and (max-width: 640px) {

    /* Row 1: title full width
       Row 2: author and country side by side */
    .st-key-litlas_add_book_identity
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 10px 8px !important;
        align-items: start !important;
    }

    .st-key-litlas_add_book_identity
    [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: none !important;
    }

    /* Book title occupies both columns */
    .st-key-litlas_add_book_identity
    [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:first-child {
        grid-column: 1 / -1;
    }

    /* Rating | Pages | Date */
    .st-key-litlas_add_book_details
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 6px !important;
        align-items: start !important;
    }

    .st-key-litlas_add_book_details [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) {
    grid-column: 1 / -1 !important;
    }
    
    .st-key-litlas_add_book_details
    [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: none !important;
    }

    /* Compact gaps inside both field groups */
    .st-key-litlas_add_book_identity
    [data-testid="stVerticalBlock"],
    .st-key-litlas_add_book_details
    [data-testid="stVerticalBlock"] {
        gap: 4px !important;
    }

    /* Allow inputs to shrink with their columns */
    .st-key-litlas_add_book_identity
    [data-testid="stColumn"] *,
    .st-key-litlas_add_book_details
    [data-testid="stColumn"] * {
        min-width: 0;
    }

    /* Smaller field labels */
    .st-key-litlas_add_book_identity
    [data-testid="stWidgetLabel"] p,
    .st-key-litlas_add_book_details
    [data-testid="stWidgetLabel"] p {
        font-size: 12px !important;
        line-height: 1.25 !important;
    }
}
/* Literary Collection — desktop retains original appearance */
.litlas-desktop-favourite-collection {
    display: block;
}

.litlas-mobile-favourite-collection {
    display: none;
}

@media screen and (max-width: 640px) {

    .litlas-desktop-favourite-collection {
        display: none !important;
    }

    .litlas-mobile-favourite-collection {
        display: block !important;
    }

    .litlas-mobile-favourite-section {
        border-bottom: 1px solid #D4C1A7;
        font-family: Georgia, serif;
        color: #58412F;
    }

    .litlas-mobile-favourite-section summary {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        padding: 12px 3px;
        cursor: pointer;
        list-style: none;
    }

    .litlas-mobile-favourite-section summary::-webkit-details-marker {
        display: none;
    }

    .litlas-mobile-favourite-heading {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        gap: 10px;
        font-size: 18px;
        font-weight: bold;
        color: #58412F;
    }

    .litlas-mobile-favourite-heading small {
        font-family: Georgia, serif;
        font-size: 12px;
        font-weight: normal;
        color: #81776E;
    }

    .litlas-mobile-favourite-chevron {
        font-size: 22px;
        color: #A47B43;
        transition: transform 0.2s ease;
    }

    .litlas-mobile-favourite-section[open]
    .litlas-mobile-favourite-chevron {
        transform: rotate(180deg);
    }

    .litlas-mobile-favourite-list {
        padding: 0 12px 14px;
    }

    .litlas-mobile-favourite-author {
        font-family: Georgia, serif;
        font-size: 14px;
        line-height: 1.6;
        padding: 3px 0;
        color: #58412F;
    }
}

/* Compact mobile dropdown menus */
@media screen and (max-width: 640px) {

    div[role="listbox"] {
        max-height: 190px !important;
        overflow-y: auto !important;
    }

    div[role="option"] {
        height: 32px !important;
        min-height: 32px !important;
        padding: 3px 8px !important;
        font-size: 13px !important;
        line-height: 1.2 !important;
        box-sizing: border-box !important;
    }
}
/* Library Management — compact mobile dropdowns */
@media screen and (max-width: 640px) {

    div[role="listbox"] {
        max-height: 240px !important;
        overflow-y: auto !important;
        -webkit-text-size-adjust: 100% !important;
        text-size-adjust: 100% !important;
    }

    div[role="option"] {
        height: 34px !important;
        min-height: 34px !important;
        padding: 3px 8px !important;
        font-family: Georgia, serif !important;
        font-size: 13px !important;
        line-height: 1.2 !important;
        box-sizing: border-box !important;
        -webkit-text-size-adjust: none !important;
        text-size-adjust: none !important;
    }

    div[role="option"] * {
        font-size: inherit !important;
        line-height: inherit !important;
    }
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


with st.container(key="litlas_library_navigation"):

    columns = st.columns(5, gap="small")

    for column, (name, symbol) in zip(columns, TOOLS):
        with column:
            selected = st.session_state.library_tool == name

            if st.button(
                name,
                icon=symbol,
                key="tool_add_book" if name == "Add a Book" else f"tool_{name}",
                type="primary" if selected else "secondary",
                width="stretch",
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


    elif selected_tool == "Favourites":
        st.subheader("Favourites")
        st.caption("A special place for the authors you treasure.")

        editor_col, collection_col = st.columns(
            [1.2, 1.8],
            gap="large",
        )

        with editor_col:
            with st.container(border=True, key="litlas_editor_card"):
                render_author_favourites()

        with collection_col:
            with st.container(key="literary_collection", gap="small"):
                st.markdown(
                    """
                    <h3 style="
                        margin: -50px 0 0;
                        padding: 0;
                        color: #58412F;
                    ">
                        My Literary Collection
                    </h3>
                    """,
                    unsafe_allow_html=True,
                )

                render_favourite_collection()

    elif selected_tool == "Author Details":
        st.subheader("Author Details")
        st.caption("Find, correct, or add authors to your literary atlas.")

        editor_col, _ = st.columns([1.2, 1.8], gap="large")

        with editor_col:
            with st.container(border=True, key="litlas_editor_card"):
                render_author_details()


    elif selected_tool == "Goodreads":
        st.subheader("Goodreads Library Sync")
        st.caption(
            "Compare your latest Goodreads export with Litlas. "
            "No database changes will be made."
        )


        if st.button(
            "Check for changes",
            key="goodreads_check_changes",
            type="secondary",
        ):
            try:
                st.session_state["goodreads_preview"] = (
                    preview_goodreads_import()
                )
            except (ValueError, OSError) as exc:
                st.session_state.pop("goodreads_preview", None)
                st.error(str(exc))


        preview = st.session_state.get("goodreads_preview")

        message = st.session_state.pop(
            "goodreads_resolution_message", None
        )
        if message:
            st.success(message)

        if preview is not None:
            source_name = Path(preview["source"]).name

            st.caption(f"Source: {source_name}")

            # ---------------------------------------------
            # Compact import summary
            # ---------------------------------------------
            summary = [
                ("New books", len(preview["new_books"])),
                ("Updates", len(preview["changed_books"])),
                ("Date conflicts", len(preview["date_conflicts"])),
                ("Unchanged", len(preview["unchanged_books"])),
            ]

            summary_html = "".join(
                f"""
                <div style="flex:1; text-align:center;">
                    <div style="
                        font-family:Georgia,serif;
                        font-size:21px;
                        color:#58412F;
                        line-height:1.2;
                    ">{count}</div>
                    <div style="
                        font-size:12px;
                        color:#81776E;
                        margin-top:3px;
                    ">{escape(label)}</div>
                </div>
                """
                for label, count in summary
            )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    gap:12px;
                    padding:12px 16px;
                    background:#F7F0E4;
                    border:1px solid #D4C1A7;
                    border-radius:8px;
                ">
                    {summary_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ---------------------------------------------
            # Compact date-conflict review
            # ---------------------------------------------
            conflicts = preview["date_conflicts"]

            if conflicts:
                with st.expander(
                    f"Reading-date conflicts ({len(conflicts)})",
                    expanded=False,):
                    rows = []

                    for conflict in conflicts:
                        litlas_date = pd.to_datetime(
                            conflict["litlas_date"],
                            errors="coerce",
                        )
                        goodreads_date = pd.to_datetime(
                            conflict["goodreads_date"],
                            errors="coerce",
                        )

                        def format_date(value):
                            if pd.isna(value):
                                return "Not recorded"
                            return (
                                f"{value.day} "
                                f"{value.strftime('%B %Y')}"
                            )

                        title = escape(conflict["title"])
                        litlas_text = escape(
                            format_date(litlas_date)
                        )
                        goodreads_text = escape(
                            format_date(goodreads_date)
                        )

                        rows.append(
                            f"""
                            <div style="
                                display:grid;
                                grid-template-columns:2fr 1fr 1fr;
                                gap:14px;
                                align-items:center;
                                padding:9px 4px;
                                border-bottom:1px solid #E4D6C5;
                                font-family:Georgia,serif;
                                font-size:13px;
                                color:#58412F;
                            ">
                                <div>{title}</div>
                                <div>{litlas_text}</div>
                                <div>{goodreads_text}</div>
                            </div>
                            """
                        )

                    table_html = f"""
                    <div style="
                        background:#F7F0E4;
                        border-radius:7px;
                        padding:6px 12px;
                    ">
                        <div style="
                            display:grid;
                            grid-template-columns:2fr 1fr 1fr;
                            gap:14px;
                            padding:8px 4px;
                            border-bottom:1px solid #C5AA87;
                            color:#81776E;
                            font-size:12px;
                        ">
                            <div>Book</div>
                            <div>Litlas</div>
                            <div>Goodreads</div>
                        </div>
                        {''.join(rows)}
                    </div>
                    """

                    st.markdown(
                        " ".join(dedent(table_html).split()),
                        unsafe_allow_html=True,
                    )


                # -----------------------------------------
                # Review and resolve one conflict
                # -----------------------------------------
                st.markdown("##### Review a conflict")

                conflict_options = {
                    conflict["book_id"]: conflict
                    for conflict in conflicts
                }

                selected_book_id = st.selectbox(
                    "Select a book",
                    options=list(conflict_options),
                    format_func=lambda book_id: (
                        conflict_options[book_id]["title"]
                    ),
                    index=None,
                    placeholder="Find a book to review...",
                    key="goodreads_conflict_book",
                )

                if selected_book_id is not None:
                    selected = conflict_options[selected_book_id]

                    litlas_date = pd.to_datetime(
                        selected["litlas_date"],
                        errors="coerce",
                    )
                    goodreads_date = pd.to_datetime(
                        selected["goodreads_date"],
                        errors="coerce",
                    )

                    left, right = st.columns(2)

                    with left:
                        st.caption("Litlas")
                        st.write(
                            litlas_date.strftime("%d %B %Y")
                            if pd.notna(litlas_date)
                            else "Not recorded"
                        )

                    with right:
                        st.caption("Goodreads")
                        st.write(
                            goodreads_date.strftime("%d %B %Y")
                            if pd.notna(goodreads_date)
                            else "Not recorded"
                        )

                    decision = st.radio(
                        "Which date is correct?",
                        [
                            "Keep Litlas date",
                            "Use Goodreads date",
                            "Decide later",
                        ],
                        index=2,
                        horizontal=True,
                        key=f"goodreads_date_choice_{selected_book_id}",
                    )

                    decision_codes = {
                        "Keep Litlas date": "keep_litlas",
                        "Use Goodreads date": "use_goodreads",
                    }

                    if decision != "Decide later":
                        if st.button(
                            "Save this decision",
                            key=f"save_date_resolution_{selected_book_id}",
                            type="secondary",
                        ):
                            try:
                                resolve_goodreads_date_conflict(
                                    book_id=selected_book_id,
                                    litlas_date=selected["litlas_date"],
                                    goodreads_date=selected["goodreads_date"],
                                    decision=decision_codes[decision],
                                    source=preview["source"],
                                )
                            except ValueError as exc:
                                st.error(str(exc))
                            else:
                                st.session_state["goodreads_preview"] = (
                                    preview_goodreads_import(
                                        preview["source"]
                                    )
                                )
                                st.session_state[
                                    "goodreads_resolution_message"
                                ] = (
                                    f"Resolved: {selected['title']} "
                                    f"— {decision}"
                                )
                                st.rerun()


            
            elif (
                not preview["new_books"]
                and not preview["changed_books"]
            ):
                st.success("No differences found.")

            if preview["new_books"]:
                with st.expander(
                    f"New books ({len(preview['new_books'])})"
                ):
                    for book in preview["new_books"]:
                        st.write(
                            f"{book['Title']} — {book['Author']}"
                        )

            if preview["changed_books"]:
                with st.expander(
                    f"Other updates ({len(preview['changed_books'])})"
                ):
                    for book in preview["changed_books"]:
                        st.write(
                            book["title"],
                            book["changes"],
                        )

            if preview["new_authors"]:
                with st.expander(
                    f"New authors ({len(preview['new_authors'])})"
                ):
                    for author in preview["new_authors"]:
                        st.write(author)
