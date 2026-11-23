"""Compact owner-only editor for The Unforgotten collection."""

import pandas as pd
import streamlit as st

from litlas.db_backend import get_repository, is_postgres


NEW_ENTRY_KEYS = (
    "name", "familiar", "work", "reflection", "type", "order", "visible"
)


def render_unforgotten_editor() -> None:
    """Add, edit, hide, reorder and delete literary characters."""

    if not is_postgres():
        st.info("The Unforgotten requires PostgreSQL.")
        return

    repo = get_repository()
    try:
        characters = repo.get_unforgotten_characters(include_hidden=True)
        books = repo.load_read_books()
    except Exception as exc:
        st.error(f"Unable to load The Unforgotten: {exc}")
        return

    work_options = {}
    for _, book in books.iterrows():
        work_id = book.get("Work ID")
        if pd.isna(work_id):
            continue
        work_options[str(work_id)] = (
            f"{book['Work Title']} — {book['Author']}"
        )

    if not work_options:
        st.warning("No literary works available.")
        return

    work_ids = sorted(work_options, key=lambda wid: work_options[wid].casefold())
    character_by_id = {int(item["id"]): item for item in characters}
    visible_count = sum(bool(c["is_visible"]) for c in characters)

    # A blank selector means a new character.  Reset widget state BEFORE
    # creating the selector or form widgets (Streamlit requires this).
    if st.session_state.pop("unforgotten_reset_form", False):
        st.session_state["unforgotten_selection"] = None
        for suffix in NEW_ENTRY_KEYS:
            st.session_state.pop(f"unforgotten_new_{suffix}", None)

    if st.session_state.get("unforgotten_selection") not in (
        None, *character_by_id.keys()
    ):
        st.session_state["unforgotten_selection"] = None

    def character_label(character_id: int) -> str:
        item = character_by_id[character_id]
        suffix = "" if item["is_visible"] else " (hidden)"
        return f"{item['name']} — {item['book']}{suffix}"

    st.subheader("The Unforgotten")

    st.markdown(
        """
        <style>
        .st-key-litlas_unforgotten_panel {
            max-width: 950px;
            width: 100%;
            background: #f8f0e4;
            border: 1px solid #ddc5a8;
            border-radius: 11px;
            padding: 16px 20px 18px;
            box-sizing: border-box;
        }
        .st-key-litlas_unforgotten_panel [data-testid="stVerticalBlock"] {
            gap: 0.65rem;
        }
        .st-key-litlas_unforgotten_panel [data-testid="stForm"] {
            border: none;
            padding: 0;
            background: transparent;
        }
        .st-key-litlas_unforgotten_panel [data-testid="stWidgetLabel"] {
            margin-bottom: 2px;
        }
        .st-key-litlas_unforgotten_panel div[data-testid="stCaptionContainer"] {
            margin: 0;
        }
        .st-key-litlas_unforgotten_panel [data-testid="stFormSubmitButton"] button {
            background: #90684f;
            color: white;
            border-color: #90684f;
        }
        @media (max-width: 768px) {
            .st-key-litlas_unforgotten_panel { padding: 12px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="litlas_unforgotten_panel"):
        col_select, col_count = st.columns(
            [3, 1], gap="small", vertical_alignment="bottom"
        )
        with col_select:
            selected_id = st.selectbox(
                "Edit an existing character (optional)",
                options=list(character_by_id),
                index=None,
                placeholder="Select a character to edit; otherwise add below...",
                format_func=character_label,
                key="unforgotten_selection",
            )
        with col_count:
            st.caption(f"{len(characters)} characters · {visible_count} visible")

        item = character_by_id.get(selected_id)
        next_order = max(
            (int(c["display_order"]) for c in characters), default=0
        ) + 1
        prefix = f"unforgotten_{selected_id}" if item else "unforgotten_new"
        default_work = str(item["work_id"]) if item else None

        with st.form(f"{prefix}_form", clear_on_submit=False, border=False):
            col_name, col_familiar, col_work = st.columns(3, gap="small")
            with col_name:
                name = st.text_input(
                    "Character name",
                    value=item["name"] if item else "",
                    placeholder="Enter character name...",
                    key=f"{prefix}_name",
                )
            with col_familiar:
                familiar_name = st.text_input(
                    "Familiar name",
                    value=(item["familiar_name"] or "") if item else "",
                    placeholder="Optional...",
                    key=f"{prefix}_familiar",
                )
            with col_work:
                work_id = st.selectbox(
                    "Literary work",
                    work_ids,
                    index=(
                        work_ids.index(default_work)
                        if default_work in work_ids else None
                    ),
                    placeholder="Find a book...",
                    format_func=lambda wid: work_options[wid],
                    key=f"{prefix}_work",
                )

            reflection = st.text_input(
                "Reflection or quotation",
                value=item["reflection"] if item else "",
                placeholder="One thought or memorable line...",
                key=f"{prefix}_reflection",
            )

            col_type, col_order, col_visible = st.columns(
                [2, 1, 1], gap="small", vertical_alignment="bottom"
            )
            with col_type:
                reflection_type = st.radio(
                    "Reflection type",
                    ["personal", "quotation"],
                    index=(
                        1 if item and item["reflection_type"] == "quotation"
                        else 0
                    ),
                    format_func=lambda value: (
                        "My words" if value == "personal" else "Quotation"
                    ),
                    horizontal=True,
                    key=f"{prefix}_type",
                )
            with col_order:
                display_order = st.number_input(
                    "Display order",
                    min_value=0,
                    value=int(item["display_order"]) if item else next_order,
                    step=1,
                    key=f"{prefix}_order",
                )
            with col_visible:
                is_visible = st.checkbox(
                    "Visible",
                    value=bool(item["is_visible"]) if item else True,
                    key=f"{prefix}_visible",
                )

            _, delete_col, save_col, message_col, _ = st.columns(
                [1.5, 1, 1, 0.8, 1.5],
                gap="small",
                vertical_alignment="center",
            )
            with delete_col:
                delete_requested = st.form_submit_button(
                    "Delete", disabled=item is None, width="stretch"
                )
            with save_col:
                save_requested = st.form_submit_button(
                    "Save", type="secondary", width="stretch"
                )
            with message_col:
                message = st.session_state.pop("unforgotten_message", None)
                if message:
                    st.markdown(
                        f'<span style="color:#90684f;font-size:13px;'
                        f'white-space:nowrap;">✓ {message}</span>',
                        unsafe_allow_html=True,
                    )

        if save_requested:
            if not name.strip():
                st.error("Please enter a character name.")
            elif not work_id:
                st.error("Please select a literary work.")
            elif not reflection.strip():
                st.error("Please enter a reflection.")
            else:
                details = dict(
                    work_id=work_id,
                    name=name.strip(),
                    familiar_name=familiar_name.strip() or None,
                    reflection=reflection.strip(),
                    reflection_type=reflection_type,
                    display_order=int(display_order),
                    is_visible=is_visible,
                )
                try:
                    if item:
                        repo.update_unforgotten_character(
                            character_id=selected_id, **details
                        )
                    else:
                        repo.add_unforgotten_character(**details)
                except Exception as exc:
                    st.error(f"Unable to save character: {exc}")
                else:
                    st.session_state["unforgotten_reset_form"] = True
                    st.session_state.pop("unforgotten_delete_id", None)
                    st.session_state["unforgotten_message"] = "Saved"
                    st.rerun()

        if delete_requested and item:
            st.session_state["unforgotten_delete_id"] = selected_id

        if item and st.session_state.get("unforgotten_delete_id") == selected_id:
            st.caption(f"Permanently delete {item['name']}?")
            _, confirm_col, cancel_col, _ = st.columns(
                [2, 1, 1, 2], gap="small"
            )
            with confirm_col:
                if st.button(
                    "Confirm", key=f"{prefix}_confirm", width="stretch"
                ):
                    try:
                        repo.delete_unforgotten_character(selected_id)
                    except Exception as exc:
                        st.error(f"Unable to delete: {exc}")
                    else:
                        st.session_state["unforgotten_reset_form"] = True
                        st.session_state.pop("unforgotten_delete_id", None)
                        st.session_state["unforgotten_message"] = "Deleted"
                        st.rerun()
            with cancel_col:
                if st.button(
                    "Cancel", key=f"{prefix}_cancel", width="stretch"
                ):
                    st.session_state.pop("unforgotten_delete_id", None)
                    st.rerun()
