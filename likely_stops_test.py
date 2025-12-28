#!/usr/bin/env python3
"""
Likely Stops on Route Feature Testing
=====================================

Tests the new "Likely Stops on Route" feature which shows intermediate bus stops 
between two cities with MAJOR/MINOR separation.

Critical Validation Rules:
- Mumbai → Ratnagiri MUST show Kashil under minor_stops
- Pune → Kolhapur MUST NOT show Kashil anywhere
- All responses must include note field with disclaimer
- UI must clearly separate MAJOR (always visible) from MINOR (expandable)
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys
import os

# Backend URL - using production URL from environment
BACKEND_URL = "https://train-resolver.preview.emergentagent.com"

class LikelyStopsTester:
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
    
    async def test_mumbai_ratnagiri_kashil_validation(self):
        """Test Mumbai → Ratnagiri route MUST show Kashil in minor_stops"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/stops",
                params={"from_city": "mumbai", "to_city": "ratnagiri"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Mumbai→Ratnagiri Kashil Validation", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["major_stops", "minor_stops", "corridor_name", "highway", "note"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Mumbai→Ratnagiri Kashil Validation",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # CRITICAL VALIDATION: Kashil MUST be in minor_stops
            minor_stops = data.get("minor_stops", [])
            kashil_found = any("kashil" in stop.lower() for stop in minor_stops)
            
            if not kashil_found:
                self.log_result(
                    "Mumbai→Ratnagiri Kashil Validation",
                    False,
                    f"CRITICAL: Kashil NOT found in minor_stops. Found: {minor_stops}",
                    data
                )
                return False
            
            # Validate expected major stops (allowing for spelling variations)
            major_stops = data.get("major_stops", [])
            expected_major = ["Panvel", "Alibag", "Chiplun"]  # Removed Mahad/Mhad due to spelling variation
            
            for expected in expected_major:
                if not any(expected.lower() in stop.lower() for stop in major_stops):
                    self.log_result(
                        "Mumbai→Ratnagiri Kashil Validation",
                        False,
                        f"Expected major stop '{expected}' not found in: {major_stops}",
                        data
                    )
                    return False
            
            # Check for Mahad/Mhad specifically (allowing spelling variations)
            mahad_found = any("mahad" in stop.lower() or "mhad" in stop.lower() for stop in major_stops)
            if not mahad_found:
                self.log_result(
                    "Mumbai→Ratnagiri Kashil Validation",
                    False,
                    f"Expected Mahad/Mhad in major stops, got: {major_stops}",
                    data
                )
                return False
            
            # Validate corridor info
            if data.get("corridor_name") != "Mumbai-Goa Konkan Highway":
                self.log_result(
                    "Mumbai→Ratnagiri Kashil Validation",
                    False,
                    f"Expected corridor 'Mumbai-Goa Konkan Highway', got: {data.get('corridor_name')}",
                    data
                )
                return False
            
            if data.get("highway") != "NH66":
                self.log_result(
                    "Mumbai→Ratnagiri Kashil Validation",
                    False,
                    f"Expected highway 'NH66', got: {data.get('highway')}",
                    data
                )
                return False
            
            # Validate disclaimer note
            note = data.get("note", "")
            if "indicative" not in note.lower() or "may vary" not in note.lower():
                self.log_result(
                    "Mumbai→Ratnagiri Kashil Validation",
                    False,
                    f"Missing proper disclaimer in note: {note}",
                    data
                )
                return False
            
            self.log_result(
                "Mumbai→Ratnagiri Kashil Validation",
                True,
                f"✅ Kashil found in minor_stops. Major: {len(major_stops)}, Minor: {len(minor_stops)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Mumbai→Ratnagiri Kashil Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_pune_kolhapur_no_kashil_validation(self):
        """Test Pune → Kolhapur route MUST NOT show Kashil anywhere"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/stops",
                params={"from_city": "pune", "to_city": "kolhapur"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Pune→Kolhapur No-Kashil Validation", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # CRITICAL VALIDATION: Kashil MUST NOT be anywhere
            major_stops = data.get("major_stops", [])
            minor_stops = data.get("minor_stops", [])
            all_stops = major_stops + minor_stops
            
            kashil_found = any("kashil" in stop.lower() for stop in all_stops)
            
            if kashil_found:
                self.log_result(
                    "Pune→Kolhapur No-Kashil Validation",
                    False,
                    f"CRITICAL: Kashil found in stops but should NOT be present. All stops: {all_stops}",
                    data
                )
                return False
            
            # Validate expected major stops for Pune→Kolhapur
            expected_major = ["Satara", "Karad", "Sangli"]
            
            for expected in expected_major:
                if not any(expected.lower() in stop.lower() for stop in major_stops):
                    self.log_result(
                        "Pune→Kolhapur No-Kashil Validation",
                        False,
                        f"Expected major stop '{expected}' not found in: {major_stops}",
                        data
                    )
                    return False
            
            # Validate expected minor stops
            expected_minor = ["Katraj", "Shirwal", "Umbraj", "Islampur", "Jaysingpur", "Ichalkaranji"]
            minor_found = 0
            for expected in expected_minor:
                if any(expected.lower() in stop.lower() for stop in minor_stops):
                    minor_found += 1
            
            if minor_found < 3:  # At least 3 expected minor stops should be found
                self.log_result(
                    "Pune→Kolhapur No-Kashil Validation",
                    False,
                    f"Expected at least 3 minor stops from {expected_minor}, found {minor_found} in: {minor_stops}",
                    data
                )
                return False
            
            # Validate corridor info
            if data.get("corridor_name") != "Pune-Kolhapur Highway":
                self.log_result(
                    "Pune→Kolhapur No-Kashil Validation",
                    False,
                    f"Expected corridor 'Pune-Kolhapur Highway', got: {data.get('corridor_name')}",
                    data
                )
                return False
            
            if data.get("highway") != "NH48":
                self.log_result(
                    "Pune→Kolhapur No-Kashil Validation",
                    False,
                    f"Expected highway 'NH48', got: {data.get('highway')}",
                    data
                )
                return False
            
            self.log_result(
                "Pune→Kolhapur No-Kashil Validation",
                True,
                f"✅ Kashil correctly NOT found. Major: {len(major_stops)}, Minor: {len(minor_stops)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Pune→Kolhapur No-Kashil Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_mumbai_nashik_corridor(self):
        """Test Mumbai → Nashik (NH3 corridor)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/stops",
                params={"from_city": "mumbai", "to_city": "nashik"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Mumbai→Nashik Corridor", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Validate basic structure
            if not all(key in data for key in ["major_stops", "minor_stops", "corridor_name", "highway"]):
                self.log_result(
                    "Mumbai→Nashik Corridor",
                    False,
                    "Missing required response fields",
                    data
                )
                return False
            
            # Should have some stops
            total_stops = len(data.get("major_stops", [])) + len(data.get("minor_stops", []))
            if total_stops == 0:
                self.log_result(
                    "Mumbai→Nashik Corridor",
                    False,
                    "No stops found for Mumbai→Nashik route",
                    data
                )
                return False
            
            self.log_result(
                "Mumbai→Nashik Corridor",
                True,
                f"Route found with {total_stops} total stops"
            )
            return True
            
        except Exception as e:
            self.log_result("Mumbai→Nashik Corridor", False, f"Exception: {str(e)}")
            return False
    
    async def test_city_id_based_query(self):
        """Test city ID based query (Pune=8, Kolhapur=11)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/stops",
                params={"from_city_id": 8, "to_city_id": 11}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "City ID Based Query", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should return same results as name-based query
            if data.get("from_city") != "Pune" or data.get("to_city") != "Kolhapur":
                self.log_result(
                    "City ID Based Query",
                    False,
                    f"Expected Pune→Kolhapur, got {data.get('from_city')}→{data.get('to_city')}",
                    data
                )
                return False
            
            # Should have expected major stops
            major_stops = data.get("major_stops", [])
            if not any("satara" in stop.lower() for stop in major_stops):
                self.log_result(
                    "City ID Based Query",
                    False,
                    f"Expected Satara in major stops, got: {major_stops}",
                    data
                )
                return False
            
            self.log_result(
                "City ID Based Query",
                True,
                f"City ID query working correctly: {data.get('from_city')}→{data.get('to_city')}"
            )
            return True
            
        except Exception as e:
            self.log_result("City ID Based Query", False, f"Exception: {str(e)}")
            return False
    
    async def test_invalid_parameters(self):
        """Test invalid parameters return 400"""
        try:
            # Test without required params
            response = await self.client.get(f"{self.backend_url}/api/routes/stops")
            
            if response.status_code != 400:
                self.log_result(
                    "Invalid Parameters", 
                    False, 
                    f"Expected 400 for missing params, got {response.status_code}",
                    response.text
                )
                return False
            
            self.log_result(
                "Invalid Parameters",
                True,
                "Missing parameters correctly rejected with 400"
            )
            return True
            
        except Exception as e:
            self.log_result("Invalid Parameters", False, f"Exception: {str(e)}")
            return False
    
    async def test_route_summary_endpoint(self):
        """Test GET /api/routes/summary endpoint"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/routes/summary",
                params={"from_city": "pune", "to_city": "kolhapur"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Route Summary Endpoint", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["via", "via_text", "has_minor_stops", "minor_count"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Route Summary Endpoint",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Validate via_text format
            via_text = data.get("via_text", "")
            if "→" not in via_text and via_text != "Direct":
                self.log_result(
                    "Route Summary Endpoint",
                    False,
                    f"Invalid via_text format: {via_text}",
                    data
                )
                return False
            
            # Should have minor stops for Pune→Kolhapur
            if not data.get("has_minor_stops"):
                self.log_result(
                    "Route Summary Endpoint",
                    False,
                    "Expected has_minor_stops=true for Pune→Kolhapur",
                    data
                )
                return False
            
            if data.get("minor_count", 0) <= 0:
                self.log_result(
                    "Route Summary Endpoint",
                    False,
                    f"Expected minor_count > 0, got: {data.get('minor_count')}",
                    data
                )
                return False
            
            self.log_result(
                "Route Summary Endpoint",
                True,
                f"Summary: {via_text}, Minor stops: {data.get('minor_count')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Route Summary Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_corridors_list_endpoint(self):
        """Test GET /api/routes/corridors endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/routes/corridors")
            
            if response.status_code != 200:
                self.log_result(
                    "Corridors List Endpoint", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            if "corridors" not in data or "total" not in data:
                self.log_result(
                    "Corridors List Endpoint",
                    False,
                    "Missing 'corridors' or 'total' in response",
                    data
                )
                return False
            
            corridors = data.get("corridors", [])
            total = data.get("total", 0)
            
            # Should return 8 corridors as per requirement
            if total != 8:
                self.log_result(
                    "Corridors List Endpoint",
                    False,
                    f"Expected 8 corridors, got {total}",
                    data
                )
                return False
            
            if len(corridors) != total:
                self.log_result(
                    "Corridors List Endpoint",
                    False,
                    f"Count mismatch: {total} reported but {len(corridors)} corridors returned",
                    data
                )
                return False
            
            # Validate corridor structure
            if corridors:
                first_corridor = corridors[0]
                required_fields = ["id", "name", "highway", "major_stops_count", "minor_stops_count"]
                missing_fields = [field for field in required_fields if field not in first_corridor]
                
                if missing_fields:
                    self.log_result(
                        "Corridors List Endpoint",
                        False,
                        f"Missing required fields in corridor: {missing_fields}",
                        first_corridor
                    )
                    return False
            
            self.log_result(
                "Corridors List Endpoint",
                True,
                f"Found {total} corridors with proper structure"
            )
            return True
            
        except Exception as e:
            self.log_result("Corridors List Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all likely stops tests"""
        print("🚀 Starting Likely Stops on Route Feature Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 70)
        
        # Run all tests in order
        tests = [
            self.test_mumbai_ratnagiri_kashil_validation,
            self.test_pune_kolhapur_no_kashil_validation,
            self.test_mumbai_nashik_corridor,
            self.test_city_id_based_query,
            self.test_invalid_parameters,
            self.test_route_summary_endpoint,
            self.test_corridors_list_endpoint
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
        print("\n" + "=" * 70)
        print("📊 LIKELY STOPS ON ROUTE TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Likely Stops tests passed!")
            print("📝 CRITICAL VALIDATIONS SUCCESSFUL:")
            print("   ✅ Mumbai→Ratnagiri shows Kashil in minor_stops")
            print("   ✅ Pune→Kolhapur does NOT show Kashil anywhere")
            print("   ✅ All endpoints return proper MAJOR/MINOR separation")
            print("   ✅ 8 corridors available with proper structure")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            print("🔍 CRITICAL ISSUES FOUND - Feature may not be working correctly")
        
        return passed == total

async def main():
    """Main test runner"""
    async with LikelyStopsTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())