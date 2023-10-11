from typing import Optional

import folium
import streamlit as st
from folium.map import Icon
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation

from src.geolocation import (
    Coords,
    get_geocode_top_hit,
    get_isochrones,
    parse_get_geolocation,
)

MIN_ADDRESS_LENGTH = 5

center_coords: Optional[Coords] = None
address_str = st.text_input(label="Address")
is_near_me = st.checkbox("Near me")

browser_coords: Optional[Coords] = None
if is_near_me:
    browser_coords = parse_get_geolocation(get_geolocation())
st.write(browser_coords)

center_coords: Optional[Coords] = None
if len(address_str) > 0:
    if len(address_str) > MIN_ADDRESS_LENGTH:
        query_params = {"text": address_str}
        if browser_coords is not None:
            query_params.update(
                {
                    "focus.point.lon": browser_coords.longitude,
                    "focus.point.lat": browser_coords.latitude,
                }
            )
            st.success("Using location from Browser location and Address field")
        else:
            st.success("Using location from Address field")
        center_coords = get_geocode_top_hit(**query_params)
    else:
        st.warning(
            f"Entered address is too short (<{MIN_ADDRESS_LENGTH}) and will be ignored"
        )

if center_coords is None and browser_coords is not None:
    center_coords = browser_coords
    st.success("Using location from Browser location")
if center_coords is None:
    st.error("No location provided")

st.write(center_coords)

if center_coords is not None:
    center_lat_lon = (center_coords.latitude, center_coords.longitude)
    bound_lat_lons = [
        center_lat_lon,
    ]

    m = folium.Map(location=center_lat_lon, control_scale=True)
    folium.Marker(
        location=center_lat_lon,
        tooltip="Current location",
        icon=Icon(color="blue"),
    ).add_to(m)

    for transportation_name, profile, fill_color in [
        ("Driving", "driving-car", "blue"),
        ("Cycling", "cycling-regular", "green"),
        ("Walking", "foot-walking", "red"),
    ]:
        isochrone_coords, isochrone_properties = get_isochrones(
            coords=center_coords,
            range_seconds=60 * 30,
            profile=profile,
        )
        isochrone_lat_lons = [
            [coords.latitude, coords.longitude] for coords in isochrone_coords
        ]
        bound_lat_lons += isochrone_lat_lons
        folium.Polygon(
            locations=isochrone_lat_lons,
            weight=0,
            fill_color=fill_color,
            fill_opacity=0.2,
            fill=True,
            tooltip=f"30mins {transportation_name} Reach Factor: {isochrone_properties['reachfactor']}",
        ).add_to(m)

    make_map_responsive = """
        <style>
        [title~="st.iframe"] { width: 100%}
        </style>
        """
    st.markdown(make_map_responsive, unsafe_allow_html=True)
    folium_static(m, width=500, height=500)
