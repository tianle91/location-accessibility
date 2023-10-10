from typing import Optional

import streamlit as st
from streamlit_js_eval import get_geolocation

from src.geolocation import Coords, get_geocode_top_hit, parse_geolocation

MIN_ADDRESS_LENGTH = 5

center_coords: Optional[Coords] = None
address_str = st.text_input(label="Address")
is_near_me = st.checkbox("Near me")

browser_coords: Optional[Coords] = None
if is_near_me:
    geo_d = get_geolocation()
    if geo_d is not None:
        browser_coords = parse_geolocation(geo_d)
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
