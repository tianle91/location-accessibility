import os
from dataclasses import dataclass
from typing import Optional

import requests

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


def parse_geolocation(d: dict) -> Coords:
    """Parse output of streamlit_js_eval.get_geolocation."""
    return Coords(**d.get("coords", {}))


def get_geocode_top_hit(**kwargs):
    params = {**kwargs}
    params.update({"api_key": ORS_KEY})
    response = requests.get(
        "https://api.openrouteservice.org/geocode/search/", params=params
    )
    print(response.json())
    coords = response.json()["features"][0]["geometry"]["coordinates"]
    longitude, latitude = coords[0], coords[1]
    return Coords(latitude=latitude, longitude=longitude)
