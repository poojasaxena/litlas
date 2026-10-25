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
                        f'<span>{escape(volume["Volume"])}</span>'
                        f'<span class="rating">{stars}</span>'
                        f"</div>"
                    )

            else:
                ratings = sorted(
                    set(float(r) for r in records["My Rating"] if float(r) > 0)
                )

                if len(ratings) == 1:
                    rating_text = format_rating(ratings[0])
                elif len(ratings) > 1:
                    rating_text = "Multiple ratings"
                else:
                    rating_text = "Not rated"

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
    </style>
    """


def format_rating(value):
    rating = float(value)

    if rating <= 0:
        return "Not rated"

    if rating.is_integer():
        stars = int(rating)
        return "★" * stars + "☆" * (5 - stars)

    return f"{rating:g}★"
