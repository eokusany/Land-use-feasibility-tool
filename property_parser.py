"""Parse property information from user input.

Handles addresses, legal descriptions, unit numbers, and rough text hints
about the municipality. Geocoding is best-effort via Nominatim.
"""

import logging
import os
import re
import threading
import time
from typing import Dict, List, Optional, Tuple

from geopy.distance import geodesic
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

from canada_municipalities import CANADIAN_MUNICIPALITIES

logger = logging.getLogger(__name__)

# Maximum distance between a geocoded point and the selected municipality's
# centroid before we flag the result as suspicious. Most Canadian cities are
# well under 60 km wide; 80 km is generous and still catches the original
# "8520 Jasper Ave 1403 → west Edmonton" failure mode.
GEOCODE_BOUNDARY_KM = float(os.environ.get("CANLAND_GEOCODE_BOUNDARY_KM", "80"))

# Nominatim's ToS is 1 req/sec from a single host. Enforced process-wide.
_NOMINATIM_MIN_INTERVAL = 1.0
_nominatim_lock = threading.Lock()
_nominatim_last_call = 0.0


def _throttle_nominatim():
    """Sleep just long enough to honour Nominatim's 1 req/sec limit."""
    global _nominatim_last_call
    with _nominatim_lock:
        delta = time.monotonic() - _nominatim_last_call
        if delta < _NOMINATIM_MIN_INTERVAL:
            time.sleep(_NOMINATIM_MIN_INTERVAL - delta)
        _nominatim_last_call = time.monotonic()


# Build a flat lookup set of all Canadian city names for fast hint matching.
# Sort longest-first so multi-word names ("Grande Prairie") beat substrings
# ("Grande") when both could match.
_ALL_CITY_NAMES: List[str] = sorted(
    {name for cities in CANADIAN_MUNICIPALITIES.values() for name in cities.keys()},
    key=lambda s: (-len(s), s.lower()),
)

# Pre-compile word-boundary patterns once. \b doesn't handle multi-word
# city names with hyphens or apostrophes correctly on its own, so we
# anchor with lookaround for non-letter characters.
_CITY_PATTERNS = [
    (
        name,
        re.compile(
            r"(?<![A-Za-z'\-])" + re.escape(name) + r"(?![A-Za-z'\-])",
            re.IGNORECASE,
        ),
    )
    for name in _ALL_CITY_NAMES
]


class PropertyParser:
    """Parse property information from various input formats (all of Canada)."""

    def __init__(self):
        # Nominatim ToS asks for a contact email in the User-Agent. Use the
        # configured one if available, else a generic but identifiable string.
        ua_contact = os.environ.get(
            "CANLAND_NOMINATIM_CONTACT",
            "canland@example.com",
        )
        self.geolocator = Nominatim(
            user_agent=f"canland_feasibility_tool/1.1 ({ua_contact})",
            timeout=10,
        )

        # Legal description patterns (primarily western Canada DLS, also lot/block plan)
        self.legal_patterns = {
            "quarter_section": re.compile(
                r"([NSEW]{1,2})\s*(\d{1,2})\s*-\s*(\d{1,3})\s*-\s*(\d{1,3})\s*-\s*([WE])\s*(\d)",
                re.IGNORECASE,
            ),
            "lot_block": re.compile(
                r"LOT\s*(\d+)\s*,?\s*BLOCK\s*(\d+)\s*,?\s*PLAN\s*(\w+)", re.IGNORECASE
            ),
            "parcel": re.compile(r"PARCEL\s*(\w+)\s*,?\s*PLAN\s*(\w+)", re.IGNORECASE),
            "section": re.compile(
                r"SECTION\s*(\d{1,2})\s*,?\s*TOWNSHIP\s*(\d{1,3})\s*,?\s*RANGE\s*(\d{1,3})\s*,?\s*([WE])\s*(\d)",
                re.IGNORECASE,
            ),
            # Ontario/Quebec PIDs
            "pid": re.compile(r"\bPID[:\s]*(\d{9})\b", re.IGNORECASE),
        }

        # Optional unit/suite prefix (Apt, Suite, Unit, #) before the street number,
        # or a trailing unit after the street name. Examples handled:
        #   "Apt 1403, 8520 Jasper Ave"
        #   "Unit 5 - 100 Main St"
        #   "100 Main St, #5"
        #   "8520 Jasper Ave, 1403"
        self._unit_prefix_re = re.compile(
            r"^\s*(?:apt\.?|apartment|unit|suite|ste\.?|#)\s*([A-Za-z0-9\-]+)\b",
            re.IGNORECASE,
        )
        self._unit_trailing_re = re.compile(
            r",\s*(?:apt\.?|apartment|unit|suite|ste\.?|#)?\s*([A-Za-z0-9\-]{1,8})\s*$",
            re.IGNORECASE,
        )

        self.address_patterns = {
            "street_address": re.compile(
                r"(\d+)\s+([A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|"
                r"Boulevard|Blvd|Way|Circle|Cir|Court|Ct|Crescent|Cres|Place|Pl|Terrace|Tr))",
                re.IGNORECASE,
            ),
            "rural_address": re.compile(
                r"(RR|Rural Route|Range Road|Township Road|County Road|Highway|Hwy|Route)\s*(\d+)",
                re.IGNORECASE,
            ),
            "postal_code": re.compile(r"([A-Za-z]\d[A-Za-z]\s*\d[A-Za-z]\d)", re.IGNORECASE),
        }

        # Canadian province/territory abbreviations to help geocoding
        self._province_suffixes = {
            "BC": "British Columbia",
            "AB": "Alberta",
            "SK": "Saskatchewan",
            "MB": "Manitoba",
            "ON": "Ontario",
            "QC": "Quebec",
            "NB": "New Brunswick",
            "NS": "Nova Scotia",
            "PE": "Prince Edward Island",
            "NL": "Newfoundland and Labrador",
            "YT": "Yukon",
            "NT": "Northwest Territories",
            "NU": "Nunavut",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_property_info(
        self,
        address: str = "",
        legal_description: str = "",
        additional_info: str = "",
        province: str = "",
    ) -> Optional[Dict]:
        """Parse property information and return a normalized dict."""
        property_info = {
            "raw_input": {
                "address": address,
                "legal_description": legal_description,
                "additional_info": additional_info,
                "province": province,
            },
            "parsed_address": None,
            "parsed_legal": None,
            "coordinates": None,
            "municipality_hints": [],
            "property_details": {},
            "province_hint": province.upper() if province else "",
        }

        if address:
            property_info["parsed_address"] = self._parse_address(address)
            coords = self._geocode_address(address, province)
            if coords:
                property_info["coordinates"] = coords

        if legal_description:
            property_info["parsed_legal"] = self._parse_legal_description(legal_description)

        all_text = f"{address} {legal_description} {additional_info}"
        property_info["municipality_hints"] = self._extract_municipality_hints(all_text)

        if additional_info:
            property_info["property_details"] = self._extract_property_details(additional_info)

        return property_info if self._is_valid(property_info) else None

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_address(self, address: str) -> Dict:
        parsed = {"type": "unknown", "components": {}, "full_address": address.strip()}

        unit = self._extract_unit(address)
        if unit:
            parsed["components"]["unit"] = unit

        m = self.address_patterns["street_address"].search(address)
        if m:
            parsed["type"] = "street"
            parsed["components"].update({"number": m.group(1), "street": m.group(2).strip()})

        m = self.address_patterns["rural_address"].search(address)
        if m:
            parsed["type"] = "rural"
            parsed["components"].update(
                {"road_type": m.group(1), "road_number": m.group(2)}
            )

        m = self.address_patterns["postal_code"].search(address)
        if m:
            parsed["components"]["postal_code"] = m.group(1).upper().replace(" ", "")

        return parsed

    def _extract_unit(self, address: str) -> Optional[str]:
        """Pull a unit/suite/apartment number out of the address if present.

        Tries explicit prefixes first (Apt 1403, Unit 5, Suite 200, #5),
        then a trailing comma-separated short numeric token.
        """
        if not address:
            return None

        m = self._unit_prefix_re.search(address)
        if m:
            return m.group(1).strip().lstrip("#")

        # Trailing "..., 1403" — only treat as a unit if it looks like one
        # (short, mostly digits) so we don't grab a postal code or street name.
        trailing = re.search(r",\s*([A-Za-z0-9\-]+)\s*$", address)
        if trailing:
            token = trailing.group(1).strip()
            if 1 <= len(token) <= 6 and any(c.isdigit() for c in token):
                # Postal-code shapes (A1A 1A1, A1A1A1) should not be treated as units
                if not re.fullmatch(r"[A-Za-z]\d[A-Za-z]\s*\d[A-Za-z]\d", token):
                    return token.lstrip("#")
        return None

    def _parse_legal_description(self, legal_desc: str) -> Dict:
        parsed = {"type": "unknown", "components": {}, "full_description": legal_desc.strip()}

        for name, pattern in self.legal_patterns.items():
            m = pattern.search(legal_desc)
            if m:
                parsed["type"] = name
                if name == "quarter_section":
                    parsed["components"] = {
                        "quarter": m.group(1),
                        "section": m.group(2),
                        "township": m.group(3),
                        "range": m.group(4),
                        "meridian_direction": m.group(5),
                        "meridian": m.group(6),
                    }
                elif name == "lot_block":
                    parsed["components"] = {
                        "lot": m.group(1),
                        "block": m.group(2),
                        "plan": m.group(3),
                    }
                elif name == "parcel":
                    parsed["components"] = {"parcel": m.group(1), "plan": m.group(2)}
                elif name == "section":
                    parsed["components"] = {
                        "section": m.group(1),
                        "township": m.group(2),
                        "range": m.group(3),
                        "meridian_direction": m.group(4),
                        "meridian": m.group(5),
                    }
                elif name == "pid":
                    parsed["components"] = {"pid": m.group(1)}
                break

        return parsed

    def _geocode_address(self, address: str, province: str = "") -> Optional[Dict]:
        # Throttle to honour Nominatim's 1 req/sec ToS — sharing a single
        # public endpoint with thousands of other users, this matters.
        _throttle_nominatim()
        try:
            # Append province name and country for better accuracy
            suffix = ""
            if province and province.upper() in self._province_suffixes:
                suffix = f", {self._province_suffixes[province.upper()]}"
            full_address = f"{address}{suffix}, Canada"
            location = self.geolocator.geocode(full_address, country_codes="ca")
            if location:
                return {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "display_name": location.address,
                }
        except (GeocoderTimedOut, GeocoderServiceError) as exc:
            logger.warning("Geocoding failed for %r: %s", address, exc)
        return None

    def _extract_municipality_hints(self, text: str) -> List[str]:
        """Extract Canadian city names mentioned in the text, with word
        boundaries so "Mount" doesn't fire on "Paramount", "Lac" on "Place",
        etc. Dedupe while preserving discovery order."""
        if not text:
            return []
        found: List[str] = []
        seen = set()
        for name, pattern in _CITY_PATTERNS:
            if pattern.search(text):
                if name not in seen:
                    seen.add(name)
                    found.append(name)
        return found

    def _extract_property_details(self, info: str) -> Dict:
        """Pull acreage, zoning hints, intentions, and infrastructure mentions
        out of free-form text. Uses word boundaries so we don't match
        "residential" inside "non-residential" or "presidential"."""
        details: Dict = {}
        if not info:
            return details

        m = re.search(r"(\d+\.?\d*)\s*acres?\b", info, re.IGNORECASE)
        if m:
            details["acreage"] = float(m.group(1))

        m = re.search(r"(\d+\.?\d*)\s*hectares?\b", info, re.IGNORECASE)
        if m:
            details.setdefault("acreage", round(float(m.group(1)) * 2.471, 2))

        def _matches_whole_word(kw: str, text: str) -> bool:
            # Anchor with lookaround that excludes letters AND hyphens — `\b`
            # alone allows "non-residential" to fire on "residential" because
            # `-` is a word boundary in Python's re module.
            return re.search(
                r"(?<![A-Za-z\-])" + re.escape(kw) + r"(?![A-Za-z\-])",
                text,
                re.IGNORECASE,
            ) is not None

        for kw in ["commercial", "residential", "rural", "agricultural", "industrial"]:
            if _matches_whole_word(kw, info):
                details.setdefault("zoning_hints", []).append(kw)

        for kw in ["develop", "cottage", "cottages", "cabin", "subdivision", "building", "construction", "resort"]:
            if _matches_whole_word(kw, info):
                details.setdefault("development_intentions", []).append(kw)

        for kw in ["septic", "water", "power", "sewer", "gas", "internet", "utility"]:
            if _matches_whole_word(kw, info):
                details.setdefault("infrastructure_mentions", []).append(kw)

        return details

    def _is_valid(self, prop: Dict) -> bool:
        has_address = (
            prop.get("parsed_address") and prop["parsed_address"]["type"] != "unknown"
        )
        has_legal = (
            prop.get("parsed_legal") and prop["parsed_legal"]["type"] != "unknown"
        )
        has_coords = prop.get("coordinates") is not None
        has_hints = len(prop.get("municipality_hints", [])) > 0
        has_details = bool(prop.get("property_details"))
        has_raw = bool(
            prop.get("raw_input", {}).get("address")
            or prop.get("raw_input", {}).get("legal_description")
            or prop.get("raw_input", {}).get("additional_info")
        )
        return any([has_address, has_legal, has_coords, has_hints, has_details, has_raw])


# ---------------------------------------------------------------------------
# Geocode-in-boundary sanity check
# ---------------------------------------------------------------------------

def is_point_within_municipality(
    lat: float,
    lon: float,
    municipality: Dict,
    max_km: float = GEOCODE_BOUNDARY_KM,
) -> Tuple[bool, float]:
    """Sanity-check whether a geocoded point is plausibly inside the selected
    municipality.

    We don't have boundary polygons for every Canadian municipality, so this
    falls back to a centroid-distance check against the coordinates we DO have
    in `canada_municipalities.py`. It's coarse but catches the failure mode
    that originally motivated this work: Nominatim resolving an address to a
    completely different part of the country, then the user trusting it.

    Returns:
        (is_within, distance_km). is_within is True when we either accept the
        point or have no centroid to compare against (default to permissive).
    """
    centroid = municipality.get("coordinates") or {}
    c_lat = centroid.get("lat")
    c_lon = centroid.get("lon")
    if c_lat is None or c_lon is None:
        return True, 0.0  # no centroid on file — can't reject

    dist = geodesic((lat, lon), (c_lat, c_lon)).kilometers
    return dist <= max_km, dist
