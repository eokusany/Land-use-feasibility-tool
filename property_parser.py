import re
from typing import Dict, Optional, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from canada_municipalities import CANADIAN_MUNICIPALITIES


# Build a flat lookup set of all Canadian city names for fast hint matching
_ALL_CITY_NAMES: List[str] = []
for _prov, _cities in CANADIAN_MUNICIPALITIES.items():
    _ALL_CITY_NAMES.extend(_cities.keys())


class PropertyParser:
    """Parse property information from various input formats (all of Canada)."""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="canland_feasibility_tool/1.0")

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

        m = self.address_patterns["street_address"].search(address)
        if m:
            parsed["type"] = "street"
            parsed["components"] = {"number": m.group(1), "street": m.group(2).strip()}

        m = self.address_patterns["rural_address"].search(address)
        if m:
            parsed["type"] = "rural"
            parsed["components"] = {"road_type": m.group(1), "road_number": m.group(2)}

        m = self.address_patterns["postal_code"].search(address)
        if m:
            parsed["components"]["postal_code"] = m.group(1).upper().replace(" ", "")

        return parsed

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
        try:
            # Append province name and country for better accuracy
            suffix = ""
            if province and province.upper() in self._province_suffixes:
                suffix = f", {self._province_suffixes[province.upper()]}"
            full_address = f"{address}{suffix}, Canada"
            location = self.geolocator.geocode(full_address, timeout=10)
            if location:
                return {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "display_name": location.address,
                }
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
        return None

    def _extract_municipality_hints(self, text: str) -> List[str]:
        found = []
        text_lower = text.lower()
        for city_name in _ALL_CITY_NAMES:
            if city_name.lower() in text_lower:
                found.append(city_name)
        return found

    def _extract_property_details(self, info: str) -> Dict:
        details: Dict = {}

        m = re.search(r"(\d+\.?\d*)\s*acres?", info, re.IGNORECASE)
        if m:
            details["acreage"] = float(m.group(1))

        m = re.search(r"(\d+\.?\d*)\s*hectares?", info, re.IGNORECASE)
        if m:
            details.setdefault("acreage", round(float(m.group(1)) * 2.471, 2))

        for kw in ["commercial", "residential", "rural", "agricultural", "industrial"]:
            if kw in info.lower():
                details.setdefault("zoning_hints", []).append(kw)

        for kw in ["develop", "cottages", "cabin", "subdivision", "building", "construction", "resort"]:
            if kw in info.lower():
                details.setdefault("development_intentions", []).append(kw)

        for kw in ["septic", "water", "power", "sewer", "gas", "internet", "utility"]:
            if kw in info.lower():
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
