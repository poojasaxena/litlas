"""Reading Density choropleth and the atlas map's view switch."""

from html import escape
from math import log1p

from branca.colormap import LinearColormap
from branca.element import Element, MacroElement
import folium
from jinja2 import Template

from litlas.app.map_style import BORDER_COLOR, DENSITY_COLORS, LAND_COLOR
from litlas.app.popups import pop_html
from litlas.processing.countries import country_name, load_simplified_country_boundaries


def add_reading_density(m, books, *, show=True):
    """Add the choropleth and legend using the same distinct-work count as SQL."""
    mapped_books = books.loc[books["ISO3"].notna() & books["ISO3"].ne("")]
    counts = mapped_books.groupby("ISO3")["Work ID"].nunique().to_dict()
    if not counts:
        return None

    max_count = max(counts.values())
    if not max_count:
        return None

    colors = LinearColormap(
        colors=DENSITY_COLORS,
        vmin=0,
        vmax=log1p(max_count),
    )

    geojson = load_simplified_country_boundaries()

    books_by_country = {iso: group for iso, group in books.groupby("ISO3")}

    for feature in geojson["features"]:
        props = feature["properties"]
        iso = props.get("ISO3166-1-Alpha-3", "")
        count = int(counts.get(iso, 0))

        fallback = props.get("ADMIN") or props.get("name")

        if fallback == "-99":
            fallback = None

        name = country_name(iso, fallback=fallback)

        props["litlas_country"] = name
        props["litlas_works"] = count

        if count > 0 and iso in books_by_country:
            props["litlas_popup"] = pop_html(
                books_by_country[iso],
                name,
                iso,
            )
        else:
            props["litlas_popup"] = (
                f"<strong>{escape(str(name))}</strong>" "<div>No mapped works</div>"
            )


    def style_country(feature):
        count = feature["properties"]["litlas_works"]

        return {
            "fillColor": (
                colors(log1p(count))
                if count > 0
                else LAND_COLOR
            ),
            "fillOpacity": 1,
            "color": BORDER_COLOR,
            "weight": 0.5,
            "opacity": 1,
        }


    layer = folium.GeoJson(
        geojson,
        name="Reading density",
        show=show,
        style_function=style_country,
        tooltip=folium.GeoJsonTooltip(
            fields=["litlas_country"],
            aliases=[""],
            labels=False,
            sticky=True,
        ),
    ).add_to(m)

    folium.GeoJsonPopup(
        fields=["litlas_popup"],
        labels=False,
        localize=False,
        max_width=400,
        style=(
            "border:0;"
            "font-family:system-ui,sans-serif;"
            "font-size:12px;"
            "line-height:1.35;"
        ),
    ).add_to(layer)

    # Compact reading-density legend inside the map
    legend_counts = sorted(
        {count for count in (1, 5, 15, 50, max_count) if count <= max_count}
    )

    legend_segments = "".join(
        f'<div style="flex:1;background:{colors(log1p(count))};"></div>'
        for count in legend_counts
    )

    legend_labels = "".join(
        f"<span>{count}</span>"
        for count in legend_counts
    )

    legend_html = f"""
    <div class="litlas-density-legend"
         {"" if show else "hidden"} style="
        position:fixed;
        bottom:2px;
        right:2px;
        width:180px;
        padding:6px 8px;
        background:rgba(250,247,241,0.93);
        border:1px solid #D4C1A7;
        border-radius:7px;
        box-shadow:0 2px 8px rgba(0,0,0,0.12);
        z-index:1000;
        font-family:Georgia,serif;
        color:#58412F;
    ">
        <div style="font-size:13px;margin-bottom:7px;">
            Reading density
        </div>
        <div style="display:flex;height:12px;">
            {legend_segments}
        </div>
        <div style="
            display:flex;
            justify-content:space-between;
            font-size:11px;
            margin-top:4px;
        ">
            {legend_labels}
        </div>
    </div>
    """
    # Mobile styling for the Reading Density legend
    m.get_root().header.add_child(Element("""
    <style>
    @media screen and (max-width: 640px) {
        .litlas-density-legend {
            bottom: 2px !important;
            right: 2px !important;
            width: 120px !important;
            padding: 5px 6px !important;
            box-sizing: border-box !important;
            background: rgba(250, 247, 241, 0.98) !important;
        }

        /* Title */
        .litlas-density-legend > div:first-child {
            font-size: 11px !important;
            margin-bottom: 5px !important;
        }

        /* Colour bar */
        .litlas-density-legend > div:nth-child(2) {
            height: 9px !important;
        }

        /* Legend numbers */
        .litlas-density-legend > div:last-child {
            font-size: 9px !important;
            margin-top: 3px !important;
        }
    }
    </style>
    """))

    # Insert the legend into the Folium map
    m.get_root().html.add_child(Element(legend_html))
    return layer


class ReadingDensitySwitch(MacroElement):
    """Switch both map layers together while keeping the current Leaflet view."""

    _template = Template("""
        {% macro script(this, kwargs) %}
        (() => {
            const map = {{ this._parent.get_name() }};
            const flags = {{ this.flags.get_name() }};
            const density = {{ this.density.get_name() }};
            const legend = document.querySelector(".litlas-density-legend");
            const journey = document.querySelector(".litlas-journey-card");
            const explorer = map.getContainer().querySelector(".litlas-explorer-control");

            const control = L.control({position: "topright"});
            control.onAdd = () => {
                const compact = {{ this.compact | tojson }};
                const panel = L.DomUtil.create("div", "litlas-density-switch");
                panel.setAttribute("role", "group");
                panel.setAttribute("aria-label", "Map view");

                function button(label) {
                    const item = L.DomUtil.create("button", "", panel);
                    item.type = "button";
                    item.textContent = label;
                    return item;
                }

                const flagButton = compact ? null : button("Flags");
                const densityButton = button(compact ? "Reading density" : "Density");
                let enabled = false;

                function selectDensity(next) {
                    if (enabled !== next) {
                        enabled = next;
                        map.closePopup();
                        map.removeLayer(enabled ? flags : density);
                        map.addLayer(enabled ? density : flags);
                        if (legend) legend.hidden = !enabled;
                        if (journey) journey.hidden = enabled;
                        if (explorer) explorer.hidden = enabled;
                    }
                    if (flagButton) flagButton.setAttribute("aria-pressed", String(!enabled));
                    densityButton.setAttribute("aria-pressed", String(enabled));
                }

                if (flagButton) {
                    flagButton.addEventListener("click", () => selectDensity(false));
                }
                densityButton.addEventListener("click", () => {
                    selectDensity(compact ? !enabled : true);
                });
                selectDensity(false);

                L.DomEvent.disableClickPropagation(panel);
                L.DomEvent.disableScrollPropagation(panel);
                return panel;
            };

            control.addTo(map);
        })();
        {% endmacro %}
    """)

    def __init__(self, flags, density, *, compact=False):
        super().__init__()
        self.flags = flags
        self.density = density
        self.compact = compact

    def render(self, **kwargs):
        self.get_root().header.add_child(Element("""
            <style>
            .litlas-density-switch {
                display: inline-flex;
                border: 1px solid #D4C1A7;
                border-radius: 6px;
                background: #FAF7F1;
                overflow: hidden;
            }
            .litlas-density-switch button {
                min-height: 44px;
                padding: 0 11px;
                border: 0;
                background: transparent;
                color: #58412F;
                font: 14px Georgia, serif;
                white-space: nowrap;
                cursor: pointer;
            }
            .litlas-density-switch button + button {
                border-left: 1px solid #D4C1A7;
            }
            .litlas-density-switch button[aria-pressed="true"] {
                background: #E6D8C3;
                font-weight: 700;
            }
            .litlas-density-switch button:focus-visible {
                outline: 2px solid #795740;
                outline-offset: -3px;
            }
            .litlas-explorer-control[hidden] {
                display: none;
            }

            @media (max-width: 640px) {
                .leaflet-control-zoom {
                    display: none;
                }

                .litlas-explorer-control {
                    left: 2px;
                    margin-top: 2px !important;
                }

                .leaflet-top.leaflet-right .litlas-density-switch {
                    margin-top: 2px;
                    margin-right: 2px;
                }

                .litlas-density-switch button {
                    min-height: 28px; /* 34 px including the surrounding border */
                    padding: 0 6px;
                    font-size: 10px;
                }
            }
            </style>
        """))
        super().render(**kwargs)
