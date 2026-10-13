"""Non-destructive cleaning of Goodreads book titles."""

import re

SERIES_SUFFIX = re.compile(
    r"\s+\([^()]*?(?:,\s*|\s+)#\d+" r"(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\)\s*$"
)

EDITION_SUFFIX = re.compile(
    r"\s*\((?:Spanish Edition|English Edition|French Edition|"
    r"German Edition|Kindle Edition)\)\s*$",
    re.IGNORECASE,
)

PUBLISHER_SERIES = re.compile(
    r"\s*\(Best Illustrated Books Book \d+\)\s*$",
    re.IGNORECASE,
)

LAYOUT_SUFFIX = re.compile(
    r"\s*\(perfect layout,\s*illustrated,\s*annotated\)\s*$",
    re.IGNORECASE,
)

BILINGUAL_SERIES = re.compile(
    r"\s*\(Listos Para Aprender\s*/\s*Ready to Learn\)\s*$",
    re.IGNORECASE,
)


def clean_title(title: str, remove_subtitles: bool = False) -> str:
    """Clean display text without altering the original title."""
    if not isinstance(title, str):
        return ""

    title = " ".join(title.split())

    patterns = (
        SERIES_SUFFIX,
        EDITION_SUFFIX,
        PUBLISHER_SERIES,
        LAYOUT_SUFFIX,
        BILINGUAL_SERIES,
    )

    while True:
        cleaned = title
        for pattern in patterns:
            cleaned = pattern.sub("", cleaned).strip()
        if cleaned == title:
            break
        title = cleaned

    if remove_subtitles:
        title = title.split(":", maxsplit=1)[0].strip()

    return title
