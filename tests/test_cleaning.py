import pytest

from litlas.processing.cleaning import clean_title

@pytest.mark.parametrize(
    "original,expected",
    [
        (
            "Emily Wilde's Encyclopaedia of Faeries (Emily Wilde, #1)",
            "Emily Wilde's Encyclopaedia of Faeries",
        ),
        (
            "All Creatures Great and Small (All Creatures Great and Small, #1-2)",
            "All Creatures Great and Small",
        ),
        (
            "The Moth Catcher (Vera Stanhope #7)",
            "The Moth Catcher",
        ),
        (
            "Farewell, My Lovely (Philip Marlowe, #2)",
            "Farewell, My Lovely",
        ),
        (
            "Superforecasting: The Art and Science of Prediction",
            "Superforecasting: The Art and Science of Prediction",
        ),
        (
            "Nirmal Verma: कव्वे और काला पानी",
            "Nirmal Verma: कव्वे और काला पानी",
        ),
    ],
)
def test_clean_title(original, expected):
    assert clean_title(original) == expected


def test_remove_everything_after_opening_parenthesis():
    assert (
        clean_title("A Short Life of Abraham Lincoln (Condensed from Nicolay & Hay")
        == "A Short Life of Abraham Lincoln"
    )

    assert clean_title("Example (Part One) The Rest") == "Example"


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            "Vera Wong's Guide to Snooping [On a Dead Man]",
            "Vera Wong's Guide to Snooping",
        ),
        (
            "A Short Life of Abraham Lincoln (Condensed from Nicolay",
            "A Short Life of Abraham Lincoln",
        ),
        (
            "Example [Special Edition]",
            "Example",
        ),
    ],
)
def test_bracket_cleanup(original, expected):
    assert clean_title(original) == expected


@pytest.mark.parametrize(
    "original,expected",
    [
        (
            "Enojado, Frustrado Y Triste / Mad, Frustrated, And Sad "
            "(Listos Para Aprender / Ready to Learn) (Spanish Edition)",
            "Enojado, Frustrado Y Triste",
        ),
        (
            "My Confession (perfect layout, illustrated, annotated) "
            "(Best Illustrated Books Book 24)",
            "My Confession",
        ),
        (
            "A Gentleman in Moscow",
            "A Gentleman in Moscow",
        ),
    ],
)
def test_edition_cleanup(original, expected):
    assert clean_title(original) == expected


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            "Enojado, Frustrado Y Triste / Mad, Frustrated, "
            "And Sad (Spanish Edition)",
            "Enojado, Frustrado Y Triste",
        ),
        (
            "Los tres cerditos / The Three Little Pigs " "(Bilingual Tales)",
            "Los tres cerditos",
        ),
        (
            "Stop Overthinking: 23 Techniques to Relieve Stress",
            "Stop Overthinking",
        ),
        (
            "The Hitchhiker's Guide to Python: " "Best Practices for Development",
            "The Hitchhiker's Guide to Python",
        ),
        (
            "The Cat Who Solved Three Murders " "(Conrad the Cat Detective #2)",
            "The Cat Who Solved Three Murders",
        ),
    ],
)
def test_display_title_cleanup(original, expected):
    assert (
        clean_title(
            original,
            remove_subtitles=True,
        )
        == expected
    )


def test_preserve_unrelated_slashes():
    assert (
        clean_title(
            "An English / French Dictionary",
            remove_subtitles=True,
        )
        == "An English"
    )
