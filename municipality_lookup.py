from typing import Dict, Optional, List
from geopy.distance import geodesic
from canada_municipalities import (
    CANADIAN_MUNICIPALITIES,
    PROVINCE_INFO,
    get_all_municipalities_flat,
    get_municipalities_by_province,
)


class MunicipalityLookup:
    """Lookup municipality information for Canadian properties."""

    def __init__(self):
        self._all_municipalities = get_all_municipalities_flat()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_municipality(self, property_info: Dict, province_hint: str = None) -> Optional[Dict]:
        """
        Find the best matching municipality for a given parsed property.

        Priority order:
          1. Name hint extracted from user text (filtered by province when given)
          2. Coordinates proximity
          3. Address component names
        """
        # 1. Name-based match from extracted hints
        hints = property_info.get("municipality_hints", [])
        for hint in hints:
            match = self._find_by_name(hint, province_hint)
            if match:
                return self._enrich(match)

        # 2. Coordinate-based proximity
        coordinates = property_info.get("coordinates")
        if coordinates:
            match = self._find_by_coordinates(
                coordinates["latitude"],
                coordinates["longitude"],
                province_hint=province_hint,
            )
            if match:
                return self._enrich(match)

        # 3. Address component text scan
        address = property_info.get("parsed_address", {})
        if address:
            full = address.get("full_address", "")
            for hint in self._extract_names(full):
                match = self._find_by_name(hint, province_hint)
                if match:
                    return self._enrich(match)

        return None

    def find_by_province_and_city(self, province_code: str, city_name: str) -> Optional[Dict]:
        """Direct lookup by province code + city name (used when user selects from dropdowns)."""
        match = self._find_by_name(city_name, province_code)
        return self._enrich(match) if match else None

    def get_supported_municipalities(self) -> List[Dict]:
        return sorted(self._all_municipalities, key=lambda x: (x["province"], x["name"]))

    def get_supported_provinces(self) -> List[Dict]:
        provinces = []
        for code, info in PROVINCE_INFO.items():
            city_count = len(CANADIAN_MUNICIPALITIES.get(code, {}))
            provinces.append({
                "code": code,
                "name": info["name"],
                "full_name": info["full_name"],
                "city_count": city_count,
                "planning_act": info.get("planning_act", ""),
                "building_code": info.get("building_code", ""),
            })
        return sorted(provinces, key=lambda x: x["name"])

    def get_cities_for_province(self, province_code: str) -> List[Dict]:
        return get_municipalities_by_province(province_code)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_by_name(self, name: str, province_hint: str = None) -> Optional[Dict]:
        name_lower = name.lower().strip()
        candidates = self._all_municipalities

        if province_hint:
            filtered = [m for m in candidates if m["province"].upper() == province_hint.upper()]
            if filtered:
                candidates = filtered

        # Exact match first
        for m in candidates:
            if m["name"].lower() == name_lower:
                return m

        # Partial / substring match
        for m in candidates:
            if name_lower in m["name"].lower() or m["name"].lower() in name_lower:
                return m

        return None

    def _find_by_coordinates(
        self, lat: float, lon: float, province_hint: str = None, max_km: float = 100
    ) -> Optional[Dict]:
        candidates = self._all_municipalities
        if province_hint:
            filtered = [m for m in candidates if m["province"].upper() == province_hint.upper()]
            if filtered:
                candidates = filtered

        closest = None
        closest_dist = float("inf")

        for m in candidates:
            coords = m.get("coordinates")
            if not coords:
                continue
            dist = geodesic((lat, lon), (coords["lat"], coords["lon"])).kilometers
            if dist < max_km and dist < closest_dist:
                closest_dist = dist
                closest = m

        if closest:
            result = closest.copy()
            result["distance_km"] = round(closest_dist, 1)
            return result

        return None

    # Capitalised words that are NOT place names. Without this filter
    # `_extract_names` returns every street suffix, direction, and ordinal
    # from the address and tries each as a candidate municipality.
    _STOPLIST = frozenset(
        w.lower()
        for w in {
            # street suffixes
            "Street", "St", "Avenue", "Ave", "Road", "Rd", "Drive", "Dr",
            "Lane", "Ln", "Boulevard", "Blvd", "Way", "Circle", "Cir",
            "Court", "Ct", "Crescent", "Cres", "Place", "Pl", "Terrace", "Tr",
            "Highway", "Hwy", "Route", "Trail",
            # directions
            "North", "South", "East", "West", "NW", "NE", "SW", "SE",
            "Northwest", "Northeast", "Southwest", "Southeast",
            # geometry / land-description keywords
            "Lot", "Block", "Plan", "Parcel", "Section", "Township", "Range",
            "Quarter", "PID", "RR", "Rural",
            # generic words / units
            "Unit", "Suite", "Apt", "Apartment", "Floor", "Building",
            # provinces / country
            "Canada", "Alberta", "BC", "AB", "SK", "MB", "ON", "QC", "NB",
            "NS", "PE", "NL", "YT", "NT", "NU",
            "British", "Columbia", "Saskatchewan", "Manitoba", "Ontario",
            "Quebec", "Brunswick", "Scotia", "Edward", "Island", "Newfoundland",
            "Labrador", "Yukon", "Northwest", "Territories", "Nunavut",
            # months (sometimes appear in legal descriptions)
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        }
    )

    def _extract_names(self, text: str) -> List[str]:
        """Extract capitalised word groups that might be place names.

        Filters against a stoplist of common capitalised non-place words
        so candidates like "Avenue" or "North" don't shadow real cities.
        """
        if not text:
            return []
        words = text.split()
        hints: List[str] = []
        seen = set()

        def _accept(token: str) -> bool:
            return (
                bool(token)
                and token[0].isupper()
                and len(token) > 2
                and token.lower() not in self._STOPLIST
                and not token.isdigit()
            )

        for i, word in enumerate(words):
            clean = word.strip(".,;:()'\"")
            if _accept(clean) and clean not in seen:
                seen.add(clean)
                hints.append(clean)
            if i + 1 < len(words):
                next_clean = words[i + 1].strip(".,;:()'\"")
                if _accept(clean) and _accept(next_clean):
                    pair = f"{clean} {next_clean}"
                    if pair not in seen:
                        seen.add(pair)
                        hints.append(pair)
        return hints

    def _enrich(self, m: Dict) -> Dict:
        """Attach province info and standard service metadata."""
        if m is None:
            return None
        result = m.copy()
        province_code = result.get("province", "")
        province = PROVINCE_INFO.get(province_code, {})
        result["province_name"] = province.get("name", province_code)
        result["planning_act"] = province.get("planning_act", "")
        result["building_code"] = province.get("building_code", "")
        result["zoning_system"] = province.get("zoning_system", province_code)
        result["supported_services"] = [
            "Land Use Bylaw Information",
            "Zoning Maps",
            "Development Permits",
            "Subdivision Applications",
            "Planning Consultation",
        ]
        result["typical_processing_times"] = {
            "development_permit": "4–8 weeks",
            "subdivision": "3–6 months",
            "rezoning": "6–12 months",
        }
        return result
