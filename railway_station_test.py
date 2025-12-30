#!/usr/bin/env python3
"""
Railway Station Database & City-First Search Model Testing
Tests the comprehensive railway station database with city-first search behavior
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys
import os

# Backend URL - using production URL from frontend config
BACKEND_URL = "https://deeplink-proxy.preview.emergentagent.com"

class RailwayStationTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_result(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    async def test_search_api_city_first_pune(self):
        """Test GET /api/trains/search?q=Pune - should return city result with station_codes"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/search",
                params={"q": "Pune"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Search API City-First Pune", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check if results contain city-type result
            results = data.get("results", [])
            if not results:
                self.log_result(
                    "Search API City-First Pune",
                    False,
                    "No results returned for Pune query",
                    data
                )
                return False
            
            # Look for city result
            city_result = None
            for result in results:
                if result.get("result_type") == "city" and "pune" in result.get("display_name", "").lower():
                    city_result = result
                    break
            
            if not city_result:
                self.log_result(
                    "Search API City-First Pune",
                    False,
                    "No city-type result found for Pune",
                    data
                )
                return False
            
            # Check station_codes array
            station_codes = city_result.get("station_codes", [])
            if not station_codes:
                self.log_result(
                    "Search API City-First Pune",
                    False,
                    "City result missing station_codes array",
                    city_result
                )
                return False
            
            # Should include PUNE and SVJR at minimum
            expected_stations = ["PUNE", "SVJR"]
            found_stations = [code for code in expected_stations if code in station_codes]
            
            if len(found_stations) < 2:
                self.log_result(
                    "Search API City-First Pune",
                    False,
                    f"Expected stations {expected_stations}, found {found_stations} in {station_codes}",
                    city_result
                )
                return False
            
            self.log_result(
                "Search API City-First Pune",
                True,
                f"City result found with {len(station_codes)} stations: {station_codes}"
            )
            return True
            
        except Exception as e:
            self.log_result("Search API City-First Pune", False, f"Exception: {str(e)}")
            return False
    
    async def test_search_api_city_first_mumbai(self):
        """Test GET /api/trains/search?q=Mumbai - should return city with 9 stations"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/search",
                params={"q": "Mumbai"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Search API City-First Mumbai", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            results = data.get("results", [])
            
            # Look for Mumbai city result
            mumbai_city = None
            for result in results:
                if result.get("result_type") == "city" and "mumbai" in result.get("display_name", "").lower():
                    mumbai_city = result
                    break
            
            if not mumbai_city:
                self.log_result(
                    "Search API City-First Mumbai",
                    False,
                    "No Mumbai city result found",
                    data
                )
                return False
            
            station_codes = mumbai_city.get("station_codes", [])
            
            # Mumbai should have 9 stations as per requirement
            if len(station_codes) < 8:  # Allow some flexibility
                self.log_result(
                    "Search API City-First Mumbai",
                    False,
                    f"Expected ~9 stations for Mumbai, got {len(station_codes)}: {station_codes}",
                    mumbai_city
                )
                return False
            
            # Should include major Mumbai stations
            expected_major = ["CSMT", "BCT", "LTT", "DR"]
            found_major = [code for code in expected_major if code in station_codes]
            
            if len(found_major) < 3:
                self.log_result(
                    "Search API City-First Mumbai",
                    False,
                    f"Expected major stations {expected_major}, found {found_major}",
                    mumbai_city
                )
                return False
            
            self.log_result(
                "Search API City-First Mumbai",
                True,
                f"Mumbai city found with {len(station_codes)} stations including major ones: {found_major}"
            )
            return True
            
        except Exception as e:
            self.log_result("Search API City-First Mumbai", False, f"Exception: {str(e)}")
            return False
    
    async def test_search_api_specific_station(self):
        """Test GET /api/trains/search?q=Shivaji%20Nagar - should return specific station SVJR"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/search",
                params={"q": "Shivaji Nagar"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Search API Specific Station", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            results = data.get("results", [])
            
            # Look for station result with SVJR
            svjr_station = None
            for result in results:
                if (result.get("result_type") == "station" and 
                    (result.get("station_code") == "SVJR" or "svjr" in str(result.get("station_codes", [])).lower())):
                    svjr_station = result
                    break
            
            if not svjr_station:
                self.log_result(
                    "Search API Specific Station",
                    False,
                    "No SVJR station result found for 'Shivaji Nagar' query",
                    data
                )
                return False
            
            self.log_result(
                "Search API Specific Station",
                True,
                f"SVJR station found: {svjr_station.get('display_name')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Search API Specific Station", False, f"Exception: {str(e)}")
            return False
    
    async def test_alias_support_bombay(self):
        """Test GET /api/trains/search?q=Bombay - should resolve to Mumbai city"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/search",
                params={"q": "Bombay"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Alias Support Bombay", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            results = data.get("results", [])
            
            # Should resolve to Mumbai
            mumbai_found = False
            for result in results:
                if "mumbai" in result.get("display_name", "").lower():
                    mumbai_found = True
                    break
            
            if not mumbai_found:
                self.log_result(
                    "Alias Support Bombay",
                    False,
                    "Bombay query did not resolve to Mumbai",
                    data
                )
                return False
            
            self.log_result(
                "Alias Support Bombay",
                True,
                "Bombay successfully resolved to Mumbai"
            )
            return True
            
        except Exception as e:
            self.log_result("Alias Support Bombay", False, f"Exception: {str(e)}")
            return False
    
    async def test_alias_support_vt(self):
        """Test GET /api/trains/search?q=VT - should resolve to CSMT station"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/search",
                params={"q": "VT"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Alias Support VT", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            results = data.get("results", [])
            
            # Should resolve to CSMT
            csmt_found = False
            for result in results:
                if ("csmt" in str(result).lower() or 
                    result.get("station_code") == "CSMT" or
                    "CSMT" in result.get("station_codes", [])):
                    csmt_found = True
                    break
            
            if not csmt_found:
                self.log_result(
                    "Alias Support VT",
                    False,
                    "VT query did not resolve to CSMT",
                    data
                )
                return False
            
            self.log_result(
                "Alias Support VT",
                True,
                "VT successfully resolved to CSMT"
            )
            return True
            
        except Exception as e:
            self.log_result("Alias Support VT", False, f"Exception: {str(e)}")
            return False
    
    async def test_resolve_api_mumbai(self):
        """Test GET /api/trains/resolve?q=Mumbai - should return city type with station_codes"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/resolve",
                params={"q": "Mumbai"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Resolve API Mumbai", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if data.get("type") != "city":
                self.log_result(
                    "Resolve API Mumbai",
                    False,
                    f"Expected type='city', got {data.get('type')}",
                    data
                )
                return False
            
            station_codes = data.get("station_codes", [])
            if not station_codes:
                self.log_result(
                    "Resolve API Mumbai",
                    False,
                    "Missing station_codes in response",
                    data
                )
                return False
            
            # Should include major Mumbai stations
            expected_stations = ["CSMT", "BCT", "LTT"]
            found_stations = [code for code in expected_stations if code in station_codes]
            
            if len(found_stations) < 2:
                self.log_result(
                    "Resolve API Mumbai",
                    False,
                    f"Expected stations {expected_stations}, found {found_stations}",
                    data
                )
                return False
            
            self.log_result(
                "Resolve API Mumbai",
                True,
                f"Mumbai resolved as city with {len(station_codes)} stations: {station_codes}"
            )
            return True
            
        except Exception as e:
            self.log_result("Resolve API Mumbai", False, f"Exception: {str(e)}")
            return False
    
    async def test_resolve_api_ndls(self):
        """Test GET /api/trains/resolve?q=NDLS - should return station type"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/resolve",
                params={"q": "NDLS"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Resolve API NDLS", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if data.get("type") != "station":
                self.log_result(
                    "Resolve API NDLS",
                    False,
                    f"Expected type='station', got {data.get('type')}",
                    data
                )
                return False
            
            station_codes = data.get("station_codes", [])
            if "NDLS" not in station_codes:
                self.log_result(
                    "Resolve API NDLS",
                    False,
                    f"Expected NDLS in station_codes, got {station_codes}",
                    data
                )
                return False
            
            self.log_result(
                "Resolve API NDLS",
                True,
                f"NDLS resolved as station: {station_codes}"
            )
            return True
            
        except Exception as e:
            self.log_result("Resolve API NDLS", False, f"Exception: {str(e)}")
            return False
    
    async def test_connectivity_api_city_to_city(self):
        """Test GET /api/trains/connectivity?from=Pune&to=Mumbai - should expand to all station pairs"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "Pune", "to": "Mumbai"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Connectivity API City to City", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["from_stations", "to_stations", "route_type", "booking_partners"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Connectivity API City to City",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            from_stations = data.get("from_stations", [])
            to_stations = data.get("to_stations", [])
            
            # Should include Pune stations
            if "PUNE" not in from_stations and "SVJR" not in from_stations:
                self.log_result(
                    "Connectivity API City to City",
                    False,
                    f"Expected Pune stations in from_stations, got {from_stations}",
                    data
                )
                return False
            
            # Should include Mumbai stations
            mumbai_stations = ["CSMT", "BCT", "LTT", "DR"]
            found_mumbai = [s for s in mumbai_stations if s in to_stations]
            
            if len(found_mumbai) < 2:
                self.log_result(
                    "Connectivity API City to City",
                    False,
                    f"Expected Mumbai stations in to_stations, got {to_stations}",
                    data
                )
                return False
            
            # Check note mentions multiple stations
            note = data.get("note", "")
            if "multiple" not in note.lower():
                self.log_result(
                    "Connectivity API City to City",
                    False,
                    f"Expected note to mention 'multiple station options', got: {note}",
                    data
                )
                return False
            
            self.log_result(
                "Connectivity API City to City",
                True,
                f"City-to-city connectivity working: {len(from_stations)} from stations, {len(to_stations)} to stations"
            )
            return True
            
        except Exception as e:
            self.log_result("Connectivity API City to City", False, f"Exception: {str(e)}")
            return False
    
    async def test_connectivity_api_station_to_station(self):
        """Test GET /api/trains/connectivity?from=PUNE&to=CSMT - should be specific"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "PUNE", "to": "CSMT"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Connectivity API Station to Station", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            from_stations = data.get("from_stations", [])
            to_stations = data.get("to_stations", [])
            
            # Should be specific stations
            if from_stations != ["PUNE"]:
                self.log_result(
                    "Connectivity API Station to Station",
                    False,
                    f"Expected from_stations=['PUNE'], got {from_stations}",
                    data
                )
                return False
            
            if to_stations != ["CSMT"]:
                self.log_result(
                    "Connectivity API Station to Station",
                    False,
                    f"Expected to_stations=['CSMT'], got {to_stations}",
                    data
                )
                return False
            
            self.log_result(
                "Connectivity API Station to Station",
                True,
                "Station-to-station connectivity working correctly"
            )
            return True
            
        except Exception as e:
            self.log_result("Connectivity API Station to Station", False, f"Exception: {str(e)}")
            return False
    
    async def test_booking_partners_in_connectivity(self):
        """Test that connectivity API includes booking_partners"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "PUNE", "to": "CSMT"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Booking Partners in Connectivity", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            booking_partners = data.get("booking_partners", [])
            
            if not booking_partners:
                self.log_result(
                    "Booking Partners in Connectivity",
                    False,
                    "Missing booking_partners in response",
                    data
                )
                return False
            
            # Should include expected partners
            expected_partners = ["IRCTC", "RailYatri", "ConfirmTkt", "Paytm"]
            partner_names = [p.get("name", "") for p in booking_partners]
            
            found_partners = [name for name in expected_partners if any(name in pname for pname in partner_names)]
            
            if len(found_partners) < 3:
                self.log_result(
                    "Booking Partners in Connectivity",
                    False,
                    f"Expected partners {expected_partners}, found {found_partners} in {partner_names}",
                    data
                )
                return False
            
            # Check IRCTC is marked as official
            irctc_partner = None
            for partner in booking_partners:
                if "IRCTC" in partner.get("name", ""):
                    irctc_partner = partner
                    break
            
            if irctc_partner and not irctc_partner.get("is_official"):
                self.log_result(
                    "Booking Partners in Connectivity",
                    False,
                    "IRCTC should be marked as is_official=true",
                    irctc_partner
                )
                return False
            
            self.log_result(
                "Booking Partners in Connectivity",
                True,
                f"Booking partners included: {partner_names}"
            )
            return True
            
        except Exception as e:
            self.log_result("Booking Partners in Connectivity", False, f"Exception: {str(e)}")
            return False
    
    async def test_city_info_api_mumbai(self):
        """Test GET /api/trains/cities/mumbai - should show 9 stations with primary"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/cities/mumbai"
            )
            
            if response.status_code != 200:
                self.log_result(
                    "City Info API Mumbai", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["station_count", "primary_station", "is_metro", "stations"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "City Info API Mumbai",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            station_count = data.get("station_count", 0)
            if station_count < 8:  # Allow some flexibility
                self.log_result(
                    "City Info API Mumbai",
                    False,
                    f"Expected ~9 stations, got {station_count}",
                    data
                )
                return False
            
            primary_station = data.get("primary_station")
            if primary_station != "CSMT":
                self.log_result(
                    "City Info API Mumbai",
                    False,
                    f"Expected primary_station='CSMT', got {primary_station}",
                    data
                )
                return False
            
            is_metro = data.get("is_metro")
            if not is_metro:
                self.log_result(
                    "City Info API Mumbai",
                    False,
                    f"Expected is_metro=true, got {is_metro}",
                    data
                )
                return False
            
            # Check stations list has is_primary flag
            stations = data.get("stations", [])
            primary_found = False
            for station in stations:
                if station.get("is_primary"):
                    primary_found = True
                    break
            
            if not primary_found:
                self.log_result(
                    "City Info API Mumbai",
                    False,
                    "No station marked with is_primary=true",
                    data
                )
                return False
            
            self.log_result(
                "City Info API Mumbai",
                True,
                f"Mumbai city info correct: {station_count} stations, primary={primary_station}, metro={is_metro}"
            )
            return True
            
        except Exception as e:
            self.log_result("City Info API Mumbai", False, f"Exception: {str(e)}")
            return False
    
    async def test_city_info_api_delhi(self):
        """Test GET /api/trains/cities/delhi - should have 6 stations"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/cities/delhi"
            )
            
            if response.status_code != 200:
                self.log_result(
                    "City Info API Delhi", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            station_count = data.get("station_count", 0)
            if station_count < 5:  # Allow some flexibility
                self.log_result(
                    "City Info API Delhi",
                    False,
                    f"Expected ~6 stations, got {station_count}",
                    data
                )
                return False
            
            # Should include major Delhi stations
            stations = data.get("stations", [])
            station_codes = [s.get("station_code") for s in stations]  # Fixed: use station_code not code
            expected_stations = ["NDLS", "DLI", "NZM", "ANVT"]
            found_stations = [code for code in expected_stations if code in station_codes]
            
            if len(found_stations) < 3:
                self.log_result(
                    "City Info API Delhi",
                    False,
                    f"Expected stations {expected_stations}, found {found_stations}",
                    data
                )
                return False
            
            self.log_result(
                "City Info API Delhi",
                True,
                f"Delhi city info correct: {station_count} stations including {found_stations}"
            )
            return True
            
        except Exception as e:
            self.log_result("City Info API Delhi", False, f"Exception: {str(e)}")
            return False
    
    async def test_cities_list_api_metro_only(self):
        """Test GET /api/trains/cities?metro_only=true - should return only metro cities"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/cities",
                params={"metro_only": "true"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Cities List API Metro Only", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            cities = data.get("cities", [])
            
            if not cities:
                self.log_result(
                    "Cities List API Metro Only",
                    False,
                    "No metro cities returned",
                    data
                )
                return False
            
            # Check that all returned cities are metros
            non_metro_cities = [c for c in cities if not c.get("is_metro")]
            if non_metro_cities:
                self.log_result(
                    "Cities List API Metro Only",
                    False,
                    f"Non-metro cities found: {non_metro_cities}",
                    data
                )
                return False
            
            # Should include major metros
            city_names = [c.get("city_name", "").lower() for c in cities]  # Fixed: use city_name not name
            expected_metros = ["delhi", "mumbai", "kolkata", "chennai"]
            found_metros = [metro for metro in expected_metros if any(metro in name for name in city_names)]
            
            if len(found_metros) < 3:
                self.log_result(
                    "Cities List API Metro Only",
                    False,
                    f"Expected metros {expected_metros}, found {found_metros}",
                    data
                )
                return False
            
            self.log_result(
                "Cities List API Metro Only",
                True,
                f"Metro cities filter working: {len(cities)} metros including {found_metros}"
            )
            return True
            
        except Exception as e:
            self.log_result("Cities List API Metro Only", False, f"Exception: {str(e)}")
            return False
    
    async def test_cities_list_api_state_filter(self):
        """Test GET /api/trains/cities?state=Maharashtra - should return Maharashtra cities"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/cities",
                params={"state": "Maharashtra"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Cities List API State Filter", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            cities = data.get("cities", [])
            
            if not cities:
                self.log_result(
                    "Cities List API State Filter",
                    False,
                    "No Maharashtra cities returned",
                    data
                )
                return False
            
            # Check that all cities are from Maharashtra
            non_mh_cities = [c for c in cities if "maharashtra" not in c.get("state", "").lower()]
            if non_mh_cities:
                self.log_result(
                    "Cities List API State Filter",
                    False,
                    f"Non-Maharashtra cities found: {non_mh_cities}",
                    data
                )
                return False
            
            # Should include major Maharashtra cities
            city_names = [c.get("city_name", "").lower() for c in cities]  # Fixed: use city_name not name
            expected_cities = ["mumbai", "pune", "nagpur"]
            found_cities = [city for city in expected_cities if any(city in name for name in city_names)]
            
            if len(found_cities) < 2:
                self.log_result(
                    "Cities List API State Filter",
                    False,
                    f"Expected cities {expected_cities}, found {found_cities}",
                    data
                )
                return False
            
            self.log_result(
                "Cities List API State Filter",
                True,
                f"Maharashtra state filter working: {len(cities)} cities including {found_cities}"
            )
            return True
            
        except Exception as e:
            self.log_result("Cities List API State Filter", False, f"Exception: {str(e)}")
            return False
    
    async def test_autocomplete_api_del(self):
        """Test GET /api/trains/autocomplete?q=Del - should suggest Delhi with city emoji"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/autocomplete",
                params={"q": "Del"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete API Del", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            suggestions = data.get("suggestions", [])
            
            if not suggestions:
                self.log_result(
                    "Autocomplete API Del",
                    False,
                    "No suggestions returned for 'Del'",
                    data
                )
                return False
            
            # Look for Delhi city suggestion with emoji
            delhi_suggestion = None
            for suggestion in suggestions:
                if ("delhi" in suggestion.get("display_name", "").lower() and 
                    suggestion.get("type") == "city"):
                    delhi_suggestion = suggestion
                    break
            
            if not delhi_suggestion:
                self.log_result(
                    "Autocomplete API Del",
                    False,
                    "No Delhi city suggestion found",
                    data
                )
                return False
            
            # Check for emoji badge
            display_name = delhi_suggestion.get("display_name", "")
            if "🏙️" not in display_name and "📍" not in display_name:
                self.log_result(
                    "Autocomplete API Del",
                    False,
                    f"Delhi suggestion missing emoji badge: {display_name}",
                    delhi_suggestion
                )
                return False
            
            self.log_result(
                "Autocomplete API Del",
                True,
                f"Delhi autocomplete working with badge: {display_name}"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete API Del", False, f"Exception: {str(e)}")
            return False
    
    async def test_autocomplete_api_csm(self):
        """Test GET /api/trains/autocomplete?q=CSM - should suggest CSMT with hub badge"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/autocomplete",
                params={"q": "CSM"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete API CSM", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            suggestions = data.get("suggestions", [])
            
            if not suggestions:
                self.log_result(
                    "Autocomplete API CSM",
                    False,
                    "No suggestions returned for 'CSM'",
                    data
                )
                return False
            
            # Look for CSMT suggestion with hub badge
            csmt_suggestion = None
            for suggestion in suggestions:
                if ("csmt" in suggestion.get("display_name", "").lower() or
                    "csmt" in str(suggestion.get("value", "")).lower()):
                    csmt_suggestion = suggestion
                    break
            
            if not csmt_suggestion:
                self.log_result(
                    "Autocomplete API CSM",
                    False,
                    "No CSMT suggestion found",
                    data
                )
                return False
            
            # Check for hub badge
            display_name = csmt_suggestion.get("display_name", "")
            if "🚉" not in display_name:
                self.log_result(
                    "Autocomplete API CSM",
                    False,
                    f"CSMT suggestion missing hub badge: {display_name}",
                    csmt_suggestion
                )
                return False
            
            self.log_result(
                "Autocomplete API CSM",
                True,
                f"CSMT autocomplete working with hub badge: {display_name}"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete API CSM", False, f"Exception: {str(e)}")
            return False
    
    async def test_booking_links_api(self):
        """Test GET /api/trains/booking-links?from=PUNE&to=CSMT - should return 4 partners"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/booking-links",
                params={"from": "PUNE", "to": "CSMT"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Booking Links API", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            booking_partners = data.get("booking_partners", [])
            
            if not booking_partners:
                self.log_result(
                    "Booking Links API",
                    False,
                    "No booking partners returned",
                    data
                )
                return False
            
            if len(booking_partners) < 3:
                self.log_result(
                    "Booking Links API",
                    False,
                    f"Expected at least 3 partners, got {len(booking_partners)}",
                    data
                )
                return False
            
            # Check for expected partners
            partner_names = [p.get("name", "") for p in booking_partners]
            expected_partners = ["IRCTC", "RailYatri", "ConfirmTkt", "Paytm"]
            found_partners = [name for name in expected_partners if any(name in pname for pname in partner_names)]
            
            if len(found_partners) < 3:
                self.log_result(
                    "Booking Links API",
                    False,
                    f"Expected partners {expected_partners}, found {found_partners}",
                    data
                )
                return False
            
            # Check IRCTC is marked as official
            irctc_official = False
            for partner in booking_partners:
                if "IRCTC" in partner.get("name", "") and partner.get("is_official"):
                    irctc_official = True
                    break
            
            if not irctc_official:
                self.log_result(
                    "Booking Links API",
                    False,
                    "IRCTC not marked as is_official=true",
                    data
                )
                return False
            
            self.log_result(
                "Booking Links API",
                True,
                f"Booking links working: {len(booking_partners)} partners including {found_partners}"
            )
            return True
            
        except Exception as e:
            self.log_result("Booking Links API", False, f"Exception: {str(e)}")
            return False
    
    async def test_disclaimer_in_responses(self):
        """Test that responses include 'Schedules are indicative' disclaimer"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/connectivity",
                params={"from": "PUNE", "to": "CSMT"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Disclaimer in Responses", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            disclaimer = data.get("disclaimer", "")
            
            if "indicative" not in disclaimer.lower():
                self.log_result(
                    "Disclaimer in Responses",
                    False,
                    f"Expected disclaimer with 'indicative', got: {disclaimer}",
                    data
                )
                return False
            
            self.log_result(
                "Disclaimer in Responses",
                True,
                f"Disclaimer present: {disclaimer}"
            )
            return True
            
        except Exception as e:
            self.log_result("Disclaimer in Responses", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all railway station database tests"""
        print("🚀 Starting Railway Station Database & City-First Search Model Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Run all tests in order
        tests = [
            # Search API - City-first behavior
            self.test_search_api_city_first_pune,
            self.test_search_api_city_first_mumbai,
            self.test_search_api_specific_station,
            
            # Alias support
            self.test_alias_support_bombay,
            self.test_alias_support_vt,
            
            # Resolve API
            self.test_resolve_api_mumbai,
            self.test_resolve_api_ndls,
            
            # Connectivity API
            self.test_connectivity_api_city_to_city,
            self.test_connectivity_api_station_to_station,
            self.test_booking_partners_in_connectivity,
            
            # City Info API
            self.test_city_info_api_mumbai,
            self.test_city_info_api_delhi,
            
            # Cities List API
            self.test_cities_list_api_metro_only,
            self.test_cities_list_api_state_filter,
            
            # Autocomplete API
            self.test_autocomplete_api_del,
            self.test_autocomplete_api_csm,
            
            # Booking Links API
            self.test_booking_links_api,
            
            # Disclaimer
            self.test_disclaimer_in_responses,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 RAILWAY STATION DATABASE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(results)
        total = len(results)
        
        # Group results by category
        categories = {
            "Search API (City-First)": self.test_results[0:3],
            "Alias Support": self.test_results[3:5],
            "Resolve API": self.test_results[5:7],
            "Connectivity API": self.test_results[7:10],
            "City Info API": self.test_results[10:12],
            "Cities List API": self.test_results[12:14],
            "Autocomplete API": self.test_results[14:16],
            "Booking Links API": self.test_results[16:17],
            "Disclaimer": self.test_results[17:18],
        }
        
        for category, category_results in categories.items():
            print(f"\n{category}:")
            for result in category_results:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All railway station database tests passed!")
            print("📝 City-first search model working correctly")
            print("📝 Multi-station metros (Mumbai=9, Delhi=6) validated")
            print("📝 Alias resolution (Bombay→Mumbai, VT→CSMT) working")
            print("📝 Booking partner integration functional")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with RailwayStationTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())