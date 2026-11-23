
"""Owner-only editor for The Unforgotten collection."""

import streamlit as st

from litlas.db_backend import get_repository, is_postgres


def render_unforgotten_editor() -> None:
    """Add, edit, hide, reorder, and delete literary characters."""

    st.subheader("The Unforgotten")
    st.caption("A collection of characters who remain with us.")

    if not is_postgres():
        st.info("The Unforgotten editor requires PostgreSQL.")
        return

    repo = get_repository()

    try:
        characters = repo.get_unforgotten_characters(
            include_hidden=True
        )
        books = repo.load_read_books()
    except Exception as exc:
        st.error(f"Unable to load The Unforgotten: {exc}")
        return

    work_options = {}

    for _, book in books.iterrows():
        work_id = book.get("Work ID")
        if work_id is None or str(work_id) == "nan":
            continue

        work_id = str(work_id)
        title = str(book["Work Title"])
        author = str(book["Author"])

        work_options[work_id] = f"{title} — {author}"

    if not work_options:
        st.warning("No literary works are available.")
        return

    work_ids = sorted(
        work_options,
        key=lambda wid: work_options[wid].casefold(),
    )

    character_by_id = {
        int(item["id"]): item for item in characters
    }

    st.caption(
        f"{len(characters)} characters · "
        f"{sum(bool(c['is_visible']) for c in characters)} visible"
    )

    choices = [0] + list(character_by_id)

    def character_label(character_id):
        if character_id == 0:
            return "＋ Add new character"

        item = character_by_id[character_id]
        suffix = "" if item["is_visible"] else " (hidden)"
        return f"{item['name']} — {item['book']}{suffix}"

    current_selection = st.session_state.get(
        "unforgotten_selection", 0
    )

    if current_selection not in choices:
        st.session_state["unforgotten_selection"] = 0

    selected_id = st.selectbox(
        "Choose a character",
        choices,
        format_func=character_label,
        key="unforgotten_selection",
    )

    item = character_by_id.get(selected_id)

    default_work = item["work_id"] if item else work_ids[0]
    if default_work not in work_ids:
        st.error("The selected character's work is unavailable.")
        return

    next_order = max(
        (int(c["display_order"]) for c in characters),
        default=0,
    ) + 1

    # Each character gets distinct widget keys so that switching
    # records loads its own values rather than retaining old inputs.
    prefix = f"unforgotten_{selected_id}"

    with st.form(f"{prefix}_form"):
        left, right = st.columns(2)

        with left:
            name = st.text_input(
                "Character name",
                value=item["name"] if item else "",
                key=f"{prefix}_name",
            )

        with right:
            familiar_name = st.text_input(
                "Familiar name",
                value=(item["familiar_name"] or "") if item else "",
                key=f"{prefix}_familiar",
            )

        work_id = st.selectbox(
            "Literary work",
            work_ids,
            index=work_ids.index(default_work),
            format_func=lambda wid: work_options[wid],
            key=f"{prefix}_work",
        )

        reflection = st.text_area(
            "Reflection or quotation",
            value=item["reflection"] if item else "",
            height=110,
            key=f"{prefix}_reflection",
        )

        reflection_type = st.radio(
            "Reflection type",
            ["personal", "quotation"],
            index=(
                1 if item and item["reflection_type"] == "quotation"
                else 0
            ),
            format_func=lambda value: (
                "My own words"
                if value == "personal"
                else "Literary quotation"
            ),
            horizontal=True,
            key=f"{prefix}_type",
        )

        col_order, col_visible = st.columns(2)

        with col_order:
            display_order = st.number_input(
                "Display order",
                min_value=0,
                value=(
                    int(item["display_order"])
                    if item else next_order
                ),
                step=1,
                key=f"{prefix}_order",
            )

        with col_visible:
            is_visible = st.checkbox(
                "Visible in Reading Statistics",
                value=bool(item["is_visible"]) if item else True,
                key=f"{prefix}_visible",
            )

        save = st.form_submit_button(
            "Save character",
            type="primary",
            use_container_width=True,
        )

    if save:
        if not name.strip():
            st.error("Please enter a character name.")
        elif not reflection.strip():
            st.error("Please enter a reflection.")
        else:
            try:
                details = dict(
                    work_id=work_id,
                    name=name,
                    familiar_name=familiar_name,
                    reflection=reflection,
                    reflection_type=reflection_type,
                    display_order=int(display_order),
                    is_visible=is_visible,
                )

                if item:
                    repo.update_unforgotten_character(
                        character_id=selected_id,
                        **details,
                    )
                else:
                    repo.add_unforgotten_character(**details)

                st.session_state.pop(
                    "unforgotten_delete_id", None
                )
                st.success("Character saved successfully.")
                st.rerun()

            except Exception as exc:
                st.error(f"Unable to save character: {exc}")

    if item:
        st.divider()

        pending_delete = st.session_state.get(
            "unforgotten_delete_id"
        )

        if pending_delete == selected_id:
            st.warning(
                f"Permanently delete {item['name']}?"
            )

            confirm, cancel = st.columns(2)

            with confirm:
                if st.button(
                    "Confirm deletion",
                    type="primary",
                    key=f"{prefix}_confirm_delete",
                    use_container_width=True,
                ):
                    try:
                        repo.delete_unforgotten_character(
                            selected_id
                        )
                        st.session_state[
                            "unforgotten_selection"
                        ] = 0
                        st.session_state.pop(
                            "unforgotten_delete_id", None
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Unable to delete: {exc}")

            with cancel:
                if st.button(
                    "Cancel",
                    key=f"{prefix}_cancel_delete",
                    use_container_width=True,
                ):
                    st.session_state.pop(
                        "unforgotten_delete_id", None
                    )
                    st.rerun()

        else:
            if st.button(
                "Delete character",
                key=f"{prefix}_delete",
            ):
                st.session_state[
                    "unforgotten_delete_id"
                ] = selected_id
                st.rerun()
