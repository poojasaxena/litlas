
"""Compact unexplored-country control inside the Literary Atlas map."""

import json

import folium
from branca.element import Element

from litlas.processing.countries import country_name
from branca.element import MacroElement
from jinja2 import Template

AFRICA_ISO3 = {
    "DZA", "AGO", "BEN", "BWA", "BFA", "BDI",
    "CPV", "CMR", "CAF", "TCD", "COM", "COG",
    "COD", "CIV", "DJI", "EGY", "GNQ", "ERI",
    "SWZ", "ETH", "GAB", "GMB", "GHA", "GIN",
    "GNB", "KEN", "LSO", "LBR", "LBY", "MDG",
    "MWI", "MLI", "MRT", "MUS", "MAR", "MOZ",
    "NAM", "NER", "NGA", "RWA", "STP", "SEN",
    "SYC", "SLE", "SOM", "ZAF", "SSD", "SDN",
    "TZA", "TGO", "TUN", "UGA", "ZMB", "ZWE",
}


def add_unexplored_lands_control(
    m: folium.Map,
    read_countries: set[str],
) -> None:
    """Add a collapsible literary explorer to the Folium map."""

    missing = sorted(
        [
            country_name(iso)
            for iso in AFRICA_ISO3 - set(read_countries)
        ],
        key=str.casefold,
    )

    # Escape HTML-significant characters in embedded JSON.
    countries_json = json.dumps(
        missing, ensure_ascii=True
    ).replace("<", "\\u003c")

    style = """
    <style>
    .litlas-explorer-control {
        position: absolute !important;
        left: 44px;
        top: 0;
        margin: 10px 0 0 0 !important;
        z-index: 1000;
        font-family: Georgia, serif;
    }

    .litlas-explorer-button {
        width: 34px;
        height: 34px;
        border: 1px solid #B9AA95;
        border-radius: 4px;
        background: #FAF7F1;
        color: #58412F;
        cursor: pointer;
        font-size: 20px;
        box-shadow: 0 1px 5px #0002;
    }

    .litlas-explorer-panel {
        position: absolute;
        top: 0;
        left: 43px;
        width: 310px;
        max-width: calc(100vw - 115px);
        box-sizing: border-box;
        background: #F7F0E4;
        border: 1px solid #C9BBA6;
        border-radius: 7px;
        box-shadow: 0 5px 18px #58412F35;
        padding: 13px;
        color: #58412F;
        display: none;
    }

    .litlas-explorer-panel.open {
        display: block;
    }

    .litlas-explorer-heading {
        font-size: 17px;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .litlas-explorer-summary {
        font-size: 12px;
        color: #96785D;
        margin-bottom: 10px;
    }

    .litlas-explorer-search {
        box-sizing: border-box;
        width: 100%;
        padding: 7px 9px;
        border-radius: 4px;
        border: 1px solid #D4C1A7;
        background: #FFFCF6;
        color: #58412F;
        font: 13px Georgia, serif;
        margin-bottom: 9px;
    }

    .litlas-explorer-list {
        max-height: 230px;
        overflow-y: auto;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0 9px;
        font-size: 12px;
    }

    .litlas-explorer-country {
        padding: 5px 2px;
        border-bottom: 1px solid #E4D8C7;
        overflow-wrap: anywhere;
    }
    </style>
    """

    m.get_root().header.add_child(Element(style))

    script = """
    (function () {
        const map = MAP_REFERENCE;
        const missing = COUNTRIES_JSON;

        const Explorer = L.Control.extend({
            options: {position: "topleft"},

            onAdd: function () {
                const control = L.DomUtil.create(
                    "div", "litlas-explorer-control"
                );

                const button = L.DomUtil.create(
                    "button", "litlas-explorer-button", control
                );
                button.type = "button";
                button.textContent = "⌕";
                button.title = "Unexplored Literary Lands";
                button.setAttribute(
                    "aria-label", "Explore unread countries"
                );

                const panel = L.DomUtil.create(
                    "div", "litlas-explorer-panel", control
                );

                const heading = L.DomUtil.create(
                    "div", "litlas-explorer-heading", panel
                );
                heading.textContent = "Unexplored Lands";

                const summary = L.DomUtil.create(
                    "div", "litlas-explorer-summary", panel
                );
                summary.textContent =
                    "Africa · " + missing.length +
                    " of 54 countries unexplored";

                const search = L.DomUtil.create(
                    "input", "litlas-explorer-search", panel
                );
                search.type = "search";
                search.placeholder = "Find an African country...";
                search.setAttribute(
                    "aria-label", "Search unexplored countries"
                );

                const list = L.DomUtil.create(
                    "div", "litlas-explorer-list", panel
                );

                function renderList() {
                    const query = search.value.trim().toLowerCase();
                    list.replaceChildren();

                    missing.filter(
                        name => name.toLowerCase().includes(query)
                    ).forEach(name => {
                        const item = L.DomUtil.create(
                            "div", "litlas-explorer-country", list
                        );
                        item.textContent = "○ " + name;
                    });

                    if (!list.children.length) {
                        const empty = L.DomUtil.create(
                            "div", "litlas-explorer-country", list
                        );
                        empty.textContent = "No matching countries";
                    }
                }

                renderList();

                L.DomEvent.disableClickPropagation(control);
                L.DomEvent.disableScrollPropagation(control);

                L.DomEvent.on(button, "click", function (event) {
                    L.DomEvent.stop(event);
                    const isOpen = panel.classList.toggle("open");
                    button.setAttribute("aria-expanded", String(isOpen));
                    if (isOpen) search.focus();
                });

                L.DomEvent.on(search, "input", renderList);

                L.DomEvent.on(control, "keydown", function (event) {
                    if (event.key === "Escape") {
                        panel.classList.remove("open");
                        button.setAttribute("aria-expanded", "false");
                        button.focus();
                    }
                });

                L.DomEvent.on(map, "click", function () {
                    panel.classList.remove("open");
                    button.setAttribute("aria-expanded", "false");
                });

                button.setAttribute("aria-expanded", "false");
                return control;
            }
        });

        map.addControl(new Explorer());
    })();
    """

    script = script.replace(
        "MAP_REFERENCE", m.get_name()
    ).replace(
        "COUNTRIES_JSON", countries_json
    )

    class UnexploredLandsControl(MacroElement):
        def __init__(self, javascript: str):
            super().__init__()
            self._name = "UnexploredLandsControl"

            self._template = Template(
                "{% macro script(this, kwargs) %}"
                + javascript
                + "{% endmacro %}"
            )

    m.add_child(UnexploredLandsControl(script))
