
"""Compact unexplored-country control inside the Literary Atlas map."""

import json

import folium
from branca.element import Element, MacroElement
from jinja2 import Template

from litlas.processing.countries import (
    country_name,
    sovereign_country_codes,
)


def add_unexplored_lands_control(
    m: folium.Map,
    read_countries: set[str],
) -> None:
    """Add a collapsible literary explorer to the Folium map."""


    # Sovereign-state reference set, independent of GeoJSON
    # territories and map rendering.
    world_iso3 = sovereign_country_codes()

    explored_iso3 = world_iso3.intersection(
        read_countries
    )

    unexplored_iso3 = world_iso3 - explored_iso3

    missing = sorted(
        (country_name(iso) for iso in unexplored_iso3),
        key=str.casefold,
    )

    total_countries = len(world_iso3)


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

    .litlas-explorer-panel {
        position: absolute;
        top: 0;
        left: 43px;

        width: 230px;
        max-width: calc(100vw - 115px);
        box-sizing: border-box;

        background: #F5EFE4;
        border: 1px solid #C9BBA6;
        border-radius: 8px;
        box-shadow: 0 3px 12px rgba(85, 63, 42, 0.14);

        padding: 14px;
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

    .leaflet-container .litlas-explorer-panel input.litlas-explorer-search {
        display: block;
        width: calc(100% - 8px);
        max-width: 100%;
        min-width: 0;
        box-sizing: border-box;

        padding: 7px 9px;
        margin: 0 4px 9px 4px;

        border: 1px solid #D4C1A7;
        border-radius: 4px;
        background: #FFFCF6;
        color: #58412F;
        font: 13px Georgia, serif;
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

    .unexplored-toggle {
        width: 34px;
        height: 34px;
        border: 1px solid #C9BBA6;
        border-radius: 4px;
        background: #FAF7F1;
        color: #7A5A3A;
        font-family: Georgia, serif;
        font-size: 18px;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 1px 4px rgba(88, 65, 47, 0.14);
    }

    .unexplored-toggle:hover {
        background: #F2E8D8;
        color: #5D3F2E;
    }

    </style>
    """

    m.get_root().header.add_child(Element(style))

    script = """
    (function () {
        const map = MAP_REFERENCE;
        const missing = COUNTRIES_JSON;
        const totalCountries = TOTAL_COUNTRIES;

        const Explorer = L.Control.extend({
            options: {position: "topleft"},

            onAdd: function () {
                const control = L.DomUtil.create(
                    "div", "litlas-explorer-control"
                );

                const toggleButton = L.DomUtil.create(
                    "button", "", control
                );
                toggleButton.type = "button";
                toggleButton.innerHTML = "⌕";
                toggleButton.className = "unexplored-toggle";
                toggleButton.title = "Browse unexplored lands";
                toggleButton.setAttribute(
                    "aria-label", "Explore unread countries"
                );

                const panel = L.DomUtil.create(
                    "div",
                    "litlas-explorer-panel",
                    control
                );

                const heading = L.DomUtil.create(
                    "div", "litlas-explorer-heading", panel
                );
                heading.textContent = "Unexplored Lands";

                const summary = L.DomUtil.create(
                    "div", "litlas-explorer-summary", panel
                );
                summary.textContent =
                    "World · " + missing.length +
                    " of " + totalCountries + " unexplored";

                const search = L.DomUtil.create(
                    "input", "litlas-explorer-search", panel
                );
                search.type = "search";
                search.placeholder = "Find a country...";
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

                L.DomEvent.on(toggleButton, "click", function (event) {
                    L.DomEvent.stop(event);
                    const isOpen = panel.classList.toggle("open");
                    toggleButton.setAttribute(
                        "aria-expanded", String(isOpen)
                    );
                    if (isOpen) search.focus();
                });

                L.DomEvent.on(search, "input", renderList);

                L.DomEvent.on(control, "keydown", function (event) {
                    if (event.key === "Escape") {
                        panel.classList.remove("open");
                        toggleButton.setAttribute("aria-expanded", "false");
                        toggleButton.focus();
                    }
                });

                L.DomEvent.on(map, "click", function () {
                    panel.classList.remove("open");
                    toggleButton.setAttribute("aria-expanded", "false");
                });

                toggleButton.setAttribute("aria-expanded", "false");
                return control;
            }
        });

        map.addControl(new Explorer());
    })();
    """

    total_json = json.dumps(total_countries)

    script = (
        script.replace("MAP_REFERENCE", m.get_name())
        .replace("COUNTRIES_JSON", countries_json)
        .replace("TOTAL_COUNTRIES", total_json)
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
