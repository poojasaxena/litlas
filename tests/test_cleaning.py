import pytest

from litlas.cleaning import clean_title


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


@pytest.mark.parametrize(
    "original,expected",
    [
        (
            "Enojado, Frustrado Y Triste / Mad, Frustrated, And Sad "
            "(Listos Para Aprender / Ready to Learn) (Spanish Edition)",
            "Enojado, Frustrado Y Triste / Mad, Frustrated, And Sad",
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
