"""
CanLand — Canadian Land Use Feasibility Platform
Comprehensive municipality database covering all 13 provinces and territories.
"""

PROVINCE_INFO = {
    "BC": {
        "name": "British Columbia",
        "full_name": "Province of British Columbia",
        "zoning_system": "BC",
        "planning_act": "Local Government Act",
        "building_code": "BC Building Code",
    },
    "AB": {
        "name": "Alberta",
        "full_name": "Province of Alberta",
        "zoning_system": "AB",
        "planning_act": "Municipal Government Act",
        "building_code": "Alberta Building Code",
    },
    "SK": {
        "name": "Saskatchewan",
        "full_name": "Province of Saskatchewan",
        "zoning_system": "SK",
        "planning_act": "The Planning and Development Act",
        "building_code": "National Building Code of Canada (as adopted by SK)",
    },
    "MB": {
        "name": "Manitoba",
        "full_name": "Province of Manitoba",
        "zoning_system": "MB",
        "planning_act": "The Planning Act",
        "building_code": "Manitoba Building Code",
    },
    "ON": {
        "name": "Ontario",
        "full_name": "Province of Ontario",
        "zoning_system": "ON",
        "planning_act": "Planning Act",
        "building_code": "Ontario Building Code",
    },
    "QC": {
        "name": "Quebec",
        "full_name": "Province of Quebec",
        "zoning_system": "QC",
        "planning_act": "Loi sur l'aménagement et l'urbanisme",
        "building_code": "Code de construction du Québec",
    },
    "NB": {
        "name": "New Brunswick",
        "full_name": "Province of New Brunswick",
        "zoning_system": "NB",
        "planning_act": "Community Planning Act",
        "building_code": "National Building Code of Canada (as adopted by NB)",
    },
    "NS": {
        "name": "Nova Scotia",
        "full_name": "Province of Nova Scotia",
        "zoning_system": "NS",
        "planning_act": "Municipal Government Act",
        "building_code": "Nova Scotia Building Code",
    },
    "PE": {
        "name": "Prince Edward Island",
        "full_name": "Province of Prince Edward Island",
        "zoning_system": "PE",
        "planning_act": "Planning Act",
        "building_code": "National Building Code of Canada (as adopted by PEI)",
    },
    "NL": {
        "name": "Newfoundland and Labrador",
        "full_name": "Province of Newfoundland and Labrador",
        "zoning_system": "NL",
        "planning_act": "Urban and Rural Planning Act",
        "building_code": "National Building Code of Canada (as adopted by NL)",
    },
    "YT": {
        "name": "Yukon",
        "full_name": "Yukon Territory",
        "zoning_system": "YT",
        "planning_act": "Municipal Act",
        "building_code": "National Building Code of Canada (as adopted by YT)",
    },
    "NT": {
        "name": "Northwest Territories",
        "full_name": "Northwest Territories",
        "zoning_system": "NT",
        "planning_act": "Cities, Towns and Villages Act",
        "building_code": "National Building Code of Canada (as adopted by NT)",
    },
    "NU": {
        "name": "Nunavut",
        "full_name": "Nunavut Territory",
        "zoning_system": "NU",
        "planning_act": "Nunavut Planning and Project Assessment Act",
        "building_code": "National Building Code of Canada (as adopted by NU)",
    },
}

CANADIAN_MUNICIPALITIES = {
    "BC": {
        "Vancouver": {
            "type": "city",
            "population": 662248,
            "coordinates": {"lat": 49.2827, "lon": -123.1207},
            "website": "https://vancouver.ca",
            "planning_dept": "planning@vancouver.ca",
            "land_use_bylaw": "https://vancouver.ca/home-property-development/zoning-and-land-use-policies.aspx",
            "zoning_map": "https://vancouver.ca/home-property-development/zoning-map.aspx",
            "contact_info": {
                "phone": "604-873-7000",
                "address": "453 West 12th Ave, Vancouver, BC V5Y 1V4"
            }
        },
        "Surrey": {
            "type": "city",
            "population": 568322,
            "coordinates": {"lat": 49.1913, "lon": -122.8490},
            "website": "https://www.surrey.ca",
            "planning_dept": "planning@surrey.ca",
            "land_use_bylaw": "https://www.surrey.ca/services-payments/permits-licences-bylaws/bylaws/zoning-bylaw",
            "contact_info": {
                "phone": "604-591-4011",
                "address": "13450 104 Ave, Surrey, BC V3T 1V8"
            }
        },
        "Burnaby": {
            "type": "city",
            "population": 249125,
            "coordinates": {"lat": 49.2488, "lon": -122.9805},
            "website": "https://www.burnaby.ca",
            "planning_dept": "planning@burnaby.ca",
            "land_use_bylaw": "https://www.burnaby.ca/city-services/permits-and-licences/zoning",
            "contact_info": {
                "phone": "604-294-7944",
                "address": "4949 Canada Way, Burnaby, BC V5G 1M2"
            }
        },
        "Richmond": {
            "type": "city",
            "population": 209937,
            "coordinates": {"lat": 49.1666, "lon": -123.1336},
            "website": "https://www.richmond.ca",
            "planning_dept": "planning@richmond.ca",
            "land_use_bylaw": "https://www.richmond.ca/plandev/planning/devapps/zoning/default.htm",
            "contact_info": {
                "phone": "604-276-4000",
                "address": "6911 No. 3 Rd, Richmond, BC V6Y 2C1"
            }
        },
        "Kelowna": {
            "type": "city",
            "population": 144576,
            "coordinates": {"lat": 49.8880, "lon": -119.4960},
            "website": "https://www.kelowna.ca",
            "planning_dept": "planning@kelowna.ca",
            "land_use_bylaw": "https://www.kelowna.ca/city-services/planning-development",
            "contact_info": {
                "phone": "250-469-8600",
                "address": "1435 Water St, Kelowna, BC V1Y 1J4"
            }
        },
        "Abbotsford": {
            "type": "city",
            "population": 153524,
            "coordinates": {"lat": 49.0504, "lon": -122.3045},
            "website": "https://www.abbotsford.ca",
            "planning_dept": "planning@abbotsford.ca",
            "land_use_bylaw": "https://www.abbotsford.ca/city-services/land-development/zoning-bylaw",
            "contact_info": {
                "phone": "604-853-2281",
                "address": "32315 South Fraser Way, Abbotsford, BC V2T 1W7"
            }
        },
        "Victoria": {
            "type": "city",
            "population": 91867,
            "coordinates": {"lat": 48.4284, "lon": -123.3656},
            "website": "https://www.victoria.ca",
            "planning_dept": "planning@victoria.ca",
            "land_use_bylaw": "https://www.victoria.ca/EN/main/residents/planning/zoning-bylaw.html",
            "contact_info": {
                "phone": "250-385-5711",
                "address": "1 Centennial Square, Victoria, BC V8W 1P6"
            }
        },
        "Coquitlam": {
            "type": "city",
            "population": 148625,
            "coordinates": {"lat": 49.2838, "lon": -122.7932},
            "website": "https://www.coquitlam.ca",
            "planning_dept": "planning@coquitlam.ca",
            "land_use_bylaw": "https://www.coquitlam.ca/city-services/planning/zoning-bylaw.aspx",
            "contact_info": {
                "phone": "604-927-3000",
                "address": "3000 Guildford Way, Coquitlam, BC V3B 7N2"
            }
        },
        "Kamloops": {
            "type": "city",
            "population": 97902,
            "coordinates": {"lat": 50.6745, "lon": -120.3273},
            "website": "https://www.kamloops.ca",
            "planning_dept": "planning@kamloops.ca",
            "land_use_bylaw": "https://www.kamloops.ca/business-development/planning/zoning-bylaw",
            "contact_info": {
                "phone": "250-828-3311",
                "address": "7 Victoria St W, Kamloops, BC V2C 1A2"
            }
        },
        "Nanaimo": {
            "type": "city",
            "population": 99863,
            "coordinates": {"lat": 49.1659, "lon": -123.9401},
            "website": "https://www.nanaimo.ca",
            "planning_dept": "planning@nanaimo.ca",
            "land_use_bylaw": "https://www.nanaimo.ca/EN/main/business/Planning-and-Development/Zoning-and-Bylaws.html",
            "contact_info": {
                "phone": "250-755-4400",
                "address": "455 Wallace St, Nanaimo, BC V9R 5J6"
            }
        },
        "Prince George": {
            "type": "city",
            "population": 89605,
            "coordinates": {"lat": 53.9171, "lon": -122.7497},
            "website": "https://www.princegeorge.ca",
            "planning_dept": "planning@princegeorge.ca",
            "land_use_bylaw": "https://www.princegeorge.ca/cityservices/bylaws/Pages/ZoningBylaw.aspx",
            "contact_info": {
                "phone": "250-561-7600",
                "address": "1100 Patricia Blvd, Prince George, BC V2L 3V9"
            }
        },
        "Chilliwack": {
            "type": "city",
            "population": 93203,
            "coordinates": {"lat": 49.1579, "lon": -121.9514},
            "website": "https://www.chilliwack.com",
            "planning_dept": "planning@chilliwack.ca",
            "land_use_bylaw": "https://www.chilliwack.com/main/page.cfm?id=1011",
            "contact_info": {
                "phone": "604-793-2911",
                "address": "8550 Young Rd, Chilliwack, BC V2P 8A4"
            }
        },
    },

    "AB": {
        "Calgary": {
            "type": "city",
            "population": 1336000,
            "coordinates": {"lat": 51.0447, "lon": -114.0719},
            "website": "https://www.calgary.ca",
            "planning_dept": "planning@calgary.ca",
            "land_use_bylaw": "https://www.calgary.ca/pda/pd/land-use-bylaw-1p2007/land-use-bylaw-1p2007.html",
            "zoning_map": "https://maps.calgary.ca/CalgaryLandUse/",
            "contact_info": {
                "phone": "311",
                "address": "800 Macleod Trail SE, Calgary, AB T2G 2M3"
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
        "Red Deer": {
            "type": "city",
            "population": 100844,
            "coordinates": {"lat": 52.2681, "lon": -113.8112},
            "website": "https://www.reddeer.ca",
            "planning_dept": "planning@reddeer.ca",
            "land_use_bylaw": "https://www.reddeer.ca/city-government/bylaws-and-policies/land-use-bylaw/",
            "contact_info": {
                "phone": "403-342-8111",
                "address": "4914 48th Ave, Red Deer, AB T4N 3T4"
            }
        },
        "Lethbridge": {
            "type": "city",
            "population": 101482,
            "coordinates": {"lat": 49.6956, "lon": -112.8451},
            "website": "https://www.lethbridge.ca",
            "planning_dept": "planning@lethbridge.ca",
            "land_use_bylaw": "https://www.lethbridge.ca/living-here/planning-development/land-use-bylaw.html",
            "contact_info": {
                "phone": "403-320-3111",
                "address": "910 4 Ave S, Lethbridge, AB T1J 0P6"
            }
        },
        "St. Albert": {
            "type": "city",
            "population": 69588,
            "coordinates": {"lat": 53.6302, "lon": -113.6253},
            "website": "https://stalbert.ca",
            "planning_dept": "planning@stalbert.ca",
            "land_use_bylaw": "https://stalbert.ca/city/bylaws/land-use-bylaw/",
            "contact_info": {
                "phone": "780-459-1500",
                "address": "5 St. Anne St, St. Albert, AB T8N 3Z9"
            }
        },
        "Medicine Hat": {
            "type": "city",
            "population": 63260,
            "coordinates": {"lat": 50.0418, "lon": -110.6774},
            "website": "https://www.medicinehat.ca",
            "planning_dept": "planning@medicinehat.ca",
            "land_use_bylaw": "https://www.medicinehat.ca/government/city-services/land-development/land-use-bylaw",
            "contact_info": {
                "phone": "403-529-8100",
                "address": "580 1st St SE, Medicine Hat, AB T1A 8E6"
            }
        },
        "Grande Prairie": {
            "type": "city",
            "population": 68556,
            "coordinates": {"lat": 55.1707, "lon": -118.7964},
            "website": "https://www.cityofgp.com",
            "planning_dept": "planning@cityofgp.com",
            "land_use_bylaw": "https://www.cityofgp.com/city-government/bylaws/land-use-bylaw",
            "contact_info": {
                "phone": "780-538-0300",
                "address": "10205 98th St, Grande Prairie, AB T8V 2E7"
            }
        },
        "Airdrie": {
            "type": "city",
            "population": 73698,
            "coordinates": {"lat": 51.2917, "lon": -114.0144},
            "website": "https://www.airdrie.ca",
            "planning_dept": "planning@airdrie.ca",
            "land_use_bylaw": "https://www.airdrie.ca/index.cfm?serviceID=1175",
            "contact_info": {
                "phone": "403-948-8800",
                "address": "400 Main St SE, Airdrie, AB T4B 3C3"
            }
        },
        "Spruce Grove": {
            "type": "city",
            "population": 36957,
            "coordinates": {"lat": 53.5453, "lon": -113.9005},
            "website": "https://www.sprucegrove.org",
            "planning_dept": "planning@sprucegrove.org",
            "land_use_bylaw": "https://www.sprucegrove.org/government/city-services/development-planning/",
            "contact_info": {
                "phone": "780-962-7612",
                "address": "315 Jespersen Ave, Spruce Grove, AB T7X 3E8"
            }
        },
        "Fort McMurray": {
            "type": "city",
            "population": 68980,
            "coordinates": {"lat": 56.7265, "lon": -111.3790},
            "website": "https://www.rmwb.ca",
            "planning_dept": "planning@rmwb.ca",
            "land_use_bylaw": "https://www.rmwb.ca/en/planning-and-development/land-use-bylaw.aspx",
            "contact_info": {
                "phone": "780-743-7000",
                "address": "9909 Franklin Ave, Fort McMurray, AB T9H 2K4"
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
    },

    "SK": {
        "Saskatoon": {
            "type": "city",
            "population": 317480,
            "coordinates": {"lat": 52.1332, "lon": -106.6700},
            "website": "https://www.saskatoon.ca",
            "planning_dept": "planning@saskatoon.ca",
            "land_use_bylaw": "https://www.saskatoon.ca/business-development/planning-development/zoning-bylaw",
            "zoning_map": "https://opendata-saskatoon.cloudapp.net/ZoningMap/",
            "contact_info": {
                "phone": "306-975-3240",
                "address": "222 3rd Ave N, Saskatoon, SK S7K 0J5"
            }
        },
        "Regina": {
            "type": "city",
            "population": 226404,
            "coordinates": {"lat": 50.4452, "lon": -104.6189},
            "website": "https://www.regina.ca",
            "planning_dept": "planning@regina.ca",
            "land_use_bylaw": "https://www.regina.ca/city-government/bylaws/zoning-bylaw/",
            "contact_info": {
                "phone": "306-777-7000",
                "address": "2476 Victoria Ave, Regina, SK S4P 3C8"
            }
        },
        "Prince Albert": {
            "type": "city",
            "population": 37756,
            "coordinates": {"lat": 53.2033, "lon": -105.7531},
            "website": "https://www.citypa.ca",
            "planning_dept": "planning@citypa.ca",
            "land_use_bylaw": "https://www.citypa.ca/en/living-here/planning-and-development.aspx",
            "contact_info": {
                "phone": "306-953-4305",
                "address": "1084 Central Ave, Prince Albert, SK S6V 7P3"
            }
        },
        "Moose Jaw": {
            "type": "city",
            "population": 34421,
            "coordinates": {"lat": 50.3934, "lon": -105.5345},
            "website": "https://www.moosejaw.ca",
            "planning_dept": "planning@moosejaw.ca",
            "land_use_bylaw": "https://www.moosejaw.ca/land-use",
            "contact_info": {
                "phone": "306-694-4400",
                "address": "228 Main St N, Moose Jaw, SK S6H 3J8"
            }
        },
        "Yorkton": {
            "type": "city",
            "population": 20643,
            "coordinates": {"lat": 51.2133, "lon": -102.4628},
            "website": "https://www.yorkton.ca",
            "planning_dept": "planning@yorkton.ca",
            "land_use_bylaw": "https://www.yorkton.ca/government/bylaws/",
            "contact_info": {
                "phone": "306-786-1700",
                "address": "37 Third Ave N, Yorkton, SK S3N 2W3"
            }
        },
        "Swift Current": {
            "type": "city",
            "population": 16604,
            "coordinates": {"lat": 50.2855, "lon": -107.7997},
            "website": "https://www.swiftcurrent.ca",
            "planning_dept": "planning@swiftcurrent.ca",
            "land_use_bylaw": "https://www.swiftcurrent.ca/city-services/planning-development",
            "contact_info": {
                "phone": "306-778-2757",
                "address": "177 First Ave NE, Swift Current, SK S9H 2B4"
            }
        },
        "Lloydminster": {
            "type": "city",
            "population": 31410,
            "coordinates": {"lat": 53.2784, "lon": -110.0092},
            "website": "https://www.lloydminster.ca",
            "planning_dept": "planning@lloydminster.ca",
            "land_use_bylaw": "https://www.lloydminster.ca/planning",
            "contact_info": {
                "phone": "780-875-6184",
                "address": "4420 50th Ave, Lloydminster, AB/SK T9V 0W2"
            }
        },
        "Weyburn": {
            "type": "city",
            "population": 11234,
            "coordinates": {"lat": 49.6600, "lon": -103.8500},
            "website": "https://www.weyburn.ca",
            "planning_dept": "planning@weyburn.ca",
            "land_use_bylaw": "https://www.weyburn.ca/government/bylaws/",
            "contact_info": {
                "phone": "306-848-3200",
                "address": "57 3rd St NE, Weyburn, SK S4H 0W5"
            }
        },
    },

    "MB": {
        "Winnipeg": {
            "type": "city",
            "population": 778489,
            "coordinates": {"lat": 49.8951, "lon": -97.1384},
            "website": "https://www.winnipeg.ca",
            "planning_dept": "planning@winnipeg.ca",
            "land_use_bylaw": "https://www.winnipeg.ca/ppd/ZoningBylaw/Default.stm",
            "zoning_map": "https://www.winnipeg.ca/ppd/Maps/ZoningMaps.stm",
            "contact_info": {
                "phone": "311",
                "address": "510 Main St, Winnipeg, MB R3B 1B9"
            }
        },
        "Brandon": {
            "type": "city",
            "population": 51313,
            "coordinates": {"lat": 49.8481, "lon": -99.9500},
            "website": "https://www.brandon.ca",
            "planning_dept": "planning@brandon.ca",
            "land_use_bylaw": "https://www.brandon.ca/index.cfm/planning/zoning",
            "contact_info": {
                "phone": "204-729-2186",
                "address": "410 9th St, Brandon, MB R7A 6A2"
            }
        },
        "Steinbach": {
            "type": "city",
            "population": 17806,
            "coordinates": {"lat": 49.5258, "lon": -96.6839},
            "website": "https://www.steinbach.ca",
            "planning_dept": "planning@steinbach.ca",
            "land_use_bylaw": "https://www.steinbach.ca/government/bylaws/",
            "contact_info": {
                "phone": "204-326-9877",
                "address": "284 Reimer Ave, Steinbach, MB R5G 0A2"
            }
        },
        "Winkler": {
            "type": "city",
            "population": 14891,
            "coordinates": {"lat": 49.1810, "lon": -97.9398},
            "website": "https://www.winkler.ca",
            "planning_dept": "planning@winkler.ca",
            "land_use_bylaw": "https://www.winkler.ca/planning-development",
            "contact_info": {
                "phone": "204-325-9524",
                "address": "185 Main St, Winkler, MB R6W 1B4"
            }
        },
        "Portage la Prairie": {
            "type": "city",
            "population": 13270,
            "coordinates": {"lat": 49.9723, "lon": -98.2920},
            "website": "https://www.portagelap.com",
            "planning_dept": "planning@portagelap.com",
            "land_use_bylaw": "https://www.portagelap.com/government/bylaws/",
            "contact_info": {
                "phone": "204-239-8341",
                "address": "97 Saskatchewan Ave E, Portage la Prairie, MB R1N 0L8"
            }
        },
        "Thompson": {
            "type": "city",
            "population": 13678,
            "coordinates": {"lat": 55.7435, "lon": -97.8558},
            "website": "https://www.thompson.ca",
            "planning_dept": "planning@thompson.ca",
            "land_use_bylaw": "https://www.thompson.ca/planning",
            "contact_info": {
                "phone": "204-677-7910",
                "address": "226 Mystery Lake Rd, Thompson, MB R8N 1S6"
            }
        },
        "Selkirk": {
            "type": "city",
            "population": 10278,
            "coordinates": {"lat": 50.1437, "lon": -96.8834},
            "website": "https://www.cityofselkirk.com",
            "planning_dept": "planning@cityofselkirk.com",
            "land_use_bylaw": "https://www.cityofselkirk.com/government/bylaws/",
            "contact_info": {
                "phone": "204-785-4900",
                "address": "200 Eaton Ave, Selkirk, MB R1A 0W6"
            }
        },
    },

    "ON": {
        "Toronto": {
            "type": "city",
            "population": 2794356,
            "coordinates": {"lat": 43.6532, "lon": -79.3832},
            "website": "https://www.toronto.ca",
            "planning_dept": "planning@toronto.ca",
            "land_use_bylaw": "https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/zoning-by-law/",
            "zoning_map": "https://www.toronto.ca/city-government/planning-development/zoning-bylaw-online/",
            "contact_info": {
                "phone": "416-338-5858",
                "address": "City Hall, 100 Queen St W, Toronto, ON M5H 2N2"
            }
        },
        "Ottawa": {
            "type": "city",
            "population": 1017449,
            "coordinates": {"lat": 45.4215, "lon": -75.6972},
            "website": "https://ottawa.ca",
            "planning_dept": "planning@ottawa.ca",
            "land_use_bylaw": "https://ottawa.ca/en/living-ottawa/laws-licences-and-permits/laws/zoning-law-no-2008-250",
            "contact_info": {
                "phone": "311",
                "address": "110 Laurier Ave W, Ottawa, ON K1P 1J1"
            }
        },
        "Mississauga": {
            "type": "city",
            "population": 721599,
            "coordinates": {"lat": 43.5890, "lon": -79.6441},
            "website": "https://www.mississauga.ca",
            "planning_dept": "planning@mississauga.ca",
            "land_use_bylaw": "https://www.mississauga.ca/services-and-programs/planning-and-building/zoning/",
            "contact_info": {
                "phone": "905-615-4311",
                "address": "300 City Centre Dr, Mississauga, ON L5B 3C1"
            }
        },
        "Brampton": {
            "type": "city",
            "population": 656480,
            "coordinates": {"lat": 43.7315, "lon": -79.7624},
            "website": "https://www.brampton.ca",
            "planning_dept": "planning@brampton.ca",
            "land_use_bylaw": "https://www.brampton.ca/EN/residents/planning/Pages/ZoningBylaw.aspx",
            "contact_info": {
                "phone": "311",
                "address": "2 Wellington St W, Brampton, ON L6Y 4R2"
            }
        },
        "Hamilton": {
            "type": "city",
            "population": 569353,
            "coordinates": {"lat": 43.2557, "lon": -79.8711},
            "website": "https://www.hamilton.ca",
            "planning_dept": "planning@hamilton.ca",
            "land_use_bylaw": "https://www.hamilton.ca/government-information/laws-and-licensing/zoning-by-law",
            "contact_info": {
                "phone": "905-546-2489",
                "address": "71 Main St W, Hamilton, ON L8P 4Y5"
            }
        },
        "London": {
            "type": "city",
            "population": 422324,
            "coordinates": {"lat": 42.9849, "lon": -81.2453},
            "website": "https://london.ca",
            "planning_dept": "planning@london.ca",
            "land_use_bylaw": "https://london.ca/residents/planning-development/zoning",
            "contact_info": {
                "phone": "519-661-2489",
                "address": "300 Dufferin Ave, London, ON N6B 1Z2"
            }
        },
        "Markham": {
            "type": "city",
            "population": 353120,
            "coordinates": {"lat": 43.8561, "lon": -79.3370},
            "website": "https://www.markham.ca",
            "planning_dept": "planning@markham.ca",
            "land_use_bylaw": "https://www.markham.ca/wps/portal/Home/Property/ZoningBylaw/ZoningBylaw",
            "contact_info": {
                "phone": "905-477-7000",
                "address": "101 Town Centre Blvd, Markham, ON L3R 9W3"
            }
        },
        "Vaughan": {
            "type": "city",
            "population": 344278,
            "coordinates": {"lat": 43.8361, "lon": -79.4983},
            "website": "https://www.vaughan.ca",
            "planning_dept": "planning@vaughan.ca",
            "land_use_bylaw": "https://www.vaughan.ca/business/planning_and_development/zoning_bylaw",
            "contact_info": {
                "phone": "905-832-2281",
                "address": "2141 Major Mackenzie Dr, Vaughan, ON L6A 1T1"
            }
        },
        "Kitchener": {
            "type": "city",
            "population": 256885,
            "coordinates": {"lat": 43.4516, "lon": -80.4925},
            "website": "https://www.kitchener.ca",
            "planning_dept": "planning@kitchener.ca",
            "land_use_bylaw": "https://www.kitchener.ca/en/city-services/zoning-bylaw.aspx",
            "contact_info": {
                "phone": "519-741-2345",
                "address": "200 King St W, Kitchener, ON N2G 4G7"
            }
        },
        "Windsor": {
            "type": "city",
            "population": 229660,
            "coordinates": {"lat": 42.3149, "lon": -83.0364},
            "website": "https://www.citywindsor.ca",
            "planning_dept": "planning@citywindsor.ca",
            "land_use_bylaw": "https://www.citywindsor.ca/residents/planning/Pages/Zoning-By-law.aspx",
            "contact_info": {
                "phone": "519-255-6267",
                "address": "350 City Hall Square W, Windsor, ON N9A 6S1"
            }
        },
        "Richmond Hill": {
            "type": "town",
            "population": 209668,
            "coordinates": {"lat": 43.8828, "lon": -79.4403},
            "website": "https://www.richmondhill.ca",
            "planning_dept": "planning@richmondhill.ca",
            "land_use_bylaw": "https://www.richmondhill.ca/en/find-city-services/planning-and-development.aspx",
            "contact_info": {
                "phone": "905-771-8949",
                "address": "225 East Beaver Creek Rd, Richmond Hill, ON L4B 3P4"
            }
        },
        "Oakville": {
            "type": "town",
            "population": 213759,
            "coordinates": {"lat": 43.4675, "lon": -79.6877},
            "website": "https://www.oakville.ca",
            "planning_dept": "planning@oakville.ca",
            "land_use_bylaw": "https://www.oakville.ca/townhall/planning-zoning.html",
            "contact_info": {
                "phone": "905-845-6601",
                "address": "1225 Trafalgar Rd, Oakville, ON L6H 0H3"
            }
        },
        "Burlington": {
            "type": "city",
            "population": 206366,
            "coordinates": {"lat": 43.3255, "lon": -79.7990},
            "website": "https://www.burlington.ca",
            "planning_dept": "planning@burlington.ca",
            "land_use_bylaw": "https://www.burlington.ca/en/services-for-you/zoning-by-law.aspx",
            "contact_info": {
                "phone": "905-335-7600",
                "address": "426 Brant St, Burlington, ON L7R 3Z6"
            }
        },
        "Oshawa": {
            "type": "city",
            "population": 170073,
            "coordinates": {"lat": 43.8971, "lon": -78.8658},
            "website": "https://www.oshawa.ca",
            "planning_dept": "planning@oshawa.ca",
            "land_use_bylaw": "https://www.oshawa.ca/residents/zoning-by-law.asp",
            "contact_info": {
                "phone": "905-436-3311",
                "address": "50 Centre St S, Oshawa, ON L1H 3Z7"
            }
        },
        "Barrie": {
            "type": "city",
            "population": 153356,
            "coordinates": {"lat": 44.3894, "lon": -79.6903},
            "website": "https://www.barrie.ca",
            "planning_dept": "planning@barrie.ca",
            "land_use_bylaw": "https://www.barrie.ca/city-services/planning-development/zoning-bylaw",
            "contact_info": {
                "phone": "705-739-4220",
                "address": "70 Collier St, Barrie, ON L4M 4T5"
            }
        },
        "Guelph": {
            "type": "city",
            "population": 143740,
            "coordinates": {"lat": 43.5448, "lon": -80.2482},
            "website": "https://guelph.ca",
            "planning_dept": "planning@guelph.ca",
            "land_use_bylaw": "https://guelph.ca/plans-property-and-environment/land-use-planning/zoning-bylaw/",
            "contact_info": {
                "phone": "519-837-5616",
                "address": "1 Carden St, Guelph, ON N1H 3A1"
            }
        },
        "St. Catharines": {
            "type": "city",
            "population": 136803,
            "coordinates": {"lat": 43.1594, "lon": -79.2469},
            "website": "https://www.stcatharines.ca",
            "planning_dept": "planning@stcatharines.ca",
            "land_use_bylaw": "https://www.stcatharines.ca/en/city-hall/planning.aspx",
            "contact_info": {
                "phone": "905-688-5600",
                "address": "PO Box 3012, 50 Church St, St. Catharines, ON L2R 7C2"
            }
        },
        "Waterloo": {
            "type": "city",
            "population": 121436,
            "coordinates": {"lat": 43.4668, "lon": -80.5164},
            "website": "https://www.waterloo.ca",
            "planning_dept": "planning@waterloo.ca",
            "land_use_bylaw": "https://www.waterloo.ca/en/government/zoningbylaw.asp",
            "contact_info": {
                "phone": "519-886-1550",
                "address": "100 Regina St S, Waterloo, ON N2J 4P9"
            }
        },
    },

    "QC": {
        "Montreal": {
            "type": "city",
            "population": 1762949,
            "coordinates": {"lat": 45.5017, "lon": -73.5673},
            "website": "https://montreal.ca",
            "planning_dept": "urbanisme@montreal.ca",
            "land_use_bylaw": "https://montreal.ca/en/topics/zoning",
            "zoning_map": "https://montreal.ca/en/topics/zoning",
            "contact_info": {
                "phone": "311",
                "address": "275 Notre-Dame St E, Montreal, QC H2Y 1C6"
            }
        },
        "Quebec City": {
            "type": "city",
            "population": 531902,
            "coordinates": {"lat": 46.8139, "lon": -71.2080},
            "website": "https://www.ville.quebec.qc.ca",
            "planning_dept": "urbanisme@ville.quebec.qc.ca",
            "land_use_bylaw": "https://www.ville.quebec.qc.ca/citoyens/propriete/zonage/index.aspx",
            "contact_info": {
                "phone": "418-641-6411",
                "address": "2, rue des Jardins, Quebec City, QC G1R 4S9"
            }
        },
        "Laval": {
            "type": "city",
            "population": 440747,
            "coordinates": {"lat": 45.5811, "lon": -73.7422},
            "website": "https://www.laval.ca",
            "planning_dept": "urbanisme@laval.ca",
            "land_use_bylaw": "https://www.laval.ca/Pages/Fr/Citoyens/urbanisme.aspx",
            "contact_info": {
                "phone": "311",
                "address": "1 Place du Souvenir, Laval, QC H7V 4B3"
            }
        },
        "Gatineau": {
            "type": "city",
            "population": 291041,
            "coordinates": {"lat": 45.4765, "lon": -75.7013},
            "website": "https://www.gatineau.ca",
            "planning_dept": "urbanisme@gatineau.ca",
            "land_use_bylaw": "https://www.gatineau.ca/portail/default.aspx?p=guichet_municipal/urbanisme_amenagement_territoire",
            "contact_info": {
                "phone": "819-595-2002",
                "address": "25 rue Laurier, Gatineau, QC J8X 4C8"
            }
        },
        "Longueuil": {
            "type": "city",
            "population": 248619,
            "coordinates": {"lat": 45.5312, "lon": -73.5185},
            "website": "https://www.longueuil.quebec",
            "planning_dept": "urbanisme@longueuil.quebec",
            "land_use_bylaw": "https://www.longueuil.quebec/fr/service/planification-et-zonage",
            "contact_info": {
                "phone": "311",
                "address": "4250 chemin de la Savane, Longueuil, QC J3Y 9G4"
            }
        },
        "Sherbrooke": {
            "type": "city",
            "population": 172950,
            "coordinates": {"lat": 45.4042, "lon": -71.8929},
            "website": "https://www.sherbrooke.ca",
            "planning_dept": "urbanisme@sherbrooke.ca",
            "land_use_bylaw": "https://www.sherbrooke.ca/fr/services/amenagement-du-territoire",
            "contact_info": {
                "phone": "819-821-5555",
                "address": "919 rue Bowen S, Sherbrooke, QC J1H 5C6"
            }
        },
        "Saguenay": {
            "type": "city",
            "population": 148056,
            "coordinates": {"lat": 48.4279, "lon": -71.0661},
            "website": "https://www.ville.saguenay.ca",
            "planning_dept": "urbanisme@ville.saguenay.ca",
            "land_use_bylaw": "https://www.ville.saguenay.ca/citoyens/urbanisme/zonage",
            "contact_info": {
                "phone": "418-698-3000",
                "address": "201 rue Racine E, Chicoutimi, QC G7H 1R6"
            }
        },
        "Levis": {
            "type": "city",
            "population": 148249,
            "coordinates": {"lat": 46.8036, "lon": -71.1836},
            "website": "https://www.ville.levis.qc.ca",
            "planning_dept": "urbanisme@ville.levis.qc.ca",
            "land_use_bylaw": "https://www.ville.levis.qc.ca/en/life/construction-and-renovation/zoning/",
            "contact_info": {
                "phone": "418-839-2002",
                "address": "2175 chemin du Fleuve, Saint-Romuald, QC G6W 7W9"
            }
        },
        "Trois-Rivieres": {
            "type": "city",
            "population": 139163,
            "coordinates": {"lat": 46.3499, "lon": -72.5476},
            "website": "https://www.v3r.net",
            "planning_dept": "urbanisme@v3r.net",
            "land_use_bylaw": "https://www.v3r.net/citoyens/amenagement-du-territoire/urbanisme",
            "contact_info": {
                "phone": "819-372-4636",
                "address": "1325 Place de l'Hôtel-de-Ville, Trois-Rivières, QC G9A 5J4"
            }
        },
        "Terrebonne": {
            "type": "city",
            "population": 118263,
            "coordinates": {"lat": 45.7025, "lon": -73.6375},
            "website": "https://www.ville.terrebonne.qc.ca",
            "planning_dept": "urbanisme@ville.terrebonne.qc.ca",
            "land_use_bylaw": "https://www.ville.terrebonne.qc.ca/citoyens/amenagement-du-territoire",
            "contact_info": {
                "phone": "450-961-2001",
                "address": "775 rue Saint-Jean-Baptiste, Terrebonne, QC J6W 1B5"
            }
        },
        "Brossard": {
            "type": "city",
            "population": 90669,
            "coordinates": {"lat": 45.4603, "lon": -73.4627},
            "website": "https://www.brossard.ca",
            "planning_dept": "urbanisme@brossard.ca",
            "land_use_bylaw": "https://www.brossard.ca/fr/services/urbanisme-et-amenagement",
            "contact_info": {
                "phone": "450-923-6311",
                "address": "2001 boul. de Rome, Brossard, QC J4W 3K5"
            }
        },
    },

    "NB": {
        "Moncton": {
            "type": "city",
            "population": 79470,
            "coordinates": {"lat": 46.0878, "lon": -64.7782},
            "website": "https://www.moncton.ca",
            "planning_dept": "planning@moncton.ca",
            "land_use_bylaw": "https://www.moncton.ca/Government/Planning/Zoning.aspx",
            "contact_info": {
                "phone": "506-853-3333",
                "address": "655 Main St, Moncton, NB E1C 1E8"
            }
        },
        "Saint John": {
            "type": "city",
            "population": 67575,
            "coordinates": {"lat": 45.2733, "lon": -66.0633},
            "website": "https://www.saintjohn.ca",
            "planning_dept": "planning@saintjohn.ca",
            "land_use_bylaw": "https://www.saintjohn.ca/en/living-here/planning/zoning",
            "contact_info": {
                "phone": "506-658-2862",
                "address": "P.O. Box 1971, 15 Market Square, Saint John, NB E2L 4L1"
            }
        },
        "Fredericton": {
            "type": "city",
            "population": 63116,
            "coordinates": {"lat": 45.9636, "lon": -66.6431},
            "website": "https://www.fredericton.ca",
            "planning_dept": "planning@fredericton.ca",
            "land_use_bylaw": "https://www.fredericton.ca/en/city-hall/planning-and-development/zoning",
            "contact_info": {
                "phone": "506-460-2041",
                "address": "397 Queen St, Fredericton, NB E3B 1B5"
            }
        },
        "Miramichi": {
            "type": "city",
            "population": 17537,
            "coordinates": {"lat": 47.0236, "lon": -65.5005},
            "website": "https://www.miramichi.org",
            "planning_dept": "planning@miramichi.org",
            "land_use_bylaw": "https://www.miramichi.org/planning",
            "contact_info": {
                "phone": "506-623-2100",
                "address": "141 Henry St, Miramichi, NB E1V 2N5"
            }
        },
        "Bathurst": {
            "type": "city",
            "population": 11897,
            "coordinates": {"lat": 47.6184, "lon": -65.6514},
            "website": "https://www.bathurst.ca",
            "planning_dept": "planning@bathurst.ca",
            "land_use_bylaw": "https://www.bathurst.ca/planning",
            "contact_info": {
                "phone": "506-548-0400",
                "address": "150 St. George St, Bathurst, NB E2A 1A7"
            }
        },
    },

    "NS": {
        "Halifax": {
            "type": "regional municipality",
            "population": 403390,
            "coordinates": {"lat": 44.6488, "lon": -63.5752},
            "website": "https://www.halifax.ca",
            "planning_dept": "planning@halifax.ca",
            "land_use_bylaw": "https://www.halifax.ca/business/planning-development/land-use-bylaws",
            "zoning_map": "https://maps.halifax.ca/",
            "contact_info": {
                "phone": "311",
                "address": "P.O. Box 1749, Halifax, NS B3J 3A5"
            }
        },
        "Cape Breton": {
            "type": "regional municipality",
            "population": 94285,
            "coordinates": {"lat": 46.1351, "lon": -60.1831},
            "website": "https://www.cbrm.ns.ca",
            "planning_dept": "planning@cbrm.ns.ca",
            "land_use_bylaw": "https://www.cbrm.ns.ca/planning.html",
            "contact_info": {
                "phone": "902-563-5010",
                "address": "320 Esplanade, Sydney, NS B1P 7B9"
            }
        },
        "Truro": {
            "type": "town",
            "population": 12954,
            "coordinates": {"lat": 45.3647, "lon": -63.2802},
            "website": "https://www.truro.ca",
            "planning_dept": "planning@truro.ca",
            "land_use_bylaw": "https://www.truro.ca/planning",
            "contact_info": {
                "phone": "902-893-6078",
                "address": "695 Prince St, Truro, NS B2N 1G5"
            }
        },
        "New Glasgow": {
            "type": "town",
            "population": 9562,
            "coordinates": {"lat": 45.5879, "lon": -62.6459},
            "website": "https://www.newglasgow.ca",
            "planning_dept": "planning@newglasgow.ca",
            "land_use_bylaw": "https://www.newglasgow.ca/planning",
            "contact_info": {
                "phone": "902-755-8100",
                "address": "111 Provost St, New Glasgow, NS B2H 2P6"
            }
        },
        "Kentville": {
            "type": "town",
            "population": 6354,
            "coordinates": {"lat": 45.0737, "lon": -64.4954},
            "website": "https://www.kentville.ca",
            "planning_dept": "planning@kentville.ca",
            "land_use_bylaw": "https://www.kentville.ca/planning",
            "contact_info": {
                "phone": "902-679-2500",
                "address": "354 Main St, Kentville, NS B4N 1K6"
            }
        },
    },

    "PE": {
        "Charlottetown": {
            "type": "city",
            "population": 38809,
            "coordinates": {"lat": 46.2382, "lon": -63.1311},
            "website": "https://www.charlottetown.ca",
            "planning_dept": "planning@charlottetown.ca",
            "land_use_bylaw": "https://www.charlottetown.ca/municipal-government/bylaws/zoning-and-development-bylaw",
            "contact_info": {
                "phone": "902-629-4013",
                "address": "199 Queen St, Charlottetown, PEI C1A 7K4"
            }
        },
        "Summerside": {
            "type": "city",
            "population": 16384,
            "coordinates": {"lat": 46.3943, "lon": -63.7883},
            "website": "https://www.summerside.ca",
            "planning_dept": "planning@summerside.ca",
            "land_use_bylaw": "https://www.summerside.ca/planning",
            "contact_info": {
                "phone": "902-432-1230",
                "address": "275 Fitzroy St, Summerside, PEI C1N 1H9"
            }
        },
        "Stratford": {
            "type": "town",
            "population": 10719,
            "coordinates": {"lat": 46.2237, "lon": -63.0748},
            "website": "https://www.townofstratford.ca",
            "planning_dept": "planning@townofstratford.ca",
            "land_use_bylaw": "https://www.townofstratford.ca/planning",
            "contact_info": {
                "phone": "902-569-1995",
                "address": "234 Shakespeare Dr, Stratford, PEI C1B 2V6"
            }
        },
    },

    "NL": {
        "St. John's": {
            "type": "city",
            "population": 110525,
            "coordinates": {"lat": 47.5615, "lon": -52.7126},
            "website": "https://www.stjohns.ca",
            "planning_dept": "planning@stjohns.ca",
            "land_use_bylaw": "https://www.stjohns.ca/living-st-johns/building-development/planning",
            "contact_info": {
                "phone": "709-754-2489",
                "address": "New City Hall, 10 New Gower St, St. John's, NL A1C 5M2"
            }
        },
        "Mount Pearl": {
            "type": "city",
            "population": 22957,
            "coordinates": {"lat": 47.5200, "lon": -52.8058},
            "website": "https://www.mountpearl.ca",
            "planning_dept": "planning@mountpearl.ca",
            "land_use_bylaw": "https://www.mountpearl.ca/planning-development",
            "contact_info": {
                "phone": "709-748-1000",
                "address": "3 Centennial St, Mount Pearl, NL A1N 1G4"
            }
        },
        "Corner Brook": {
            "type": "city",
            "population": 19806,
            "coordinates": {"lat": 48.9520, "lon": -57.9522},
            "website": "https://www.cornerbrook.com",
            "planning_dept": "planning@cornerbrook.com",
            "land_use_bylaw": "https://www.cornerbrook.com/planning",
            "contact_info": {
                "phone": "709-637-1500",
                "address": "5 Park St, Corner Brook, NL A2H 2X2"
            }
        },
        "Grand Falls-Windsor": {
            "type": "town",
            "population": 13725,
            "coordinates": {"lat": 48.9312, "lon": -55.6686},
            "website": "https://www.grandfallswindsor.com",
            "planning_dept": "planning@grandfallswindsor.com",
            "land_use_bylaw": "https://www.grandfallswindsor.com/planning",
            "contact_info": {
                "phone": "709-489-0471",
                "address": "4 High St, Grand Falls-Windsor, NL A2A 2K4"
            }
        },
    },

    "YT": {
        "Whitehorse": {
            "type": "city",
            "population": 28201,
            "coordinates": {"lat": 60.7212, "lon": -135.0568},
            "website": "https://www.whitehorse.ca",
            "planning_dept": "planning@whitehorse.ca",
            "land_use_bylaw": "https://www.whitehorse.ca/government/administration/planning-development",
            "contact_info": {
                "phone": "867-668-8337",
                "address": "2121 Second Ave, Whitehorse, YT Y1A 1C2"
            }
        },
        "Dawson City": {
            "type": "town",
            "population": 1375,
            "coordinates": {"lat": 64.0601, "lon": -139.4322},
            "website": "https://www.dawsoncity.ca",
            "planning_dept": "planning@dawsoncity.ca",
            "land_use_bylaw": "https://www.dawsoncity.ca/planning",
            "contact_info": {
                "phone": "867-993-7400",
                "address": "PO Box 308, Dawson City, YT Y0B 1G0"
            }
        },
    },

    "NT": {
        "Yellowknife": {
            "type": "city",
            "population": 20340,
            "coordinates": {"lat": 62.4540, "lon": -114.3718},
            "website": "https://www.yellowknife.ca",
            "planning_dept": "planning@yellowknife.ca",
            "land_use_bylaw": "https://www.yellowknife.ca/en/doing-business/land-development.aspx",
            "contact_info": {
                "phone": "867-920-5600",
                "address": "4807 52 St, Yellowknife, NT X1A 2N4"
            }
        },
        "Hay River": {
            "type": "town",
            "population": 3606,
            "coordinates": {"lat": 60.8169, "lon": -115.7997},
            "website": "https://www.hayriver.com",
            "planning_dept": "planning@hayriver.com",
            "land_use_bylaw": "https://www.hayriver.com/planning",
            "contact_info": {
                "phone": "867-874-6522",
                "address": "73 Woodland Drive, Hay River, NT X0E 1G1"
            }
        },
    },

    "NU": {
        "Iqaluit": {
            "type": "city",
            "population": 7740,
            "coordinates": {"lat": 63.7467, "lon": -68.5170},
            "website": "https://www.city.iqaluit.nu.ca",
            "planning_dept": "planning@city.iqaluit.nu.ca",
            "land_use_bylaw": "https://www.city.iqaluit.nu.ca/en/our-government/bylaws/land-use-bylaw",
            "contact_info": {
                "phone": "867-979-5600",
                "address": "PO Box 460, Iqaluit, NU X0A 0H0"
            }
        },
        "Rankin Inlet": {
            "type": "hamlet",
            "population": 2842,
            "coordinates": {"lat": 62.8081, "lon": -92.0853},
            "website": "https://www.rankininlet.ca",
            "planning_dept": "planning@rankininlet.ca",
            "land_use_bylaw": "https://www.rankininlet.ca/planning",
            "contact_info": {
                "phone": "867-645-5068",
                "address": "PO Box 310, Rankin Inlet, NU X0C 0G0"
            }
        },
    },
}


def get_all_municipalities_flat():
    """Return a flat list of all municipalities with province info attached."""
    result = []
    for province_code, cities in CANADIAN_MUNICIPALITIES.items():
        province = PROVINCE_INFO.get(province_code, {})
        for city_name, city_data in cities.items():
            entry = city_data.copy()
            entry["name"] = city_name
            entry["province"] = province_code
            entry["province_name"] = province.get("name", province_code)
            result.append(entry)
    return result


def get_municipalities_by_province(province_code: str):
    """Return list of municipalities for a given province code."""
    cities = CANADIAN_MUNICIPALITIES.get(province_code.upper(), {})
    province = PROVINCE_INFO.get(province_code.upper(), {})
    result = []
    for city_name, city_data in cities.items():
        entry = city_data.copy()
        entry["name"] = city_name
        entry["province"] = province_code.upper()
        entry["province_name"] = province.get("name", province_code)
        result.append(entry)
    return sorted(result, key=lambda x: x["name"])
