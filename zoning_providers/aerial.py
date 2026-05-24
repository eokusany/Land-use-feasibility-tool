"""Mapbox Static Images helper.

Builds a URL for a single satellite image centred on a coordinate. Returns
None when the `PLOTLINE_MAPBOX_TOKEN` env var is missing — the Parcel
Context UI/PDF treats `aerial_image=None` as "no image available" and
shows a small caveat instead of failing the whole report.

Mapbox Static Images API docs:
  https://docs.mapbox.com/api/maps/static-images/

Rate limits: 50k requests/month on the free tier, then $1 per 1k requests
on Static Images. Plotline caches the URL in policy_info, so subsequent
renders of the same report don't re-fetch.
"""

import os
from typing import Optional
from urllib.parse import quote

from .parcel_context import AerialImage


_MAX_DIMENSION = 1280
_DEFAULT_WIDTH = 600
_DEFAULT_HEIGHT = 400
_DEFAULT_ZOOM = 18
_STYLE = "mapbox/satellite-v9"


def build_static_aerial(
    lat: float,
    lon: float,
    *,
    width: int = _DEFAULT_WIDTH,
    height: int = _DEFAULT_HEIGHT,
    zoom: int = _DEFAULT_ZOOM,
) -> Optional[AerialImage]:
    """Return an AerialImage for the given coordinate, or None when the token
    is missing or the requested dimensions exceed Mapbox's limits."""
    token = os.environ.get("PLOTLINE_MAPBOX_TOKEN", "").strip()
    if not token:
        return None
    if width <= 0 or height <= 0 or width > _MAX_DIMENSION or height > _MAX_DIMENSION:
        return None

    # The Mapbox Static API URL shape:
    #   /styles/v1/<style>/static/<lon>,<lat>,<zoom>/<width>x<height>?access_token=...
    url = (
        f"https://api.mapbox.com/styles/v1/{_STYLE}/static/"
        f"{lon},{lat},{zoom}/"
        f"{width}x{height}"
        f"?access_token={quote(token, safe='')}"
    )
    return AerialImage(
        url=url,
        width=width,
        height=height,
        zoom=zoom,
        attribution="© Mapbox © OpenStreetMap",
    )
