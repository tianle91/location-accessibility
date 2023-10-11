import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
import requests_cache

requests_cache.install_cache("geolocation_cache", backend="sqlite")
ORS_KEY = os.getenv("OPENROUTESERVICE_API_KEY")


@dataclass
class Coords:
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    altitudeAccuracy: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None


def parse_get_geolocation(d: Optional[dict] = None) -> Optional[Coords]:
    """Parse output of streamlit_js_eval.get_geolocation."""
    if d is not None:
        return Coords(**d.get("coords", {}))


def get_geocode_top_hit(**kwargs) -> Coords:
    params = {**kwargs}
    params.update({"api_key": ORS_KEY})
    response = requests.get(
        "https://api.openrouteservice.org/geocode/search/", params=params
    )
    coords = response.json()["features"][0]["geometry"]["coordinates"]
    longitude, latitude = coords[0], coords[1]
    return Coords(latitude=latitude, longitude=longitude)


def get_isochrones(
    coords: Coords, range_seconds: int = 200, profile: str = "driving-car"
) -> Tuple[List[Coords], dict]:
    """
    # https://github.com/GIScience/openrouteservice-py/blob/9fc22f378db8f9ef98a1675031055b1ae2bec97b/openrouteservice/directions.py#L66-L69
    profile: One of ["driving-car", "foot-walking", "cycling-regular"]
    """
    body = {
        "locations": [[coords.longitude, coords.latitude]],
        "range": [range_seconds],
        "attributes": ["area", "reachfactor", "total_pop"],
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
        response.json()["features"][0]["properties"],
    )
