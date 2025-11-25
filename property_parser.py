import re
from typing import Dict, Optional, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

class PropertyParser:
    """Parse property information from various input formats"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="alberta_land_use_tool")
        
        # Legal description patterns for Alberta
        self.legal_patterns = {
            'quarter_section': re.compile(r'([NSEW]{1,2})\s*(\d{1,2})\s*-\s*(\d{1,3})\s*-\s*(\d{1,3})\s*-\s*([WE])\s*(\d)', re.IGNORECASE),
            'lot_block': re.compile(r'LOT\s*(\d+)\s*,?\s*BLOCK\s*(\d+)\s*,?\s*PLAN\s*(\w+)', re.IGNORECASE),
            'parcel': re.compile(r'PARCEL\s*(\w+)\s*,?\s*PLAN\s*(\w+)', re.IGNORECASE),
            'section': re.compile(r'SECTION\s*(\d{1,2})\s*,?\s*TOWNSHIP\s*(\d{1,3})\s*,?\s*RANGE\s*(\d{1,3})\s*,?\s*([WE])\s*(\d)', re.IGNORECASE)
        }
        
        # Address patterns
        self.address_patterns = {
            'street_address': re.compile(r'(\d+)\s+([A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Circle|Cir|Court|Ct|Crescent|Cres))', re.IGNORECASE),
            'rural_address': re.compile(r'(RR|Rural Route|Range Road|Township Road|Highway|Hwy)\s*(\d+)', re.IGNORECASE),
            'postal_code': re.compile(r'([A-Za-z]\d[A-Za-z]\s*\d[A-Za-z]\d)', re.IGNORECASE)
        }
    
    def parse_property_info(self, address: str = "", legal_description: str = "", additional_info: str = "") -> Optional[Dict]:
        """
        Parse property information from various input formats
        
        Args:
            address: Street address or rural address
            legal_description: Legal land description
            additional_info: Additional property information
        
        Returns:
            Dictionary containing parsed property information
        """
        property_info = {
            'raw_input': {
                'address': address,
                'legal_description': legal_description,
                'additional_info': additional_info
            },
            'parsed_address': None,
            'parsed_legal': None,
            'coordinates': None,
            'municipality_hints': [],
            'property_details': {}
        }
        
        # Parse address
        if address:
            property_info['parsed_address'] = self._parse_address(address)
            
            # Try to geocode the address
            coordinates = self._geocode_address(address)
            if coordinates:
                property_info['coordinates'] = coordinates
        
        # Parse legal description
        if legal_description:
            property_info['parsed_legal'] = self._parse_legal_description(legal_description)
        
        # Extract municipality hints from all inputs
        all_text = f"{address} {legal_description} {additional_info}"
        property_info['municipality_hints'] = self._extract_municipality_hints(all_text)
        
        # Extract property details from additional info
        if additional_info:
            property_info['property_details'] = self._extract_property_details(additional_info)
        
        return property_info if self._is_valid_property_info(property_info) else None
    
    def _parse_address(self, address: str) -> Dict:
        """Parse street or rural address"""
        parsed = {
            'type': 'unknown',
            'components': {},
            'full_address': address.strip()
        }
        
        # Check for street address
        street_match = self.address_patterns['street_address'].search(address)
        if street_match:
            parsed['type'] = 'street'
            parsed['components'] = {
                'number': street_match.group(1),
                'street': street_match.group(2).strip()
            }
        
        # Check for rural address
        rural_match = self.address_patterns['rural_address'].search(address)
        if rural_match:
            parsed['type'] = 'rural'
            parsed['components'] = {
                'road_type': rural_match.group(1),
                'road_number': rural_match.group(2)
            }
        
        # Extract postal code
        postal_match = self.address_patterns['postal_code'].search(address)
        if postal_match:
            parsed['components']['postal_code'] = postal_match.group(1).upper().replace(' ', '')
        
        return parsed
    
    def _parse_legal_description(self, legal_desc: str) -> Dict:
        """Parse legal land description"""
        parsed = {
            'type': 'unknown',
            'components': {},
            'full_description': legal_desc.strip()
        }
        
        # Try different legal description patterns
        for pattern_name, pattern in self.legal_patterns.items():
            match = pattern.search(legal_desc)
            if match:
                parsed['type'] = pattern_name
                
                if pattern_name == 'quarter_section':
                    parsed['components'] = {
                        'quarter': match.group(1),
                        'section': match.group(2),
                        'township': match.group(3),
                        'range': match.group(4),
                        'meridian_direction': match.group(5),
                        'meridian': match.group(6)
                    }
                elif pattern_name == 'lot_block':
                    parsed['components'] = {
                        'lot': match.group(1),
                        'block': match.group(2),
                        'plan': match.group(3)
                    }
                elif pattern_name == 'parcel':
                    parsed['components'] = {
                        'parcel': match.group(1),
                        'plan': match.group(2)
                    }
                elif pattern_name == 'section':
                    parsed['components'] = {
                        'section': match.group(1),
                        'township': match.group(2),
                        'range': match.group(3),
                        'meridian_direction': match.group(4),
                        'meridian': match.group(5)
                    }
                break
        
        return parsed
    
    def _geocode_address(self, address: str) -> Optional[Dict]:
        """Geocode address to get coordinates"""
        try:
            # Add Alberta, Canada to improve geocoding accuracy
            full_address = f"{address}, Alberta, Canada"
            location = self.geolocator.geocode(full_address, timeout=10)
            
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'display_name': location.address
                }
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
        
        return None
    
    def _extract_municipality_hints(self, text: str) -> List[str]:
        """Extract potential municipality names from text"""
        # Common Alberta municipalities between Red Deer and Athabasca
        municipalities = [
            'Red Deer', 'Lacombe', 'Ponoka', 'Wetaskiwin', 'Camrose', 'Leduc',
            'Edmonton', 'St. Albert', 'Sherwood Park', 'Fort Saskatchewan',
            'Morinville', 'Legal', 'Bon Accord', 'Gibbons', 'Redwater',
            'Smoky Lake', 'Vilna', 'Mundare', 'Lamont', 'Bruderheim',
            'Athabasca', 'Boyle', 'Westlock', 'Barrhead', 'Mayerthorpe',
            'Whitecourt', 'Slave Lake', 'High Prairie', 'Valleyview'
        ]
        
        # Also include county names
        counties = [
            'Lacombe County', 'Ponoka County', 'Wetaskiwin County',
            'Camrose County', 'Leduc County', 'Strathcona County',
            'Sturgeon County', 'Parkland County', 'Lac Ste. Anne County',
            'Barrhead County', 'Westlock County', 'Athabasca County'
        ]
        
        all_locations = municipalities + counties
        found_hints = []
        
        text_lower = text.lower()
        for location in all_locations:
            if location.lower() in text_lower:
                found_hints.append(location)
        
        return found_hints
    
    def _extract_property_details(self, additional_info: str) -> Dict:
        """Extract property details from additional information"""
        details = {}
        
        # Extract acreage
        acreage_match = re.search(r'(\d+\.?\d*)\s*acres?', additional_info, re.IGNORECASE)
        if acreage_match:
            details['acreage'] = float(acreage_match.group(1))
        
        # Extract zoning hints
        zoning_keywords = ['commercial', 'residential', 'rural', 'agricultural', 'industrial']
        for keyword in zoning_keywords:
            if keyword in additional_info.lower():
                details.setdefault('zoning_hints', []).append(keyword)
        
        # Extract development intentions
        development_keywords = ['develop', 'cottages', 'subdivision', 'building', 'construction']
        for keyword in development_keywords:
            if keyword in additional_info.lower():
                details.setdefault('development_intentions', []).append(keyword)
        
        # Extract infrastructure mentions
        infrastructure_keywords = ['septic', 'water', 'power', 'sewer', 'gas', 'internet']
        for keyword in infrastructure_keywords:
            if keyword in additional_info.lower():
                details.setdefault('infrastructure_mentions', []).append(keyword)
        
        return details
    
    def _is_valid_property_info(self, property_info: Dict) -> bool:
        """Check if parsed property information is valid"""
        # Must have either a valid address or legal description
        has_address = (property_info.get('parsed_address') and 
                      property_info['parsed_address']['type'] != 'unknown')
        
        has_legal = (property_info.get('parsed_legal') and 
                    property_info['parsed_legal']['type'] != 'unknown')
        
        has_coordinates = property_info.get('coordinates') is not None
        
        has_municipality_hints = len(property_info.get('municipality_hints', [])) > 0
        
        has_property_details = len(property_info.get('property_details', {})) > 0
        
        has_raw_input = bool(property_info.get('raw_input', {}).get('address') or 
                           property_info.get('raw_input', {}).get('legal_description') or
                           property_info.get('raw_input', {}).get('additional_info'))
        
        # Valid if we have at least one way to identify the property
        return has_address or has_legal or has_coordinates or has_municipality_hints or has_property_details or has_raw_input
