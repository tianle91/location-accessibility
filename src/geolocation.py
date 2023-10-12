import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
import requests_cache

requests_cache.install_cache("geolocation_cache", backend="sqlite")
ORS_KEY = os.getenv("OPENROUTESERVICE_API_KEY")
import logging

logger = logging.getLogger(__name__)


@dataclass
class Coords:
    latitude: float
    longitude: float


def parse_get_geolocation(d: Optional[dict] = None) -> Optional[Coords]:
    """Parse output of streamlit_js_eval.get_geolocation."""
    if d is not None:
        return Coords(
            latitude=d["coords"]["latitude"],
            longitude=d["coords"]["longitude"],
        )


def get_geocode_top_hit(**kwargs) -> Optional[Coords]:
    params = {**kwargs}
    params.update({"api_key": ORS_KEY})
    response_json = requests.get(
        "https://api.openrouteservice.org/geocode/search/", params=params
    ).json()
    try:
        coords = response_json["features"][0]["geometry"]["coordinates"]
        return Coords(latitude=coords[1], longitude=coords[0])
    except Exception as e:
        logger.warning(
            f"Failed to get coordinates from geocode/search. response_json:\n{response_json}"
            f"Error:\n{e}"
        )


ISOCHRONE_PROFILES = ["driving-car", "cycling-regular", "foot-walking", "wheelchair"]


def get_isochrones(
    coords: Coords, range_seconds: int = 200, profile: str = "driving-car"
) -> Tuple[List[Coords], dict]:
    """
    # https://github.com/GIScience/openrouteservice-py/blob/9fc22f378db8f9ef98a1675031055b1ae2bec97b/openrouteservice/directions.py#L66-L69
    profile: One of ISOCHRONE_PROFILES
    """
    if profile not in ISOCHRONE_PROFILES:
        raise ValueError(
            f"Profile {profile} not in ISOCHRONE_PROFILES: {ISOCHRONE_PROFILES}"
        )
    attributes = ["area", "reachfactor", "total_pop"]
    body = {
        "locations": [[coords.longitude, coords.latitude]],
        "range": [range_seconds],
        "attributes": attributes,
    }
    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
        "Authorization": ORS_KEY,
        "Content-Type": "application/json; charset=utf-8",
    }
    response = requests.post(
        f"https://api.openrouteservice.org/v2/isochrones/{profile}",
        json=body,
        headers=headers,
    )
    # return response.json()["features"][0]["geometry"]["coordinates"]
    return (
        [
            Coords(longitude=l[0], latitude=l[1])
            for l in response.json()["features"][0]["geometry"]["coordinates"][0]
        ],
        {k: response.json()["features"][0]["properties"][k] for k in attributes},
    )
