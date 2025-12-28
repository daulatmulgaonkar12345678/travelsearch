#!/usr/bin/env python3
"""
Backend API Testing for Station-First Train Search Architecture
Tests the new STATION-FIRST train search architecture for /api/search/trains and /api/trains/autocomplete endpoints.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta, date
import sys
import os

# Backend URL - using production URL from frontend config
BACKEND_URL = "https://stationapi.preview.emergentagent.com"

class StationFirstTrainSearchTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.future_date = (date.today() + timedelta(days=10)).isoformat()
        
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
    
    # ============================================================
    # VALID INPUTS TESTS (Must return 200 with results)
    # ============================================================
    
    async def test_valid_station_codes(self):
        """Test 1.1: Station codes - GET /api/search/trains?origin=CSMT&destination=PUNE"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "CSMT",
                    "destination": "PUNE", 
                    "departure_date": self.future_date
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Valid Station Codes", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["status", "route", "offers"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Valid Station Codes",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Check status is success
            if data.get("status") != "success":
                self.log_result(
                    "Valid Station Codes",
                    False,
                    f"Expected status='success', got {data.get('status')}",
                    data
                )
                return False
            
            # Check route contains CSMT and PUNE
            route = data.get("route", {})
            origin_city = route.get("origin_city", "")
            dest_city = route.get("destination_city", "")
            
            if "CSMT" not in origin_city and "Mumbai" not in origin_city:
                self.log_result(
                    "Valid Station Codes",
                    False,
                    f"Origin city should contain CSMT or Mumbai, got: {origin_city}",
                    data
                )
                return False
            
            if "PUNE" not in dest_city and "Pune" not in dest_city:
                self.log_result(
                    "Valid Station Codes",
                    False,
                    f"Destination city should contain PUNE or Pune, got: {dest_city}",
                    data
                )
                return False
            
            self.log_result(
                "Valid Station Codes",
                True,
                f"Successfully returned results for CSMT→PUNE: {origin_city} → {dest_city}"
            )
            return True
            
        except Exception as e:
            self.log_result("Valid Station Codes", False, f"Exception: {str(e)}")
            return False
    
    async def test_valid_city_all_single(self):
        """Test 1.2: CITY_ALL token (single) - GET /api/search/trains?origin=MUMBAI_ALL&destination=PUNE"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "MUMBAI_ALL",
                    "destination": "PUNE", 
                    "departure_date": self.future_date
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Valid CITY_ALL Single", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check status is success
            if data.get("status") != "success":
                self.log_result(
                    "Valid CITY_ALL Single",
                    False,
                    f"Expected status='success', got {data.get('status')}",
                    data
                )
                return False
            
            # Check route.origin_city contains 'Mumbai (All Stations)'
            route = data.get("route", {})
            origin_city = route.get("origin_city", "")
            
            if "Mumbai" not in origin_city and "All Stations" not in origin_city:
                self.log_result(
                    "Valid CITY_ALL Single",
                    False,
                    f"Expected origin_city to contain 'Mumbai (All Stations)', got: {origin_city}",
                    data
                )
                return False
            
            self.log_result(
                "Valid CITY_ALL Single",
                True,
                f"Successfully returned results for MUMBAI_ALL→PUNE: {origin_city}"
            )
            return True
            
        except Exception as e:
            self.log_result("Valid CITY_ALL Single", False, f"Exception: {str(e)}")
            return False
    
    async def test_valid_both_city_all(self):
        """Test 1.3: Both CITY_ALL tokens - GET /api/search/trains?origin=MUMBAI_ALL&destination=PUNE_ALL"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "MUMBAI_ALL",
                    "destination": "PUNE_ALL", 
                    "departure_date": self.future_date
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Valid Both CITY_ALL", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check status is success
            if data.get("status") != "success":
                self.log_result(
                    "Valid Both CITY_ALL",
                    False,
                    f"Expected status='success', got {data.get('status')}",
                    data
                )
                return False
            
            # Check both cities show '(All Stations)'
            route = data.get("route", {})
            origin_city = route.get("origin_city", "")
            dest_city = route.get("destination_city", "")
            
            if "All Stations" not in origin_city:
                self.log_result(
                    "Valid Both CITY_ALL",
                    False,
                    f"Expected origin_city to contain '(All Stations)', got: {origin_city}",
                    data
                )
                return False
            
            if "All Stations" not in dest_city:
                self.log_result(
                    "Valid Both CITY_ALL",
                    False,
                    f"Expected destination_city to contain '(All Stations)', got: {dest_city}",
                    data
                )
                return False
            
            self.log_result(
                "Valid Both CITY_ALL",
                True,
                f"Successfully returned results for MUMBAI_ALL→PUNE_ALL: {origin_city} → {dest_city}"
            )
            return True
            
        except Exception as e:
            self.log_result("Valid Both CITY_ALL", False, f"Exception: {str(e)}")
            return False
    
    # ============================================================
    # INVALID INPUTS TESTS (MUST return 400, NOT 500)
    # ============================================================
    
    async def test_invalid_raw_city_name(self):
        """Test 2.1: Raw city name (Mumbai) - MUST return 400 error"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Mumbai",
                    "destination": "Pune", 
                    "departure_date": self.future_date
                }
            )
            
            # MUST return 400, NOT 500
            if response.status_code != 400:
                self.log_result(
                    "Invalid Raw City Name", 
                    False, 
                    f"Expected 400 for raw city name, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check error structure
            if "detail" not in data:
                self.log_result(
                    "Invalid Raw City Name",
                    False,
                    "Missing 'detail' in error response",
                    data
                )
                return False
            
            detail = data.get("detail", {})
            error_type = detail.get("error_type", "")
            message = detail.get("message", "")
            
            # Check error_type is INVALID_ORIGIN
            if error_type != "INVALID_ORIGIN":
                self.log_result(
                    "Invalid Raw City Name",
                    False,
                    f"Expected error_type='INVALID_ORIGIN', got: {error_type}",
                    data
                )
                return False
            
            # Check message contains "City names are not allowed"
            if "City names are not allowed" not in message:
                self.log_result(
                    "Invalid Raw City Name",
                    False,
                    f"Expected message to contain 'City names are not allowed', got: {message}",
                    data
                )
                return False
            
            self.log_result(
                "Invalid Raw City Name",
                True,
                f"Correctly rejected raw city name with 400 error: {error_type}"
            )
            return True
            
        except Exception as e:
            self.log_result("Invalid Raw City Name", False, f"Exception: {str(e)}")
            return False
    
    async def test_invalid_old_alias(self):
        """Test 2.2: Old alias (Bombay) - MUST return 400 error"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Bombay",
                    "destination": "PUNE", 
                    "departure_date": self.future_date
                }
            )
            
            # MUST return 400, NOT 500
            if response.status_code != 400:
                self.log_result(
                    "Invalid Old Alias", 
                    False, 
                    f"Expected 400 for old alias, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            detail = data.get("detail", {})
            error_type = detail.get("error_type", "")
            
            # Check error_type is INVALID_ORIGIN (aliases also rejected now)
            if error_type != "INVALID_ORIGIN":
                self.log_result(
                    "Invalid Old Alias",
                    False,
                    f"Expected error_type='INVALID_ORIGIN', got: {error_type}",
                    data
                )
                return False
            
            self.log_result(
                "Invalid Old Alias",
                True,
                f"Correctly rejected old alias with 400 error: {error_type}"
            )
            return True
            
        except Exception as e:
            self.log_result("Invalid Old Alias", False, f"Exception: {str(e)}")
            return False
    
    async def test_invalid_unknown_input(self):
        """Test 2.3: Unknown input - MUST return 400 error"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Xyzzy",
                    "destination": "PUNE", 
                    "departure_date": self.future_date
                }
            )
            
            # MUST return 400, NOT 500
            if response.status_code != 400:
                self.log_result(
                    "Invalid Unknown Input", 
                    False, 
                    f"Expected 400 for unknown input, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            detail = data.get("detail", {})
            error_type = detail.get("error_type", "")
            message = detail.get("message", "")
            
            # Check error_type is INVALID_ORIGIN
            if error_type != "INVALID_ORIGIN":
                self.log_result(
                    "Invalid Unknown Input",
                    False,
                    f"Expected error_type='INVALID_ORIGIN', got: {error_type}",
                    data
                )
                return False
            
            # Check message contains "not a valid station code"
            if "not a valid station code" not in message:
                self.log_result(
                    "Invalid Unknown Input",
                    False,
                    f"Expected message to contain 'not a valid station code', got: {message}",
                    data
                )
                return False
            
            self.log_result(
                "Invalid Unknown Input",
                True,
                f"Correctly rejected unknown input with 400 error: {error_type}"
            )
            return True
            
        except Exception as e:
            self.log_result("Invalid Unknown Input", False, f"Exception: {str(e)}")
            return False
    
    # ============================================================
    # AUTOCOMPLETE ENDPOINT TESTS (Station-First Dropdown)
    # ============================================================
    
    async def test_autocomplete_city_search(self):
        """Test 3.1: City search - GET /api/trains/autocomplete?q=Mumbai"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/autocomplete",
                params={"q": "Mumbai"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete City Search", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if "results" not in data:
                self.log_result(
                    "Autocomplete City Search",
                    False,
                    "Missing 'results' in response",
                    data
                )
                return False
            
            results = data.get("results", [])
            
            if not results:
                self.log_result(
                    "Autocomplete City Search",
                    False,
                    "No results returned for Mumbai search",
                    data
                )
                return False
            
            # First result should have value='MUMBAI_ALL'
            first_result = results[0]
            
            if first_result.get("value") != "MUMBAI_ALL":
                self.log_result(
                    "Autocomplete City Search",
                    False,
                    f"Expected first result value='MUMBAI_ALL', got: {first_result.get('value')}",
                    data
                )
                return False
            
            # Label should contain '(All Stations) ⭐'
            label = first_result.get("label", "")
            if "(All Stations)" not in label or "⭐" not in label:
                self.log_result(
                    "Autocomplete City Search",
                    False,
                    f"Expected label to contain '(All Stations) ⭐', got: {label}",
                    data
                )
                return False
            
            # Type should be 'city_all'
            if first_result.get("type") != "city_all":
                self.log_result(
                    "Autocomplete City Search",
                    False,
                    f"Expected type='city_all', got: {first_result.get('type')}",
                    data
                )
                return False
            
            # Following results should be individual stations
            station_results = [r for r in results[1:] if r.get("type") == "station"]
            if not station_results:
                self.log_result(
                    "Autocomplete City Search",
                    False,
                    "No individual station results found after city_all option",
                    data
                )
                return False
            
            self.log_result(
                "Autocomplete City Search",
                True,
                f"Correctly returned MUMBAI_ALL first with {len(station_results)} individual stations"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete City Search", False, f"Exception: {str(e)}")
            return False
    
    async def test_autocomplete_station_code_search(self):
        """Test 3.2: Station code search - GET /api/trains/autocomplete?q=CSMT"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/autocomplete",
                params={"q": "CSMT"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete Station Code Search", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                self.log_result(
                    "Autocomplete Station Code Search",
                    False,
                    "No results returned for CSMT search",
                    data
                )
                return False
            
            # First result should have value='CSMT'
            first_result = results[0]
            
            if first_result.get("value") != "CSMT":
                self.log_result(
                    "Autocomplete Station Code Search",
                    False,
                    f"Expected first result value='CSMT', got: {first_result.get('value')}",
                    data
                )
                return False
            
            # Type should be 'station'
            if first_result.get("type") != "station":
                self.log_result(
                    "Autocomplete Station Code Search",
                    False,
                    f"Expected type='station', got: {first_result.get('type')}",
                    data
                )
                return False
            
            self.log_result(
                "Autocomplete Station Code Search",
                True,
                f"Correctly returned CSMT station result: {first_result.get('label')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete Station Code Search", False, f"Exception: {str(e)}")
            return False
    
    async def test_autocomplete_pune_city_search(self):
        """Test 3.3: City search (Pune) - GET /api/trains/autocomplete?q=Pune"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/trains/autocomplete",
                params={"q": "Pune"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Autocomplete Pune City Search", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                self.log_result(
                    "Autocomplete Pune City Search",
                    False,
                    "No results returned for Pune search",
                    data
                )
                return False
            
            # First result should have value='PUNE_ALL'
            first_result = results[0]
            
            if first_result.get("value") != "PUNE_ALL":
                self.log_result(
                    "Autocomplete Pune City Search",
                    False,
                    f"Expected first result value='PUNE_ALL', got: {first_result.get('value')}",
                    data
                )
                return False
            
            # Label should contain '(All Stations) ⭐'
            label = first_result.get("label", "")
            if "(All Stations)" not in label or "⭐" not in label:
                self.log_result(
                    "Autocomplete Pune City Search",
                    False,
                    f"Expected label to contain '(All Stations) ⭐', got: {label}",
                    data
                )
                return False
            
            self.log_result(
                "Autocomplete Pune City Search",
                True,
                f"Correctly returned PUNE_ALL first: {label}"
            )
            return True
            
        except Exception as e:
            self.log_result("Autocomplete Pune City Search", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all station-first train search tests"""
        print("🚀 Starting Station-First Train Search Architecture Tests")
        print(f"Backend URL: {self.backend_url}")
        print(f"Future date for testing: {self.future_date}")
        print("=" * 80)
        
        # Run all tests in order
        tests = [
            # Valid inputs (Must return 200 with results)
            self.test_valid_station_codes,
            self.test_valid_city_all_single,
            self.test_valid_both_city_all,
            
            # Invalid inputs (MUST return 400, NOT 500)
            self.test_invalid_raw_city_name,
            self.test_invalid_old_alias,
            self.test_invalid_unknown_input,
            
            # Autocomplete endpoint (Station-First Dropdown)
            self.test_autocomplete_city_search,
            self.test_autocomplete_station_code_search,
            self.test_autocomplete_pune_city_search,
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
        print("📊 STATION-FIRST TRAIN SEARCH TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(results)
        total = len(results)
        
        # Group results by category
        valid_tests = self.test_results[:3]
        invalid_tests = self.test_results[3:6]
        autocomplete_tests = self.test_results[6:]
        
        print("\n🟢 VALID INPUTS TESTS (Must return 200 with results):")
        for result in valid_tests:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['details']}")
        
        print("\n🔴 INVALID INPUTS TESTS (MUST return 400, NOT 500):")
        for result in invalid_tests:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['details']}")
        
        print("\n🔍 AUTOCOMPLETE ENDPOINT TESTS (Station-First Dropdown):")
        for result in autocomplete_tests:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Station-First Train Search tests passed!")
            print("📝 Station codes (CSMT, PUNE) working correctly")
            print("📝 CITY_ALL tokens (MUMBAI_ALL, PUNE_ALL) working correctly")
            print("📝 Raw city names properly rejected with 400 errors")
            print("📝 Autocomplete returns station-first dropdown format")
            print("📝 NO 500 errors for any input - architecture is robust")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            failed_tests = [r for r in self.test_results if not r["success"]]
            print(f"❌ Failed tests: {[t['test'] for t in failed_tests]}")
        
        return passed == total

async def main():
    """Main test runner"""
    async with StationFirstTrainSearchTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())