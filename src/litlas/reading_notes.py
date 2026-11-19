"""Shared field rules for personal reading notes."""

READING_NOTE_MAX_CHARS = 180


def normalize_reading_note(note: str | None) -> str | None:
    """Validate a note while preserving the difference between blank and omitted."""
    if note is None:
        return None

    note = note.strip()
    if len(note) > READING_NOTE_MAX_CHARS:
        raise ValueError(f"Reading note must be {READING_NOTE_MAX_CHARS} characters or fewer.")
    return note
