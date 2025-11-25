import json
import os
from typing import Dict, Optional, List
import requests
from geopy.distance import geodesic

class MunicipalityLookup:
    """Lookup municipality information for Alberta properties"""
    
    def __init__(self):
        self.municipalities_data = self._load_municipalities_data()
        self.supported_regions = self._get_supported_regions()
    
    def _load_municipalities_data(self) -> Dict:
        """Load municipality data from local database"""
        # This would typically load from a database or API
        # For now, we'll use a comprehensive static dataset
        return {
            "cities": {
                "Red Deer": {
                    "type": "city",
                    "population": 100844,
                    "coordinates": {"lat": 52.2681, "lon": -113.8112},
                    "website": "https://www.reddeer.ca",
                    "planning_dept": "planning@reddeer.ca",
                    "land_use_bylaw": "https://www.reddeer.ca/city-government/bylaws-and-policies/land-use-bylaw/",
                    "zoning_map": "https://www.reddeer.ca/city-services/planning-and-development/zoning-maps/",
                    "contact_info": {
                        "phone": "403-342-8111",
                        "address": "4914 48th Ave, Red Deer, AB T4N 3T4"
                    }
                },
                "Edmonton": {
                    "type": "city",
                    "population": 1010899,
                    "coordinates": {"lat": 53.5461, "lon": -113.4938},
                    "website": "https://www.edmonton.ca",
                    "planning_dept": "development@edmonton.ca",
                    "land_use_bylaw": "https://www.edmonton.ca/city_government/bylaws/zoning-bylaw",
                    "zoning_map": "https://maps.edmonton.ca/map.aspx?id=ZoningBylaw",
                    "contact_info": {
                        "phone": "311",
                        "address": "1 Sir Winston Churchill Square, Edmonton, AB T5J 2R7"
                    }
                },
                "Lacombe": {
                    "type": "city",
                    "population": 13057,
                    "coordinates": {"lat": 52.4675, "lon": -113.7364},
                    "website": "https://www.lacombe.ca",
                    "planning_dept": "planning@lacombe.ca",
                    "land_use_bylaw": "https://www.lacombe.ca/government/bylaws/",
                    "contact_info": {
                        "phone": "403-782-6666",
                        "address": "5432 56 Ave, Lacombe, AB T4L 1E9"
                    }
                },
                "Wetaskiwin": {
                    "type": "city",
                    "population": 12655,
                    "coordinates": {"lat": 52.9692, "lon": -113.3747},
                    "website": "https://www.wetaskiwin.ca",
                    "planning_dept": "planning@wetaskiwin.ca",
                    "land_use_bylaw": "https://www.wetaskiwin.ca/government/bylaws-policies/",
                    "contact_info": {
                        "phone": "780-361-4400",
                        "address": "4905 50 Ave, Wetaskiwin, AB T9A 0S7"
                    }
                },
                "Camrose": {
                    "type": "city",
                    "population": 18742,
                    "coordinates": {"lat": 53.0167, "lon": -112.8333},
                    "website": "https://www.camrose.ca",
                    "planning_dept": "planning@camrose.ca",
                    "land_use_bylaw": "https://www.camrose.ca/government/bylaws/",
                    "contact_info": {
                        "phone": "780-672-4428",
                        "address": "4703 50 Ave, Camrose, AB T4V 0P7"
                    }
                },
                "Athabasca": {
                    "type": "town",
                    "population": 2965,
                    "coordinates": {"lat": 54.7186, "lon": -113.2856},
                    "website": "https://www.athabasca.ca",
                    "planning_dept": "cao@athabasca.ca",
                    "land_use_bylaw": "https://www.athabasca.ca/government/bylaws/",
                    "contact_info": {
                        "phone": "780-675-2273",
                        "address": "4904 50 St, Athabasca, AB T9S 1E2"
                    }
                }
            },
            "counties": {
                "Lacombe County": {
                    "type": "county",
                    "coordinates": {"lat": 52.4000, "lon": -113.8000},
                    "website": "https://www.lacombecounty.com",
                    "planning_dept": "planning@lacombecounty.com",
                    "land_use_bylaw": "https://www.lacombecounty.com/government/bylaws/",
                    "contact_info": {
                        "phone": "403-782-8060",
                        "address": "4611 52 Ave, Lacombe, AB T4L 1G3"
                    }
                },
                "Ponoka County": {
                    "type": "county",
                    "coordinates": {"lat": 52.6833, "lon": -113.5833},
                    "website": "https://www.ponokacounty.com",
                    "planning_dept": "planning@ponokacounty.com",
                    "land_use_bylaw": "https://www.ponokacounty.com/government/bylaws/",
                    "contact_info": {
                        "phone": "403-783-3333",
                        "address": "5506 57 Ave, Ponoka, AB T4J 1A1"
                    }
                },
                "Wetaskiwin County": {
                    "type": "county",
                    "coordinates": {"lat": 53.0000, "lon": -113.5000},
                    "website": "https://www.county.wetaskiwin.ab.ca",
                    "planning_dept": "planning@county.wetaskiwin.ab.ca",
                    "land_use_bylaw": "https://www.county.wetaskiwin.ab.ca/government/bylaws/",
                    "contact_info": {
                        "phone": "780-352-3321",
                        "address": "Multi-Municipal Building, 4905 51 Ave, Wetaskiwin, AB T9A 1P2"
                    }
                },
                "Camrose County": {
                    "type": "county",
                    "coordinates": {"lat": 53.0000, "lon": -112.5000},
                    "website": "https://www.camrosecounty.ab.ca",
                    "planning_dept": "planning@camrosecounty.ab.ca",
                    "land_use_bylaw": "https://www.camrosecounty.ab.ca/government/bylaws/",
                    "contact_info": {
                        "phone": "780-672-4446",
                        "address": "#10, 3755 43 Ave, Camrose, AB T4V 3S8"
                    }
                },
                "Leduc County": {
                    "type": "county",
                    "coordinates": {"lat": 53.2667, "lon": -113.5500},
                    "website": "https://www.leduc-county.com",
                    "planning_dept": "planning@leduc-county.com",
                    "land_use_bylaw": "https://www.leduc-county.com/government/bylaws/",
                    "contact_info": {
                        "phone": "780-955-3555",
                        "address": "1101 5 St, Nisku, AB T9E 2X3"
                    }
                },
                "Strathcona County": {
                    "type": "county",
                    "coordinates": {"lat": 53.5167, "lon": -113.2000},
                    "website": "https://www.strathcona.ca",
                    "planning_dept": "planning@strathcona.ca",
                    "land_use_bylaw": "https://www.strathcona.ca/council-county/bylaws/",
                    "contact_info": {
                        "phone": "780-464-8111",
                        "address": "2001 Sherwood Dr, Sherwood Park, AB T8A 3W7"
                    }
                },
                "Sturgeon County": {
                    "type": "county",
                    "coordinates": {"lat": 53.8000, "lon": -113.6000},
                    "website": "https://www.sturgeoncounty.ca",
                    "planning_dept": "planning@sturgeoncounty.ca",
                    "land_use_bylaw": "https://www.sturgeoncounty.ca/government/bylaws/",
                    "contact_info": {
                        "phone": "780-939-4321",
                        "address": "9613 100 St, Morinville, AB T8R 1L9"
                    }
                },
                "Parkland County": {
                    "type": "county",
                    "coordinates": {"lat": 53.7000, "lon": -114.0000},
                    "website": "https://www.parklandcounty.com",
                    "planning_dept": "planning@parklandcounty.com",
                    "land_use_bylaw": "https://www.parklandcounty.com/government/bylaws/",
                    "contact_info": {
                        "phone": "780-968-8888",
                        "address": "53109A Hwy 779, Parkland County, AB T7Z 1R1"
                    }
                },
                "Athabasca County": {
                    "type": "county",
                    "coordinates": {"lat": 54.5000, "lon": -113.0000},
                    "website": "https://www.athabascacounty.com",
                    "planning_dept": "planning@athabascacounty.com",
                    "land_use_bylaw": "https://www.athabascacounty.com/government/bylaws/",
                    "contact_info": {
                        "phone": "780-675-2273",
                        "address": "4904 50 St, Athabasca, AB T9S 1E2"
                    }
                }
            }
        }
    
    def _get_supported_regions(self) -> List[str]:
        """Get list of supported regions"""
        regions = []
        for category in self.municipalities_data.values():
            regions.extend(category.keys())
        return regions
    
    def find_municipality(self, property_info: Dict) -> Optional[Dict]:
        """
        Find the municipality for a given property
        
        Args:
            property_info: Parsed property information
            
        Returns:
            Municipality information dictionary
        """
        # Try different methods to identify municipality
        
        # Method 1: Check municipality hints from text
        municipality_hints = property_info.get('municipality_hints', [])
        for hint in municipality_hints:
            municipality = self._find_by_name(hint)
            if municipality:
                return municipality
        
        # Method 2: Use coordinates if available
        coordinates = property_info.get('coordinates')
        if coordinates:
            municipality = self._find_by_coordinates(
                coordinates['latitude'], 
                coordinates['longitude']
            )
            if municipality:
                return municipality
        
        # Method 3: Try to geocode legal description
        legal_desc = property_info.get('parsed_legal')
        if legal_desc and legal_desc.get('type') != 'unknown':
            municipality = self._find_by_legal_description(legal_desc)
            if municipality:
                return municipality
        
        # Method 4: Fallback - try to extract from address components
        address = property_info.get('parsed_address')
        if address:
            municipality = self._find_by_address_components(address)
            if municipality:
                return municipality
        
        return None
    
    def _find_by_name(self, name: str) -> Optional[Dict]:
        """Find municipality by name"""
        name_lower = name.lower()
        
        # Check cities first
        for city_name, city_data in self.municipalities_data['cities'].items():
            if city_name.lower() == name_lower or city_name.lower() in name_lower:
                result = city_data.copy()
                result['name'] = city_name
                result['category'] = 'city'
                return result
        
        # Check counties
        for county_name, county_data in self.municipalities_data['counties'].items():
            if county_name.lower() == name_lower or county_name.lower() in name_lower:
                result = county_data.copy()
                result['name'] = county_name
                result['category'] = 'county'
                return result
        
        return None
    
    def _find_by_coordinates(self, lat: float, lon: float) -> Optional[Dict]:
        """Find municipality by coordinates using proximity"""
        closest_municipality = None
        closest_distance = float('inf')
        
        # Check all municipalities
        for category_name, category_data in self.municipalities_data.items():
            for municipality_name, municipality_data in category_data.items():
                muni_coords = municipality_data.get('coordinates')
                if muni_coords:
                    distance = geodesic(
                        (lat, lon),
                        (muni_coords['lat'], muni_coords['lon'])
                    ).kilometers
                    
                    # Consider within 50km as potential match
                    if distance < 50 and distance < closest_distance:
                        closest_distance = distance
                        result = municipality_data.copy()
                        result['name'] = municipality_name
                        result['category'] = category_name.rstrip('s')  # Remove 's' from 'cities'/'counties'
                        result['distance_km'] = distance
                        closest_municipality = result
        
        return closest_municipality
    
    def _find_by_legal_description(self, legal_desc: Dict) -> Optional[Dict]:
        """Find municipality by legal description"""
        # This would typically involve more sophisticated mapping
        # For now, we'll use basic heuristics based on township/range
        
        components = legal_desc.get('components', {})
        
        if legal_desc.get('type') in ['quarter_section', 'section']:
            township = components.get('township')
            range_num = components.get('range')
            
            if township and range_num:
                try:
                    township_int = int(township)
                    range_int = int(range_num)
                    
                    # Basic mapping based on township/range (simplified)
                    if 40 <= township_int <= 50 and 20 <= range_int <= 30:
                        return self._find_by_name("Red Deer")
                    elif 50 <= township_int <= 60 and 20 <= range_int <= 30:
                        return self._find_by_name("Edmonton")
                    elif 60 <= township_int <= 70 and 20 <= range_int <= 30:
                        return self._find_by_name("Athabasca")
                    
                except ValueError:
                    pass
        
        return None
    
    def _find_by_address_components(self, address: Dict) -> Optional[Dict]:
        """Find municipality by address components"""
        # Extract potential municipality names from address
        full_address = address.get('full_address', '')
        
        # Try to find municipality names in the address
        for hint in self._extract_location_hints(full_address):
            municipality = self._find_by_name(hint)
            if municipality:
                return municipality
        
        return None
    
    def _extract_location_hints(self, text: str) -> List[str]:
        """Extract potential location names from text"""
        # This is a simplified version - in practice, you'd use more sophisticated NLP
        words = text.split()
        hints = []
        
        # Look for capitalized words that might be place names
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 3:
                hints.append(word)
                
                # Also check two-word combinations
                if i < len(words) - 1 and words[i + 1][0].isupper():
                    hints.append(f"{word} {words[i + 1]}")
        
        return hints
    
    def get_supported_municipalities(self) -> List[Dict]:
        """Get list of all supported municipalities"""
        municipalities = []
        
        for category_name, category_data in self.municipalities_data.items():
            for municipality_name, municipality_data in category_data.items():
                municipality = municipality_data.copy()
                municipality['name'] = municipality_name
                municipality['category'] = category_name.rstrip('s')
                municipalities.append(municipality)
        
        return sorted(municipalities, key=lambda x: x['name'])
    
    def get_municipality_details(self, municipality_name: str) -> Optional[Dict]:
        """Get detailed information about a specific municipality"""
        municipality = self._find_by_name(municipality_name)
        if municipality:
            # Add additional details that might be useful for land use analysis
            municipality['supported_services'] = [
                'Land Use Bylaw Information',
                'Zoning Maps',
                'Development Permits',
                'Subdivision Applications',
                'Planning Consultation'
            ]
            
            municipality['typical_processing_times'] = {
                'development_permit': '4-6 weeks',
                'subdivision': '3-6 months',
                'rezoning': '6-12 months'
            }
        
        return municipality
