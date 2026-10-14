
"""Shared Folium styling for Litlas maps."""

import folium
from branca.element import Element


def apply_map_style(m: folium.Map) -> None:
    """Apply Litlas's vintage map and popup styling."""

    m.get_root().header.add_child(Element("""
    <style>
        /* Parchment ocean */
        .leaflet-container {
            background-color: #E6DDD0 !important;
        }

        /* Popup body */
        .leaflet-popup-content-wrapper {
            background: #FAF7F1 !important;
            color: #58412F !important;
            border: 1px solid #C9BBA6;
            border-radius: 10px !important;
            box-shadow: 0 3px 12px rgba(85, 63, 42, 0.12);
        }

        /* Popup content */
        .leaflet-popup-content {
            color: #58412F;
        }

        /* Subtle popup title styling */
        .leaflet-popup-content h3,
        .leaflet-popup-content h4 {
            color: #58412F !important;
        }

        /* Remove popup and tooltip pointers */
        .leaflet-popup-tip-container,
        .leaflet-popup-tip,
        .leaflet-tooltip::before,
        .leaflet-tooltip::after {
            display: none !important;
        }
    </style>
    """))
