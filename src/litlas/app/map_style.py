
"""Shared Folium styling for Litlas maps."""

import folium
from branca.element import Element
from string import Template
from branca.element import MacroElement
from jinja2 import Template as JinjaTemplate

# Shared vintage map palette
OCEAN_COLOR = "#E6DDD0"
LAND_COLOR = "#F6F0E6"
BORDER_COLOR = "#C9BBA6"
EXPLORED_COLOR = "#B5A17F"

DENSITY_COLORS = [
    "#F3E6CA",
    "#E3C895",
    "#C9A678",
    "#A98160",
    "#855C45",
    "#603E33",
]

def apply_map_style(m: folium.Map) -> None:
    """Apply Litlas's vintage map and popup styling."""

    m.get_root().header.add_child(Element(Template("""
    <style>
        .leaflet-container {
            background-color: $ocean_color !important;
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

        @media screen and (max-width: 640px) {
            .leaflet-control-scale-line {
                font-size: 10px !important;
                line-height: 1.1 !important;
                padding: 2px 4px !important;
            }
        }

        /* Remove Leaflet's rectangular focus outline */
        .leaflet-interactive:focus {
            outline: none !important;
        }
    </style>
    """).substitute(ocean_color=OCEAN_COLOR)))

class ResponsiveInitialView(MacroElement):
    def __init__(self):
        super().__init__()
        self._name = "ResponsiveInitialView"
        self._template = JinjaTemplate("""
        {% macro script(this, kwargs) %}
            var litlasMap = {{ this._parent.get_name() }};

            if (litlasMap.getContainer().clientWidth <= 640) {
                litlasMap.setView([15, 0], 1, {animate: false});
            } else {
                litlasMap.fitBounds([[-55, -170], [75, 180]]);
            }
        {% endmacro %}
        """)

def create_litlas_map(mobile_focus=False) -> folium.Map:
    """Create a Litlas map with shared settings and styling."""

    m = folium.Map(
        location=[15, 0],
        zoom_start=2,
        tiles=None,
        control_scale=True,
        prefer_canvas=False,
        world_copy_jump=True,
        zoom_control=True,
    )

    apply_map_style(m)

    if mobile_focus:
        m.add_child(ResponsiveInitialView())
    else:
        m.fit_bounds([[-55, -170], [75, 180]])

    return m

def create_litlas_map_obsolete(
    fit_world=True,
    initial_zoom=2,
) -> folium.Map:
    """Create a Litlas map with shared settings and styling."""

    m = folium.Map(
        location=[15, 10],
        zoom_start=initial_zoom,
        tiles=None,
        control_scale=True,
        prefer_canvas=False,
        world_copy_jump=True,
        zoom_control=True,
    )

    apply_map_style(m)
    if fit_world:
        m.fit_bounds([[-55, -170], [75, 180]])    


    return m