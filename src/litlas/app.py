"""Minimal interactive literary map. Run: streamlit run app.py"""
from html import escape
from pathlib import Path
import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from countryinfo import CountryInfo
import pycountry
from litlas.core import enriched_books_path, load_config
import requests


## Configuration constants for the map and flag display
config = load_config()
map_config = config.get("map", {})

FLAG_SIZE = map_config.get("flag_size", 14)
MAP_HEIGHT = map_config.get("height", 800)
COUNTRY_FILL = map_config.get("country_fill", "#82BFA0")
COUNTRY_OPACITY = map_config.get("country_opacity", 0.25)


@st.cache_data
def load_country_boundaries():
    url = (
        "https://raw.githubusercontent.com/"
        "datasets/geo-countries/master/data/countries.geojson"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title='Literary Atlas',page_icon='🌍',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
        .block-container {max-width:1550px;padding-top:1.3rem;padding-bottom:1rem}
        #MainMenu,footer {visibility:hidden}
        [data-testid="stFileUploader"] {max-width:440px}
        </style>''',unsafe_allow_html=True)
st.title('🌍 Literary Atlas')
st.caption('A world of books, mapped by where their authors were born.')

# The map is display-only. Run `litlas-prepare` first.
source = enriched_books_path()
if not source.is_file():
    st.warning('No enriched CSV found. Run `litlas-prepare --no-lookup` first, then `litlas-prepare` for birthplace lookups.')
    st.stop()
try:
    books = pd.read_csv(source, keep_default_na=False, low_memory=False)
except Exception as exc:
    st.error(f'Could not read enriched CSV: {exc}')
    st.stop()
for field in ('Author','Title','ISO3','My Rating'):
    if field not in books.columns:
        st.error(f'Enriched CSV missing column: {field}')
        st.stop()
books['My Rating']=pd.to_numeric(books['My Rating'],errors='coerce').fillna(0).astype(int)
mapped=books[books['ISO3'].astype(bool)].copy()

# Approximate marker anchors; CountryInfo includes packaged offline geographic coordinates.
SPECIAL={'XKX':[42.6,21.0], 'TWN':[23.7,121.0], 'PSE':[31.9,35.2]}
def locate(iso):
    if iso in SPECIAL:return SPECIAL[iso]
    try:
        country=pycountry.countries.get(alpha_3=iso)
        if country is None:return None
        return CountryInfo(country.name).latlng()
    except (KeyError,ValueError,AttributeError,TypeError):
        try:
            aliases={'USA':'United States','GBR':'United Kingdom','KOR':'South Korea','RUS':'Russia', 'CZE':'Czech Republic', 'IRN':'Iran'}
            return CountryInfo(aliases.get(iso,iso)).latlng()
        except (KeyError,ValueError,AttributeError,TypeError):return None

def flag(code):
    try:
        a=pycountry.countries.get(alpha_3=code)
        if not a:return '📍'
        return ''.join(chr(127397+ord(c)) for c in a.alpha_2)
    except (AttributeError,TypeError): return '📍'

def pop_html(group, name, code):
    grouped = []

    for author, items in sorted(
        group.groupby("Author"),
        key=lambda pair: pair[0].casefold()
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
                    rating = int(volume["My Rating"])

                    stars = (
                        "★" * rating + "☆" * (5 - rating) if 1 <= rating <= 5 else "Not rated"
                    )

                    lines.append(
                        f'<div class="book">'
                        f'<span>{escape(volume["Volume"])}</span>'
                        f'<span class="rating">{stars}</span>'
                        f"</div>"
                    )

            else:
                ratings = sorted(set(int(r) for r in records["My Rating"] if int(r) > 0))

                if len(ratings) == 1:
                    rating_text = "★" * ratings[0] + "☆" * (5 - ratings[0])
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

        grouped.append(
            f'<h4>{escape(author)}</h4>' + "".join(lines)
        )

    unique_works = group["Work ID"].nunique()

    return f"""
    <div style="font-family:system-ui,sans-serif;
                width:340px;max-height:370px;
                overflow:auto;color:#222">
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
        
    </style>
    """

def pop_html_deprecated(group,name,code):
    count_books=len(group)
    grouped=[]
    for author,items in sorted(group.groupby('Author'),key=lambda pair:pair[0].casefold()):
        lines=[]
        for _,b in items.sort_values('Title').iterrows():
            rating=int(b['My Rating'])
            stars=(('★'*rating)+('☆'*(5-rating))) if 1<=rating<=5 else 'Not rated'
            lines.append(
                f'<div class="book">'
                f'<span>{escape(str(b["Display Title"]))}</span>'
                f'<span class="rating">{stars}</span>'
                f'</div>'
            )
        grouped.append(f'<h4>{escape(author)}</h4>'+''.join(lines))

    return f'''<div style="font-family:system-ui,sans-serif;width:340px;max-height:370px;overflow:auto;color:#222">
    <h3 style="margin:0 0 4px">{flag(code)} {escape(name)}</h3>
    <div style="color:#777;font-size:12px;margin-bottom:14px">{len(group['Author'].unique())} authors · {count_books} books</div>
    {''.join(grouped)}</div>
    <style>h4{{font-size:14px;margin:11px 0 6px;border-bottom:1px solid #eee;padding-bottom:5px}}.book{{display:flex;justify-content:space-between;gap:12px;margin:5px 0;font-size:12px;line-height:1.35}}.rating{{white-space:nowrap;color:#b57b13}}</style>'''

m = folium.Map(
    location=[15, 0],
    zoom_start=2,
    tiles="OpenStreetMap",
    control_scale=True,
    prefer_canvas=False,
    world_copy_jump=True,
    zoom_control=True,
)

m.fit_bounds([[-55, -170], [75, 180]])
read_countries = set(mapped["ISO3"].unique())

geojson = load_country_boundaries()

folium.GeoJson(
    geojson,
    name="Countries explored",
    style_function=lambda feature: {
        "fillColor": (
            COUNTRY_FILL
            if feature["properties"].get("ISO3166-1-Alpha-3") in read_countries
            else "transparent"
        ),
        "fillOpacity": (
            COUNTRY_OPACITY
            if feature["properties"].get("ISO3166-1-Alpha-3") in read_countries
            else 0
        ),
        "color": "#8A9A9F",
        "weight": 0.4,
        "opacity": 0.5,
    },
).add_to(m)

# cluster=MarkerCluster(name='Countries',disableClusteringAtZoom=4,showCoverageOnHover=False).add_to(m)
placed=0
for iso,group in mapped.groupby('ISO3',sort=True):
    position=locate(iso)
    if not position: continue
    c=pycountry.countries.get(alpha_3=iso)
    name=(c.name if c else iso)
    if iso=='USA':name='United States'
    if iso=='GBR':name='United Kingdom'

    html = f"""
    <div style="
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: {FLAG_SIZE}px;
        line-height: 1;
    ">
        {flag(iso)}
    </div>
    """

    folium.Marker(
        location=position,
        icon=folium.DivIcon(
            html=html,
            class_name="",
            icon_size=(20, 20),
            icon_anchor=(10, 10),
        ),
        popup=folium.Popup(
            pop_html(group, name, iso),
            max_width=400,
        ),
        tooltip=name,
    ).add_to(m)
    placed+=1
folium.LayerControl(position='topright').add_to(m)
st_folium(m,height=MAP_HEIGHT,use_container_width=True,returned_objects=[],key='literarymap')
if mapped.empty:
    st.info('No author birth countries assigned yet. Run `litlas-prepare` in your terminal, then refresh this page.')
elif placed==0:
    st.warning('Authors have country codes, but map coordinates were unavailable. Check Vault/Personal/Learning/Library/authors.csv.')
missing=books.loc[~books['ISO3'].astype(bool),'Author'].nunique()
st.caption(f'{len(books)} read books · {books["Author"].nunique()} authors · {placed} mapped countries · {missing} authors still without a mapped birth country. Birth-country matches are provisional until reviewed.')
