from typing import Optional

import folium
import pandas as pd
import streamlit as st
from folium.map import Icon
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation

from src.geolocation import (
    ISOCHRONE_PROFILES,
    Coords,
    get_geocode_top_hit,
    get_isochrones,
    parse_get_geolocation,
)

MIN_ADDRESS_LENGTH = 5

ISOCHRONE_OPTIONS = {
    # {display_name: (profile_name, display_color) for k in ISOCHRONE_PROFILES}
    "Driving": ("driving-car", "green"),
    "Cycling": ("cycling-regular", "blue"),
    "Walking": ("foot-walking", "orange"),
    "Wheelchair": ("wheelchair", "red"),
}
if set([v[0] for v in ISOCHRONE_OPTIONS.values()]) != set(ISOCHRONE_PROFILES):
    raise ValueError(
        f"ISOCHRONE_OPTIONS keys: {ISOCHRONE_OPTIONS.keys()} "
        f"must match ISOCHRONE_PROFILES: {ISOCHRONE_PROFILES}"
    )


center_address_str = st.text_input(label="Center Address")
home_address_str = st.text_input(label="Home Address")
work_address_str = st.text_input(label="Work Address")

browser_coords: Optional[Coords] = None
if st.checkbox("Near me"):
    browser_coords = parse_get_geolocation(get_geolocation())


def get_coords_from_text(
    text: str, browser_coords: Optional[Coords], warning_text_type: str = ""
) -> Optional[Coords]:
    if len(text) == 0:
        return None
    if len(text) < MIN_ADDRESS_LENGTH:
        st.warning(
            f"Ignoring {warning_text_type} since entered text length <{MIN_ADDRESS_LENGTH}"
        )
        return browser_coords
    query_params = {"text": text}
    if browser_coords is not None:
        query_params.update(
            {
                "focus.point.lon": browser_coords.longitude,
                "focus.point.lat": browser_coords.latitude,
            }
        )
        st.success(f"Searching for {warning_text_type} near browser location.")
    return get_geocode_top_hit(**query_params)


center_coords = get_coords_from_text(
    text=center_address_str,
    browser_coords=browser_coords,
    warning_text_type="Center Address",
)
home_coords = get_coords_from_text(
    text=home_address_str,
    browser_coords=browser_coords,
    warning_text_type="Home Address",
)
work_coords = get_coords_from_text(
    text=work_address_str,
    browser_coords=browser_coords,
    warning_text_type="Work Address",
)

if center_coords is None and browser_coords is not None:
    center_coords = browser_coords

if center_coords is not None:
    bound_lat_lons = []

    center_lat_lon = (center_coords.latitude, center_coords.longitude)
    m = folium.Map(location=center_lat_lon, control_scale=True)

    bound_lat_lons.append(center_lat_lon)
    folium.Marker(
        location=center_lat_lon,
        tooltip="Center",
        icon=Icon(color="blue"),
    ).add_to(m)

    if home_coords is not None:
        home_lat_lon = (home_coords.latitude, home_coords.longitude)
        bound_lat_lons.append(home_lat_lon)
        folium.Marker(
            location=home_lat_lon,
            tooltip="Home",
            icon=Icon(color="green"),
        ).add_to(m)

    if work_coords is not None:
        work_lat_lon = (work_coords.latitude, work_coords.longitude)
        bound_lat_lons.append(work_lat_lon)
        folium.Marker(
            location=work_lat_lon,
            tooltip="Work",
            icon=Icon(color="yellow"),
        ).add_to(m)

    selected_isochrone_display_names = st.multiselect(
        label="Plot isochrones", options=ISOCHRONE_OPTIONS.keys(), default=None
    )
    isochrone_minutes = st.number_input(
        label="Isochrone minutes", step=15, min_value=15, max_value=120, value=30
    )
    isochrone_resl = []
    for isochrone_display_name in selected_isochrone_display_names:
        profile_name, isochrone_color = ISOCHRONE_OPTIONS[isochrone_display_name]
        isochrone_coords, isochrone_properties = get_isochrones(
            coords=center_coords,
            range_seconds=60 * isochrone_minutes,
            profile=profile_name,
        )
        isochrone_lat_lons = [
            [coords.latitude, coords.longitude] for coords in isochrone_coords
        ]
        bound_lat_lons += isochrone_lat_lons
        folium.Polygon(
            locations=isochrone_lat_lons,
            weight=0,
            fill_color=isochrone_color,
            fill_opacity=0.2,
            fill=True,
            tooltip=f"{isochrone_minutes} mins {isochrone_display_name} Reach Factor: {isochrone_properties['reachfactor']}",
        ).add_to(m)
        isochrone_resl.append(
            {
                "Isochrone Type": isochrone_display_name,
                **isochrone_properties,
            }
        )

    make_map_responsive = """
        <style>
        [title~="st.iframe"] { width: 100%}
        </style>
        """
    st.markdown(make_map_responsive, unsafe_allow_html=True)
    m.fit_bounds(bound_lat_lons)
    folium_static(m, width=500, height=500)

    st.write(pd.DataFrame(isochrone_resl))
