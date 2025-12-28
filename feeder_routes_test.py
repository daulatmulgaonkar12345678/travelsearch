#!/usr/bin/env python3
"""
Feeder Routes API Testing for Tourist Destinations in Maharashtra
================================================================

Tests the new Feeder Routes feature that provides bus connectivity
to tourist destinations via feeder connections.

Test Coverage:
1. Route Finding API: GET /api/routes/find
2. Tourist Destinations API: GET /api/routes/destinations  
3. Destination Info API: GET /api/routes/destination/{id}
4. Check Tourist API: GET /api/routes/check-tourist
5. Autocomplete Integration: GET /api/autocomplete/bus

Based on review request requirements for Maharashtra tourist destinations.
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys
import os

# Backend URL - using localhost as per system setup
BACKEND_URL = "http://localhost:8001"

class FeederRoutesTester:
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
    
    async def test_pune_to_mahabaleshwar(self):
        """Test 1: Pune → Mahabaleshwar (hill station)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/find",
                params={"from_city": "pune", "to_city": "mahabaleshwar"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Pune → Mahabaleshwar Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["connected", "route_type", "from_city", "to_city", "segments", "note"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Pune → Mahabaleshwar Route",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Validate expected values
            if not data.get("connected"):
                self.log_result(
                    "Pune → Mahabaleshwar Route",
                    False,
                    f"Expected connected=true, got {data.get('connected')}",
                    data
                )
                return False
            
            route_type = data.get("route_type")
            if route_type not in ["FEEDER", "HIGHWAY_PLUS_FEEDER", "DIRECT_FEEDER"]:
                self.log_result(
                    "Pune → Mahabaleshwar Route",
                    False,
                    f"Expected route_type FEEDER/HIGHWAY_PLUS_FEEDER/DIRECT_FEEDER, got {route_type}",
                    data
                )
                return False
            
            # Check destination info
            dest_info = data.get("destination_info")
            if not dest_info:
                self.log_result(
                    "Pune → Mahabaleshwar Route",
                    False,
                    "Missing destination_info for tourist destination",
                    data
                )
                return False
            
            if dest_info.get("type") != "HILL_STATION":
                self.log_result(
                    "Pune → Mahabaleshwar Route",
                    False,
                    f"Expected destination type HILL_STATION, got {dest_info.get('type')}",
                    data
                )
                return False
            
            # Check segments structure
            segments = data.get("segments", [])
            if not segments:
                self.log_result(
                    "Pune → Mahabaleshwar Route",
                    False,
                    "No route segments found",
                    data
                )
                return False
            
            # Should have distance and time estimates
            if not data.get("total_distance_km") and not data.get("estimated_time_hrs"):
                self.log_result(
                    "Pune → Mahabaleshwar Route",
                    False,
                    "Missing distance_km and estimated_time_hrs",
                    data
                )
                return False
            
            self.log_result(
                "Pune → Mahabaleshwar Route",
                True,
                f"✅ Connected via {route_type}, destination type: {dest_info.get('type')}, segments: {len(segments)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Pune → Mahabaleshwar Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_mumbai_to_ganpatipule(self):
        """Test 2: Mumbai → Ganpatipule (coastal temple)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/find",
                params={"from_city": "mumbai", "to_city": "ganpatipule"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Mumbai → Ganpatipule Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check connectivity
            if not data.get("connected"):
                self.log_result(
                    "Mumbai → Ganpatipule Route",
                    False,
                    f"Expected connected=true, got {data.get('connected')}",
                    data
                )
                return False
            
            # Check destination type
            dest_info = data.get("destination_info")
            if not dest_info or dest_info.get("type") != "RELIGIOUS":
                self.log_result(
                    "Mumbai → Ganpatipule Route",
                    False,
                    f"Expected destination type RELIGIOUS, got {dest_info.get('type') if dest_info else None}",
                    data
                )
                return False
            
            # Check for highway + feeder segments
            segments = data.get("segments", [])
            segment_types = [seg.get("type") for seg in segments]
            
            # Should have HIGHWAY and FEEDER segments for Mumbai → Ratnagiri → Ganpatipule
            if "HIGHWAY" not in segment_types or "FEEDER" not in segment_types:
                self.log_result(
                    "Mumbai → Ganpatipule Route",
                    False,
                    f"Expected HIGHWAY + FEEDER segments, got types: {segment_types}",
                    data
                )
                return False
            
            self.log_result(
                "Mumbai → Ganpatipule Route",
                True,
                f"✅ Connected via {data.get('route_type')}, segments: {segment_types}, destination: RELIGIOUS"
            )
            return True
            
        except Exception as e:
            self.log_result("Mumbai → Ganpatipule Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_aurangabad_to_ajanta(self):
        """Test 3: Aurangabad → Ajanta (UNESCO site)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/find",
                params={"from_city": "aurangabad", "to_city": "ajanta"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Aurangabad → Ajanta Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check connectivity
            if not data.get("connected"):
                self.log_result(
                    "Aurangabad → Ajanta Route",
                    False,
                    f"Expected connected=true, got {data.get('connected')}",
                    data
                )
                return False
            
            # Should be DIRECT_FEEDER (direct tourist buses)
            route_type = data.get("route_type")
            if route_type != "DIRECT_FEEDER":
                self.log_result(
                    "Aurangabad → Ajanta Route",
                    False,
                    f"Expected route_type DIRECT_FEEDER, got {route_type}",
                    data
                )
                return False
            
            # Check destination type
            dest_info = data.get("destination_info")
            if not dest_info or dest_info.get("type") != "HERITAGE":
                self.log_result(
                    "Aurangabad → Ajanta Route",
                    False,
                    f"Expected destination type HERITAGE, got {dest_info.get('type') if dest_info else None}",
                    data
                )
                return False
            
            # Check frequency (should be HIGH for direct tourist buses)
            frequency = data.get("frequency")
            if frequency != "Frequent":  # HIGH maps to "Frequent"
                self.log_result(
                    "Aurangabad → Ajanta Route",
                    False,
                    f"Expected frequency 'Frequent' (HIGH), got {frequency}",
                    data
                )
                return False
            
            self.log_result(
                "Aurangabad → Ajanta Route",
                True,
                f"✅ Connected via DIRECT_FEEDER, destination: HERITAGE, frequency: {frequency}"
            )
            return True
            
        except Exception as e:
            self.log_result("Aurangabad → Ajanta Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_nashik_to_trimbakeshwar(self):
        """Test 4: Nashik → Trimbakeshwar (religious)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/find",
                params={"from_city": "nashik", "to_city": "trimbakeshwar"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Nashik → Trimbakeshwar Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check connectivity
            if not data.get("connected"):
                self.log_result(
                    "Nashik → Trimbakeshwar Route",
                    False,
                    f"Expected connected=true, got {data.get('connected')}",
                    data
                )
                return False
            
            # Should be DIRECT_FEEDER
            route_type = data.get("route_type")
            if route_type != "DIRECT_FEEDER":
                self.log_result(
                    "Nashik → Trimbakeshwar Route",
                    False,
                    f"Expected route_type DIRECT_FEEDER, got {route_type}",
                    data
                )
                return False
            
            # Check destination type
            dest_info = data.get("destination_info")
            if not dest_info or dest_info.get("type") != "RELIGIOUS":
                self.log_result(
                    "Nashik → Trimbakeshwar Route",
                    False,
                    f"Expected destination type RELIGIOUS, got {dest_info.get('type') if dest_info else None}",
                    data
                )
                return False
            
            self.log_result(
                "Nashik → Trimbakeshwar Route",
                True,
                f"✅ Connected via DIRECT_FEEDER, destination: RELIGIOUS"
            )
            return True
            
        except Exception as e:
            self.log_result("Nashik → Trimbakeshwar Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_regular_city_to_city(self):
        """Test 5: Regular city-to-city (highway route) - Pune → Kolhapur"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/find",
                params={"from_city": "pune", "to_city": "kolhapur"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Pune → Kolhapur Highway Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check connectivity
            if not data.get("connected"):
                self.log_result(
                    "Pune → Kolhapur Highway Route",
                    False,
                    f"Expected connected=true, got {data.get('connected')}",
                    data
                )
                return False
            
            # Should be HIGHWAY_DIRECT
            route_type = data.get("route_type")
            if route_type != "HIGHWAY_DIRECT":
                self.log_result(
                    "Pune → Kolhapur Highway Route",
                    False,
                    f"Expected route_type HIGHWAY_DIRECT, got {route_type}",
                    data
                )
                return False
            
            # Should NOT have destination_info (not a tourist destination)
            dest_info = data.get("destination_info")
            if dest_info is not None:
                self.log_result(
                    "Pune → Kolhapur Highway Route",
                    False,
                    f"Expected no destination_info for regular city route, got {dest_info}",
                    data
                )
                return False
            
            self.log_result(
                "Pune → Kolhapur Highway Route",
                True,
                f"✅ Connected via HIGHWAY_DIRECT, no destination_info (regular city route)"
            )
            return True
            
        except Exception as e:
            self.log_result("Pune → Kolhapur Highway Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_remote_village_no_connectivity(self):
        """Test 6: Remote village (no connectivity)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/find",
                params={"from_city": "pune", "to_city": "someinvalidvillage"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Remote Village No Connectivity", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should be not connected
            if data.get("connected") != False:
                self.log_result(
                    "Remote Village No Connectivity",
                    False,
                    f"Expected connected=false, got {data.get('connected')}",
                    data
                )
                return False
            
            # Should be NO_ROUTE
            route_type = data.get("route_type")
            if route_type != "NO_ROUTE":
                self.log_result(
                    "Remote Village No Connectivity",
                    False,
                    f"Expected route_type NO_ROUTE, got {route_type}",
                    data
                )
                return False
            
            self.log_result(
                "Remote Village No Connectivity",
                True,
                f"✅ Correctly returns connected=false, route_type=NO_ROUTE"
            )
            return True
            
        except Exception as e:
            self.log_result("Remote Village No Connectivity", False, f"Exception: {str(e)}")
            return False
    
    async def test_list_all_destinations(self):
        """Test 7: List all destinations"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/destinations"
            )
            
            if response.status_code != 200:
                self.log_result(
                    "List All Destinations", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            required_fields = ["destinations", "total"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "List All Destinations",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            destinations = data.get("destinations", [])
            total = data.get("total", 0)
            
            # Should return 20 total destinations (as per review request)
            if total != 20:
                self.log_result(
                    "List All Destinations",
                    False,
                    f"Expected 20 total destinations, got {total}",
                    data
                )
                return False
            
            if len(destinations) != total:
                self.log_result(
                    "List All Destinations",
                    False,
                    f"Mismatch: total={total} but destinations array has {len(destinations)} items",
                    data
                )
                return False
            
            # Check destination structure
            if destinations:
                first_dest = destinations[0]
                required_dest_fields = ["id", "name_en", "type", "district_id"]
                missing_dest_fields = [field for field in required_dest_fields if field not in first_dest]
                
                if missing_dest_fields:
                    self.log_result(
                        "List All Destinations",
                        False,
                        f"Missing destination fields: {missing_dest_fields}",
                        first_dest
                    )
                    return False
            
            self.log_result(
                "List All Destinations",
                True,
                f"✅ Retrieved {total} destinations with correct structure"
            )
            return True
            
        except Exception as e:
            self.log_result("List All Destinations", False, f"Exception: {str(e)}")
            return False
    
    async def test_filter_hill_stations(self):
        """Test 8: Filter by type - Hill Stations"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/destinations",
                params={"type": "HILL_STATION"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Filter Hill Stations", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            destinations = data.get("destinations", [])
            total = data.get("total", 0)
            
            # Should return 5 hill stations (as per review request)
            expected_hill_stations = ["Mahabaleshwar", "Panchgani", "Lonavala", "Khandala", "Matheran"]
            if total != 5:
                self.log_result(
                    "Filter Hill Stations",
                    False,
                    f"Expected 5 hill stations, got {total}",
                    data
                )
                return False
            
            # Check that all returned destinations are HILL_STATION type
            for dest in destinations:
                if dest.get("type") != "HILL_STATION":
                    self.log_result(
                        "Filter Hill Stations",
                        False,
                        f"Non-hill station in results: {dest.get('name_en')} type={dest.get('type')}",
                        data
                    )
                    return False
            
            # Check for expected hill stations
            dest_names = [dest.get("name_en") for dest in destinations]
            for expected in expected_hill_stations:
                if expected not in dest_names:
                    self.log_result(
                        "Filter Hill Stations",
                        False,
                        f"Missing expected hill station: {expected}. Found: {dest_names}",
                        data
                    )
                    return False
            
            self.log_result(
                "Filter Hill Stations",
                True,
                f"✅ Retrieved {total} hill stations: {dest_names}"
            )
            return True
            
        except Exception as e:
            self.log_result("Filter Hill Stations", False, f"Exception: {str(e)}")
            return False
    
    async def test_get_mahabaleshwar_info(self):
        """Test 9: Get Mahabaleshwar destination info"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/destination/mahabaleshwar"
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Get Mahabaleshwar Info", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            required_fields = ["destination", "reachable_from", "total_connections"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Get Mahabaleshwar Info",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            destination = data.get("destination")
            if not destination:
                self.log_result(
                    "Get Mahabaleshwar Info",
                    False,
                    "Missing destination info",
                    data
                )
                return False
            
            # Check destination details
            if destination.get("name_en") != "Mahabaleshwar":
                self.log_result(
                    "Get Mahabaleshwar Info",
                    False,
                    f"Expected name_en=Mahabaleshwar, got {destination.get('name_en')}",
                    data
                )
                return False
            
            if destination.get("type") != "HILL_STATION":
                self.log_result(
                    "Get Mahabaleshwar Info",
                    False,
                    f"Expected type=HILL_STATION, got {destination.get('type')}",
                    data
                )
                return False
            
            # Check reachable_from cities
            reachable_from = data.get("reachable_from", [])
            if not reachable_from:
                self.log_result(
                    "Get Mahabaleshwar Info",
                    False,
                    "No reachable_from cities found",
                    data
                )
                return False
            
            # Should have connections from major cities
            city_names = [city.get("city") for city in reachable_from]
            expected_cities = ["Pune", "Mumbai"]  # Based on feeder_links.json
            
            for expected_city in expected_cities:
                if expected_city not in city_names:
                    self.log_result(
                        "Get Mahabaleshwar Info",
                        False,
                        f"Missing expected connection from {expected_city}. Found: {city_names}",
                        data
                    )
                    return False
            
            self.log_result(
                "Get Mahabaleshwar Info",
                True,
                f"✅ Retrieved destination info with {len(reachable_from)} connections: {city_names}"
            )
            return True
            
        except Exception as e:
            self.log_result("Get Mahabaleshwar Info", False, f"Exception: {str(e)}")
            return False
    
    async def test_check_shirdi_tourist(self):
        """Test 10: Check Shirdi as tourist destination"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/check-tourist",
                params={"name": "shirdi"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Check Shirdi Tourist", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            required_fields = ["name", "is_tourist_destination"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Check Shirdi Tourist",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Should be a tourist destination
            if not data.get("is_tourist_destination"):
                self.log_result(
                    "Check Shirdi Tourist",
                    False,
                    f"Expected is_tourist_destination=true, got {data.get('is_tourist_destination')}",
                    data
                )
                return False
            
            # Check destination info
            dest_info = data.get("destination_info")
            if not dest_info:
                self.log_result(
                    "Check Shirdi Tourist",
                    False,
                    "Missing destination_info for tourist destination",
                    data
                )
                return False
            
            if dest_info.get("type") != "RELIGIOUS":
                self.log_result(
                    "Check Shirdi Tourist",
                    False,
                    f"Expected type=RELIGIOUS, got {dest_info.get('type')}",
                    data
                )
                return False
            
            self.log_result(
                "Check Shirdi Tourist",
                True,
                f"✅ Shirdi correctly identified as tourist destination, type: RELIGIOUS"
            )
            return True
            
        except Exception as e:
            self.log_result("Check Shirdi Tourist", False, f"Exception: {str(e)}")
            return False
    
    async def test_autocomplete_mahab(self):
        """Test 11: Autocomplete for 'mahab' should return tourist destination"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/autocomplete/bus",
                params={"q": "mahab", "limit": 5}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete Mahab", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            required_fields = ["query", "count", "results"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Autocomplete Mahab",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            results = data.get("results", [])
            if not results:
                self.log_result(
                    "Autocomplete Mahab",
                    False,
                    "No autocomplete results found for 'mahab'",
                    data
                )
                return False
            
            # Look for tourist destination with hill station emoji
            found_tourist_dest = False
            for result in results:
                label = result.get("label", "")
                result_type = result.get("type", "")
                
                if "🏔️" in label and "Mahabaleshwar" in label:
                    found_tourist_dest = True
                    
                    if result_type != "tourist_destination":
                        self.log_result(
                            "Autocomplete Mahab",
                            False,
                            f"Expected type=tourist_destination for Mahabaleshwar, got {result_type}",
                            result
                        )
                        return False
                    break
            
            if not found_tourist_dest:
                self.log_result(
                    "Autocomplete Mahab",
                    False,
                    f"No tourist destination with 🏔️ emoji found in results: {[r.get('label') for r in results]}",
                    data
                )
                return False
            
            self.log_result(
                "Autocomplete Mahab",
                True,
                f"✅ Found tourist destination with 🏔️ emoji in {len(results)} results"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete Mahab", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all feeder routes tests"""
        print("🚀 Starting Feeder Routes API Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Run all tests in order
        tests = [
            self.test_pune_to_mahabaleshwar,
            self.test_mumbai_to_ganpatipule,
            self.test_aurangabad_to_ajanta,
            self.test_nashik_to_trimbakeshwar,
            self.test_regular_city_to_city,
            self.test_remote_village_no_connectivity,
            self.test_list_all_destinations,
            self.test_filter_hill_stations,
            self.test_get_mahabaleshwar_info,
            self.test_check_shirdi_tourist,
            self.test_autocomplete_mahab
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
        print("\n" + "=" * 60)
        print("📊 FEEDER ROUTES TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All feeder routes tests passed!")
            print("📝 Tourist destination connectivity working correctly")
            print("📝 Route finding logic operational")
            print("📝 Autocomplete integration functional")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with FeederRoutesTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())