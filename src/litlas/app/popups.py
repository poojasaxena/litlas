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

            # Respect personal title edits for individual reading records.
            if len(records) == 1:
                title = escape(str(book["Display Title"]))
            else:
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
                    stars = format_rating(
                        volume["My Rating"],
                        book_id=str(volume["Book Id"]),
                    )

                    lines.append(
                        f'<div class="book">'
                        f'<span>{escape(str(volume["Volume"]))}</span>'
                        f'<span class="rating">{stars}</span>'
                        f"</div>"
                    )
            else:
                if len(records) == 1:
                    record = records.iloc[0]

                    rating_text = format_rating(
                        record["My Rating"],
                        book_id=str(record["Book Id"]),
                    )

                    lines.append(
                        f'<div class="book">'
                        f"<span>{title}</span>"
                        f'<span class="rating">{rating_text}</span>'
                        f"</div>"
                    )

                else:
                    # Multiple reading records for one work.
                    # Each record must have its own rating control.
                    lines.append(
                        f'<div class="work-title">{title}</div>'
                    )

                    for reading_number, (_, record) in enumerate(
                        records.iterrows(), start=1
                    ):
                        rating_text = format_rating(
                            record["My Rating"],
                            book_id=str(record["Book Id"]),
                        )

                        lines.append(
                            f'<div class="book">'
                            f"<span>Reading {reading_number}</span>"
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
            padding: 1px 0;
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

    label = (
        f"{rating:g} out of 5 stars"
        if rating else "Not rated"
    )

    attributes = 'class="star-rating" '
    done_button = ""

    if book_id is not None:
        calculate = """
            const box = this.getBoundingClientRect();
            const fraction = Math.max(
                0,
                Math.min(1, (event.clientX - box.left) / box.width)
            );
            const selected = Math.max(
                0.5,
                Math.min(5, Math.ceil(fraction * 10) / 2)
            );
        """

        preview_js = calculate + """
            if (event.pointerType !== 'mouse') return;
            if (this.dataset.pendingRating) return;

            this.style.setProperty(
                '--rating-fill',
                (selected / 5 * 100) + '%'
            );
        """

        restore_js = """
            const pending = this.dataset.pendingRating;
            this.style.setProperty(
                '--rating-fill',
                pending
                    ? (Number(pending) / 5 * 100) + '%'
                    : this.dataset.originalFill
            );
        """

        select_js = calculate + """
            event.preventDefault();
            event.stopPropagation();

            this.dataset.pendingRating = selected;

            this.style.setProperty(
                '--rating-fill',
                (selected / 5 * 100) + '%'
            );

            const button = this.nextElementSibling;
            button.hidden = false;
            button.textContent = 'Done';
        """

        done_js = """
            event.preventDefault();
            event.stopPropagation();

            const stars = this.previousElementSibling;
            const selected = Number(stars.dataset.pendingRating);

            if (!selected) return;

            window.parent.postMessage({
                type: 'litlas-rating-test',
                book_id: stars.dataset.bookId,
                rating: selected
            }, '*');

            this.hidden = true;
        """

        attributes = (
            'class="star-rating litlas-interactive-stars" '
            f'data-book-id="{escape(str(book_id), quote=True)}" '
            f'data-original-fill="{percentage}%" '
            f'onpointermove="{escape(preview_js, quote=True)}" '
            f'onpointerleave="{escape(restore_js, quote=True)}" '
            f'onpointerup="{escape(select_js, quote=True)}" '
            'onclick="event.preventDefault();event.stopPropagation();" '
        )

        done_button = (
            '<button type="button" hidden '
            f'onclick="{escape(done_js, quote=True)}" '
            'style="'
            'margin-left:6px;'
            'padding:3px 7px;'
            'border:1px solid #B29A7C;'
            'border-radius:5px;'
            'background:#F5EFE4;'
            'color:#58412F;'
            'font:12px Georgia,serif;'
            'cursor:pointer;'
            'touch-action:manipulation;'
            '">'
            'Done'
            '</button>'
        )

    stars_html = (
        f'<span {attributes}'
        f'style="'
        f'--rating-fill:{percentage}%;'
        f'display:inline-block;'
        f'font-family:Arial,sans-serif;'
        f'font-size:14px;'
        f'letter-spacing:0;'
        f'white-space:nowrap;'
        f'background:linear-gradient('
        f'to right,'
        f'#b57b13 var(--rating-fill),'
        f'#DDD5C9 var(--rating-fill));'
        f'-webkit-background-clip:text;'
        f'background-clip:text;'
        f'-webkit-text-fill-color:transparent;'
        f'" '
        f'aria-label="{escape(label, quote=True)}">'
        '★★★★★'
        '</span>'
    )

    return stars_html + done_button

