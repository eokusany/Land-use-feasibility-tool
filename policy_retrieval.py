import re
import time
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Province-specific zoning classification systems
# ---------------------------------------------------------------------------

PROVINCE_ZONING = {
    "BC": {
        "residential": {
            "RS-1": "Single Family Residential",
            "RS-2": "Single Family Residential (Larger Lot)",
            "RT-1": "Two-Family / Duplex Residential",
            "RM-1": "Low-Density Multi-Family",
            "RM-3": "Medium-Density Multi-Family",
            "RM-5": "High-Density Multi-Family",
            "CD-1": "Comprehensive Development",
        },
        "commercial": {
            "C-1": "Neighbourhood Commercial",
            "C-2": "District Commercial",
            "C-3A": "Downtown Commercial",
            "CV": "Commercial / Village",
        },
        "industrial": {
            "I-1": "Light Industrial",
            "I-2": "General Industrial",
            "M-2": "Industrial (Manufacturing)",
        },
        "rural": {
            "A-1": "General Agricultural",
            "A-2": "Agricultural / Residential",
            "CR-1": "Country Residential",
        },
        "special": {
            "P-1": "Civic / Institutional",
            "OS": "Open Space",
            "HA": "Historic Area",
        },
    },
    "AB": {
        "residential": {
            "R-1": "Single Family Residential",
            "R-2": "Low Density Residential",
            "R-3": "Multi-Family Residential",
            "R-4": "Apartment Residential",
            "MH": "Mobile Home Residential",
        },
        "commercial": {
            "C-1": "Neighbourhood Commercial",
            "C-2": "Community Commercial",
            "C-3": "Highway Commercial",
            "C-4": "Downtown Commercial",
        },
        "industrial": {
            "I-1": "Light Industrial",
            "I-2": "General Industrial",
            "I-3": "Heavy Industrial",
        },
        "rural": {
            "AG": "Agricultural",
            "CR": "Country Residential",
            "RUR": "Rural Residential",
            "RC": "Rural Commercial",
        },
        "special": {
            "P": "Public / Institutional",
            "OS": "Open Space",
            "PUD": "Planned Unit Development",
            "DC": "Direct Control",
        },
    },
    "SK": {
        "residential": {
            "R1": "Single Family Residential",
            "R2": "Two-Family Residential",
            "R3": "Multi-Family Residential",
            "R4": "High-Density Residential",
        },
        "commercial": {
            "C1": "Neighbourhood Commercial",
            "C2": "General Commercial",
            "C3": "Highway / Regional Commercial",
        },
        "industrial": {
            "M1": "Light Industrial",
            "M2": "General Industrial",
            "M3": "Heavy Industrial",
        },
        "rural": {
            "AG": "Agricultural",
            "RR": "Rural Residential",
            "RC": "Rural Commercial",
        },
        "special": {
            "P": "Public / Institutional",
            "OS": "Open Space",
        },
    },
    "MB": {
        "residential": {
            "R1": "Single Family Residential",
            "R2": "Two-Family Residential",
            "R3": "Multiple Dwelling",
            "RM": "Residential Mixed",
        },
        "commercial": {
            "C1": "Convenience Commercial",
            "C2": "Community Commercial",
            "C3": "Regional Commercial",
        },
        "industrial": {
            "M1": "Light Manufacturing",
            "M2": "General Industrial",
        },
        "rural": {
            "AG": "Agricultural",
            "RR": "Rural Residential",
        },
        "special": {
            "P": "Public / Institutional",
            "PR": "Parks and Recreation",
        },
    },
    "ON": {
        "residential": {
            "R": "Residential",
            "R1": "Low-Density Residential",
            "R2": "Medium-Density Residential",
            "R3": "High-Density Residential",
            "RR": "Rural Residential",
        },
        "commercial": {
            "C": "Commercial",
            "C1": "Local Commercial",
            "C2": "General Commercial",
            "MU": "Mixed Use",
        },
        "industrial": {
            "E": "Employment",
            "E1": "Light Industrial / Employment",
            "M": "Industrial",
        },
        "rural": {
            "RU": "Rural",
            "AG": "Agricultural",
            "EP": "Environmental Protection",
        },
        "special": {
            "OS": "Open Space",
            "I": "Institutional",
            "FD": "Future Development",
        },
    },
    "QC": {
        "residential": {
            "H": "Habitation (Residential)",
            "H1": "Faible densité (Low Density)",
            "H2": "Densité moyenne (Medium Density)",
            "H3": "Forte densité (High Density)",
        },
        "commercial": {
            "C": "Commercial",
            "CA": "Artère commerciale (Commercial Arterial)",
            "CC": "Centre-ville (Downtown)",
        },
        "industrial": {
            "I": "Industriel",
            "IL": "Industriel léger (Light Industrial)",
            "IG": "Industriel général (General Industrial)",
        },
        "rural": {
            "A": "Agricole (Agricultural)",
            "AR": "Agri-résidentiel",
        },
        "special": {
            "P": "Public",
            "VE": "Vert / espaces ouverts (Green / Open Space)",
        },
    },
    "NB": {
        "residential": {
            "R1": "Single Unit Dwelling",
            "R2": "Two-Unit Dwelling",
            "R3": "Multiple Unit Dwelling",
        },
        "commercial": {
            "C1": "Local Commercial",
            "C2": "General Commercial",
            "C3": "Highway Commercial",
        },
        "industrial": {
            "I1": "Light Industrial",
            "I2": "General Industrial",
        },
        "rural": {
            "RR": "Rural Residential",
            "A": "Agricultural",
        },
        "special": {
            "P": "Public / Institutional",
            "OS": "Open Space",
        },
    },
    "NS": {
        "residential": {
            "R-1": "Single Unit Residential",
            "R-2": "General Residential",
            "R-3": "Multi-Unit Residential",
            "MR": "Mixed Residential",
        },
        "commercial": {
            "C-1": "General Business",
            "C-2": "Community Commercial",
            "MU": "Mixed Use",
        },
        "industrial": {
            "I-1": "Light Industrial",
            "I-2": "Heavy Industrial",
        },
        "rural": {
            "RU": "Rural",
            "A": "Agricultural",
        },
        "special": {
            "P": "Public / Institutional",
            "OS": "Open Space",
        },
    },
    "PE": {
        "residential": {
            "R1": "Low Density Residential",
            "R2": "Medium Density Residential",
            "R3": "High Density Residential",
        },
        "commercial": {
            "C": "Commercial",
            "C1": "Central Business",
            "C2": "General Commercial",
        },
        "industrial": {
            "I": "Industrial",
        },
        "rural": {
            "A": "Agricultural",
            "RR": "Rural Residential",
            "MR": "Marine Residential",
        },
        "special": {
            "P": "Public",
            "OS": "Open Space",
        },
    },
    "NL": {
        "residential": {
            "R1": "Low Density Residential",
            "R2": "Medium Density Residential",
            "R3": "High Density Residential",
        },
        "commercial": {
            "C1": "Local Commercial",
            "C2": "General Commercial",
        },
        "industrial": {
            "I1": "Light Industrial",
            "I2": "General Industrial",
        },
        "rural": {
            "RR": "Rural Residential",
            "A": "Agricultural",
        },
        "special": {
            "P": "Institutional",
            "OS": "Open Space / Recreation",
        },
    },
    "YT": {
        "residential": {
            "RS": "Single Residential",
            "RR": "Rural Residential",
            "RM": "Multiple Residential",
        },
        "commercial": {
            "C": "Commercial",
            "CG": "General Commercial",
        },
        "industrial": {
            "I": "Industrial",
        },
        "rural": {
            "CR": "Country Residential",
            "AG": "Agricultural",
        },
        "special": {
            "P": "Public",
            "OS": "Open Space",
        },
    },
    "NT": {
        "residential": {
            "R1": "Low Density Residential",
            "R2": "Medium Density Residential",
        },
        "commercial": {
            "C1": "Downtown Commercial",
            "C2": "General Commercial",
        },
        "industrial": {
            "I1": "Light Industrial",
            "I2": "General Industrial",
        },
        "rural": {
            "RR": "Rural Residential",
            "AG": "Agricultural",
        },
        "special": {
            "P": "Public",
        },
    },
    "NU": {
        "residential": {
            "R1": "Residential",
            "R2": "Multi-Unit Residential",
        },
        "commercial": {
            "C1": "Commercial",
        },
        "industrial": {
            "I1": "Industrial",
        },
        "rural": {
            "RR": "Rural",
        },
        "special": {
            "P": "Public / Institutional",
        },
    },
}

# ---------------------------------------------------------------------------
# Setback templates (keyed by zone category)
# ---------------------------------------------------------------------------

SETBACK_TEMPLATES = {
    "residential_low": {"front": "6.0 m", "rear": "6.0 m", "side": "1.5 m"},
    "residential_high": {"front": "6.0 m", "rear": "7.5 m", "side": "3.0 m"},
    "commercial": {"front": "3.0 m", "rear": "6.0 m", "side": "3.0 m"},
    "industrial": {"front": "9.0 m", "rear": "4.5 m", "side": "4.5 m"},
    "rural": {"front": "30.0 m", "rear": "15.0 m", "side": "15.0 m"},
    "rural_commercial": {"front": "15.0 m", "rear": "15.0 m", "side": "7.5 m"},
}

DENSITY_TEMPLATES = {
    "residential_low": {
        "maximum_site_coverage": "40%",
        "minimum_lot_size": "450 m²",
        "maximum_dwelling_units": "1 per lot",
    },
    "residential_high": {
        "maximum_site_coverage": "60%",
        "minimum_lot_size": "300 m²",
        "maximum_floor_area_ratio": "2.5",
    },
    "commercial": {
        "maximum_site_coverage": "80%",
        "minimum_lot_size": "250 m²",
        "maximum_floor_area_ratio": "3.0",
    },
    "industrial": {
        "maximum_site_coverage": "60%",
        "minimum_lot_size": "2,000 m²",
    },
    "rural": {
        "maximum_site_coverage": "25%",
        "minimum_lot_size": "2 ha",
        "maximum_dwelling_units": "1 per lot",
    },
    "rural_commercial": {
        "maximum_site_coverage": "40%",
        "minimum_lot_size": "1 ha",
        "maximum_floor_area_ratio": "0.5",
    },
}

HEIGHT_TEMPLATES = {
    "residential_low": {"maximum_height": "9.0 m", "maximum_stories": "2.5"},
    "residential_high": {"maximum_height": "20.0 m", "maximum_stories": "6"},
    "commercial": {"maximum_height": "15.0 m", "maximum_stories": "4"},
    "industrial": {"maximum_height": "12.0 m", "maximum_stories": "3"},
    "rural": {"maximum_height": "10.0 m", "maximum_stories": "2"},
    "rural_commercial": {"maximum_height": "12.0 m", "maximum_stories": "3"},
}

# ---------------------------------------------------------------------------
# Permitted / discretionary use templates per zone type
# ---------------------------------------------------------------------------

PERMITTED_USES = {
    "residential_low": [
        "Single detached dwelling",
        "Home-based business (minor)",
        "Accessory buildings and structures",
        "Parks and playgrounds",
    ],
    "residential_high": [
        "Multiple unit dwellings (apartments, condominiums)",
        "Townhouses and row housing",
        "Home-based business (minor)",
        "Supportive housing",
        "Child care facilities",
    ],
    "commercial": [
        "Retail stores",
        "Restaurants and food services",
        "Office buildings",
        "Personal services",
        "Financial institutions",
        "Hotels and motels",
    ],
    "industrial": [
        "Light manufacturing",
        "Warehousing and storage",
        "Service and repair shops",
        "Research and development facilities",
    ],
    "rural": [
        "Single detached dwelling",
        "Home occupation",
        "Agricultural uses",
        "Accessory buildings",
        "Hobby farms",
    ],
    "rural_commercial": [
        "Tourist accommodation",
        "Recreation facilities",
        "Small-scale retail",
        "Restaurants",
        "Bed and breakfast",
        "Campgrounds",
    ],
}

DISCRETIONARY_USES = {
    "residential_low": [
        "Secondary suite / garden suite",
        "Bed and breakfast",
        "Licensed day care",
        "Small-scale religious assembly",
    ],
    "residential_high": [
        "Live-work units",
        "Group care facilities",
        "Senior living and long-term care",
    ],
    "commercial": [
        "Drive-through services",
        "Automotive service stations",
        "Outdoor storage",
        "Recreational vehicle parks",
    ],
    "industrial": [
        "Caretaker dwelling",
        "Commercial uses accessory to industrial",
        "Renewable energy generation",
    ],
    "rural": [
        "Bed and breakfast",
        "Secondary suite",
        "Small-scale tourism",
        "Farm-based retail / agri-tourism",
    ],
    "rural_commercial": [
        "Cottage/cabin resort development",
        "RV and campsite parks",
        "Event and conference facilities",
        "Equestrian facilities",
    ],
}


class PolicyRetrieval:
    """Retrieve land use policies and zoning for Canadian municipalities."""

    def __init__(self):
        self.policy_cache: Dict = {}

    def get_land_use_policies(self, municipality_info: Dict, property_info: Dict) -> Dict:
        """
        Return zoning and policy info for a property in a given municipality.
        """
        muni_name = municipality_info.get("name", "")
        cache_key = f"{muni_name}_{id(property_info)}"
        if cache_key in self.policy_cache:
            return self.policy_cache[cache_key]

        province = municipality_info.get("province", "AB")
        zoning_system = PROVINCE_ZONING.get(province, PROVINCE_ZONING["AB"])

        policy_info: Dict = {
            "municipality": muni_name,
            "province": province,
            "zoning": None,
            "zoning_code": None,
            "zone_category": None,
            "land_use_bylaw": None,
            "permitted_uses": [],
            "discretionary_uses": [],
            "setbacks": {},
            "density_restrictions": {},
            "height_restrictions": {},
            "special_provisions": [],
            "development_requirements": [],
            "contact_info": municipality_info.get("contact_info", {}),
            "bylaw_links": [],
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            zoning = self._determine_zoning(province, zoning_system, property_info)
            policy_info.update(zoning)

            bylaw = self._get_bylaw_info(municipality_info)
            if bylaw:
                policy_info["land_use_bylaw"] = bylaw

            policy_info["development_requirements"] = self._get_dev_requirements(
                municipality_info, policy_info.get("zone_category", "")
            )

            self.policy_cache[cache_key] = policy_info
        except Exception as exc:
            policy_info["error"] = f"Error retrieving policy information: {exc}"

        return policy_info

    # ------------------------------------------------------------------
    # Zoning determination
    # ------------------------------------------------------------------

    def _determine_zoning(self, province: str, zoning_system: Dict, property_info: Dict) -> Dict:
        """Choose the most likely zone and fill in all related fields."""
        details = property_info.get("property_details", {})
        acreage = details.get("acreage", 0) or 0
        hints = [h.lower() for h in details.get("zoning_hints", [])]
        intentions = [i.lower() for i in details.get("development_intentions", [])]

        # Determine category
        if "industrial" in hints:
            category = "industrial"
        elif "commercial" in hints or "commercial" in intentions:
            if acreage > 5:
                category = "rural_commercial"
            else:
                category = "commercial"
        elif acreage > 5 or "rural" in hints or "agricultural" in hints:
            category = "rural"
        elif acreage > 2:
            category = "rural"
        elif "residential" in hints or any(t in hints for t in ["apartment", "condo", "multifamily"]):
            category = "residential_high"
        else:
            category = "residential_low"

        # Pick province-appropriate zone code
        zone_map = {
            "residential_low": "residential",
            "residential_high": "residential",
            "commercial": "commercial",
            "rural_commercial": "rural",
            "industrial": "industrial",
            "rural": "rural",
        }

        broad = zone_map.get(category, "residential")
        zone_codes = list(zoning_system.get(broad, {}).items())

        # Pick the first code that roughly matches the density level
        if category == "residential_low" and len(zone_codes) >= 1:
            code, label = zone_codes[0]
        elif category == "residential_high" and len(zone_codes) >= 3:
            code, label = zone_codes[2]
        elif category == "rural_commercial" and "rural" in zoning_system:
            rural_codes = list(zoning_system["rural"].items())
            # Prefer anything with "commercial" or "RC" in the code/label
            rc = next(
                ((c, l) for c, l in rural_codes if "commercial" in l.lower() or "RC" in c),
                rural_codes[-1] if rural_codes else ("RC", "Rural Commercial"),
            )
            code, label = rc
        elif zone_codes:
            code, label = zone_codes[0]
        else:
            code, label = "R1", "Residential"

        # Setback key
        setback_key = category if category in SETBACK_TEMPLATES else "residential_low"

        return {
            "zoning": f"{code} — {label}",
            "zoning_code": code,
            "zone_category": category,
            "permitted_uses": PERMITTED_USES.get(category, PERMITTED_USES["residential_low"]),
            "discretionary_uses": DISCRETIONARY_USES.get(category, DISCRETIONARY_USES["residential_low"]),
            "setbacks": SETBACK_TEMPLATES.get(setback_key, SETBACK_TEMPLATES["residential_low"]),
            "density_restrictions": DENSITY_TEMPLATES.get(setback_key, DENSITY_TEMPLATES["residential_low"]),
            "height_restrictions": HEIGHT_TEMPLATES.get(setback_key, HEIGHT_TEMPLATES["residential_low"]),
        }

    def _get_bylaw_info(self, municipality_info: Dict) -> Optional[Dict]:
        url = municipality_info.get("land_use_bylaw")
        if not url:
            return None
        return {
            "url": url,
            "title": f"{municipality_info.get('name', '')} Land Use Bylaw",
            "sections": [
                {"section": "1", "title": "Definitions and General Provisions", "description": "Definitions, purpose, and general requirements"},
                {"section": "2", "title": "Zoning Districts", "description": "Description of all zoning districts and their intent"},
                {"section": "3", "title": "General Regulations", "description": "Setbacks, height limits, parking, landscaping"},
                {"section": "4", "title": "Development Permits", "description": "Application process and submission requirements"},
                {"section": "5", "title": "Subdivision", "description": "Subdivision standards and approval process"},
                {"section": "6", "title": "Variances and Appeals", "description": "Variance procedures and appeal rights"},
            ],
        }

    def _get_dev_requirements(self, municipality_info: Dict, zone_category: str) -> List[str]:
        province = municipality_info.get("province", "AB")
        province_info_map = {
            "BC": ("BC Building Code", "Local Government Act"),
            "AB": ("Alberta Building Code", "Municipal Government Act"),
            "SK": ("National Building Code", "Planning and Development Act"),
            "MB": ("Manitoba Building Code", "The Planning Act"),
            "ON": ("Ontario Building Code", "Planning Act"),
            "QC": ("Code de construction du Québec", "Loi sur l'aménagement et l'urbanisme"),
            "NB": ("National Building Code", "Community Planning Act"),
            "NS": ("Nova Scotia Building Code", "Municipal Government Act"),
            "PE": ("National Building Code", "Planning Act"),
            "NL": ("National Building Code", "Urban and Rural Planning Act"),
            "YT": ("National Building Code", "Municipal Act"),
            "NT": ("National Building Code", "Cities, Towns and Villages Act"),
            "NU": ("National Building Code", "Nunavut Planning Act"),
        }
        building_code, planning_act = province_info_map.get(province, ("National Building Code", "Municipal Planning Act"))

        reqs = [
            "Development permit required",
            "Building permit required",
            f"Compliance with {building_code}",
            f"Compliance with {planning_act}",
        ]

        if "commercial" in zone_category:
            reqs += [
                "Site plan approval required",
                "Parking and circulation plan submission",
                "Landscaping plan required",
                "Signage permit required",
                "Accessibility compliance (AODA/provincial equivalent)",
            ]
        if "rural" in zone_category:
            reqs += [
                "Septic / wastewater system approval (if applicable)",
                "Water source testing required",
                "Environmental site assessment may be required",
                "Agricultural impact assessment",
            ]
        if "industrial" in zone_category:
            reqs += [
                "Environmental impact assessment required",
                "Stormwater management plan",
                "Traffic impact assessment",
            ]

        if "county" in municipality_info.get("type", "").lower():
            reqs += [
                "County road access approval",
                "Fire protection plan",
                "Waste management plan",
            ]

        return reqs

    # ------------------------------------------------------------------
    # Cottage / resort development analysis (preserved from original)
    # ------------------------------------------------------------------

    def get_cottage_development_analysis(self, policy_info: Dict, property_details: Dict) -> Dict:
        analysis = {
            "feasibility": "Unknown",
            "cottage_potential": {},
            "regulatory_considerations": [],
            "next_steps": [],
        }
        zoning = policy_info.get("zoning", "")
        zone_cat = policy_info.get("zone_category", "")
        acreage = property_details.get("acreage", 0) or 0

        if zone_cat == "rural_commercial" or "commercial" in zoning.lower():
            analysis["feasibility"] = "High"
            if acreage >= 5:
                developable = acreage * 0.4
                units = int(developable * 4.5)
                analysis["cottage_potential"] = {
                    "total_acreage": acreage,
                    "developable_acreage": round(developable, 1),
                    "estimated_cottage_units": units,
                    "phased_development": True,
                    "recommended_phase_1": min(5, units),
                }
            analysis["regulatory_considerations"] = [
                "Tourist accommodation is typically a permitted or discretionary use",
                "Development permit required for each phase",
                "Site plan approval required",
                "Septic system capacity assessment required",
                "Water supply adequacy verification needed",
                "Fire access and safety plan required",
                "Environmental screening may be required",
            ]
        elif zone_cat == "rural" or "rural" in zoning.lower():
            analysis["feasibility"] = "Moderate"
            analysis["regulatory_considerations"] = [
                "Rezoning to Rural Commercial may be required",
                "Discretionary use application may be possible",
                "Bed and breakfast operations typically permitted",
                "Small-scale tourism may be conditionally approved",
            ]
        else:
            analysis["feasibility"] = "Low"
            analysis["regulatory_considerations"] = [
                "Rezoning likely required",
                "Commercial/tourist uses not typically permitted in this zone",
                "Significant regulatory hurdles expected",
                "Pre-application meeting strongly recommended",
            ]

        analysis["next_steps"] = [
            "Schedule pre-application meeting with the planning department",
            "Obtain detailed zoning map and bylaw review",
            "Conduct Phase 1 environmental site assessment",
            "Verify utility capacity and connection availability",
            "Engage a development engineer for servicing analysis",
            "Prepare a preliminary site plan",
        ]
        return analysis
