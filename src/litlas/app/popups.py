from html import escape

import pandas as pd
import pycountry

def flag(code):
    try:
        a = pycountry.countries.get(alpha_3=code)
        if not a:
            return "📍"
        return "".join(chr(127397 + ord(c)) for c in a.alpha_2)
    except (AttributeError, TypeError):
        return "📍"


def pop_html(group, name, code):
    grouped = []

    for author, items in sorted(
        group.groupby("Author"), key=lambda pair: pair[0].casefold()
    ):
        lines = []

        for work_id, records in items.groupby("Work ID", sort=False):
            book = records.iloc[0]
            title = escape(str(book["Work Title"]))

            volumes = records.loc[records["Volume"].ne("")].copy()

            if not volumes.empty:
                lines.append(f'<div class="work-title">{title}</div>')

                volumes["Volume Number"] = pd.to_numeric(
                    volumes["Volume"].str.extract(r"(\d+)")[0],
                    errors="coerce",
                )

                volumes = volumes.sort_values("Volume Number")

                for _, volume in volumes.iterrows():
                    stars = format_rating(volume["My Rating"])

                    lines.append(
                        f'<div class="book">'
                        f'<span>{escape(str(volume["Volume"]))}</span>'
                        f'<span class="rating">{stars}</span>'
                        f"</div>"
                    )
            else:
                ratings = sorted(
                    set(float(r) for r in records["My Rating"] if float(r) > 0)
                )

                if len(records) == 1:
                    record = records.iloc[0]

                    # Experiment: only the Morocco test book.
                    is_test_book = (
                        code == "MAR"
                        and str(record["Work Title"]).strip().casefold()
                        == "litlas-book"
                        and str(record["Author"]).strip().casefold()
                        == "litlas-author"
                    )

                    rating_text = format_rating(
                        record["My Rating"],
                        book_id=(
                            str(record["Book Id"])
                            if is_test_book else None
                        ),
                    )

                elif len(ratings) == 1:
                    rating_text = format_rating(ratings[0])
                elif len(ratings) > 1:
                    rating_text = "Multiple ratings"
                else:
                    rating_text = format_rating(None)

                lines.append(
                    f'<div class="book">'
                    f"<span>{title}</span>"
                    f'<span class="rating">{rating_text}</span>'
                    f"</div>"
                )

        grouped.append(f"<h4>{escape(author)}</h4>" + "".join(lines))

    unique_works = group["Work ID"].nunique()

    return f"""
    <div class="litlas-country-popup" style="
        font-family:system-ui,sans-serif;
        color:#222;">
        <h3>{flag(code)} {escape(name)}</h3>
        <div style="color:#777;font-size:12px">
            {group['Author'].nunique()} authors ·
            {unique_works} works
        </div>
        {''.join(grouped)}
    </div>
    <style>
        h4 {{
            font-size:14px;
            margin:11px 0 6px;
            border-bottom:1px solid #eee;
        }}
        .work-title {{
            font-weight:600;
            margin:12px 0 8px;
        }}
        .book {{
            display:flex;
            justify-content:space-between;
            gap:12px;
            margin:5px 0;
            font-size:12px;
            line-height:1.35;
        }}
        .rating {{
            white-space:nowrap;
            color:#b57b13;
        }}
        .star-rating {{
            display: inline-block;
            font-family: Arial, sans-serif;
            font-size: 14px;
            letter-spacing: 0;
            white-space: nowrap;
            background: linear-gradient(
                to right,
                #b57b13 var(--rating-fill),
                #DDD5C9 var(--rating-fill)
            );
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .book > span:first-child {{
            flex: 1;
            min-width: 0;
            overflow-wrap: anywhere;
        }}

        .book .rating {{
            flex-shrink: 0;
        }}

        .litlas-country-popup {{
            width: 340px;
            max-height: 370px;
            overflow-y: auto;
            overflow-x: hidden;
        }}

        @media screen and (max-width: 640px) {{
            .litlas-country-popup {{
                width: 200px;
                max-height: 260px;
            }}
        }}
        .litlas-interactive-stars {{
            display: inline-block;
            cursor: pointer;
            touch-action: none;
            padding: 10px 0;
            user-select: none;
            -webkit-user-select: none;
            -webkit-tap-highlight-color: transparent;
        }}

        .litlas-interactive-stars:hover {{
            filter: brightness(1.1);
        }}
    </style>
    """
def format_rating(value, book_id=None):
    rating = pd.to_numeric(value, errors="coerce")

    if pd.isna(rating) or rating <= 0:
        rating = 0.0
    else:
        rating = max(0.0, min(5.0, float(rating)))

    percentage = rating / 5 * 100
    attributes = 'class="star-rating" '

    if book_id is not None:
        # Calculate the nearest half-star from pointer position.
        calculate = """
            const box = this.getBoundingClientRect();
            const fraction = Math.max(
                0, Math.min(1, (event.clientX - box.left) / box.width)
            );
            const selected = Math.max(
                0.5, Math.min(5, Math.ceil(fraction * 10) / 2)
            );
        """

        preview_js = calculate + """
            this.style.setProperty(
                '--rating-fill', (selected / 5 * 100) + '%'
            );
        """

        restore_js = """
            this.style.setProperty(
                '--rating-fill', this.dataset.originalFill
            );
        """

        submit_js = calculate + """
            event.preventDefault();
            event.stopPropagation();

            this.style.setProperty(
                '--rating-fill',
                (selected / 5 * 100) + '%'
            );

            window.parent.postMessage({
                type: 'litlas-rating-test',
                book_id: this.dataset.bookId,
                rating: selected
            }, '*');
        """
        touch_js = """
            event.preventDefault();
            event.stopPropagation();

            const touch = event.touches[0];
            if (!touch) return;

            const box = this.getBoundingClientRect();
            const fraction = Math.max(
                0,
                Math.min(1, (touch.clientX - box.left) / box.width)
            );

            const selected = Math.max(
                0.5,
                Math.min(5, Math.ceil(fraction * 10) / 2)
            );

            this.style.setProperty(
                '--rating-fill',
                (selected / 5 * 100) + '%'
            );

            window.parent.postMessage({
                type: 'litlas-rating-test',
                book_id: this.dataset.bookId,
                rating: selected
            }, '*');
        """

        attributes = (
            'class="star-rating litlas-interactive-stars" '
            f'data-book-id="{escape(str(book_id), quote=True)}" '
            f'data-original-fill="{percentage}%" '
            f'onpointermove="{escape(preview_js, quote=True)}" '
            f'onpointerleave="if (event.pointerType === \'mouse\') {{ {escape(restore_js, quote=True)} }}" '
            f'ontouchstart="{escape(touch_js, quote=True)}" '
            f'onclick="{escape(submit_js, quote=True)}" '
        )

    label = (
        f"{rating:g} out of 5 stars"
        if rating else "Not rated"
    )

    return (
        f'<span {attributes}'
        f'style="--rating-fill:{percentage}%;" '
        f'aria-label="{label}">'
        '★★★★★'
        '</span>'
    )