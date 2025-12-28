#!/usr/bin/env python3
"""
Train Search Endpoint Testing - Defensive Backend with City Resolution
Tests the refactored /api/search/trains endpoint for all critical test cases
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Backend URL - using production URL from environment
BACKEND_URL = "https://train-resolver.preview.emergentagent.com"

class TrainSearchTester:
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
    
    def get_future_date(self, days_ahead: int = 10) -> str:
        """Get a future date for testing"""
        future_date = datetime.now().date() + timedelta(days=days_ahead)
        return future_date.isoformat()
    
    def get_far_future_date(self, days_ahead: int = 130) -> str:
        """Get a date too far in future for testing"""
        future_date = datetime.now().date() + timedelta(days=days_ahead)
        return future_date.isoformat()
    
    def get_past_date(self) -> str:
        """Get a past date for testing"""
        past_date = datetime.now().date() - timedelta(days=1)
        return past_date.isoformat()
    
    async def test_valid_city_names(self):
        """Test 1: Valid City Names - Pune to Mumbai"""
        try:
            future_date = self.get_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Pune",
                    "destination": "Mumbai", 
                    "departure_date": future_date
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Valid City Names (Pune→Mumbai)", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required response structure
            required_fields = ["status", "search_id", "timestamp", "route", "offers", "total_results", "is_fallback", "disclaimer"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Valid City Names (Pune→Mumbai)",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Check status is success
            if data.get("status") != "success":
                self.log_result(
                    "Valid City Names (Pune→Mumbai)",
                    False,
                    f"Expected status='success', got {data.get('status')}",
                    data
                )
                return False
            
            # Check route city names
            route = data.get("route", {})
            if route.get("origin_city") != "Pune":
                self.log_result(
                    "Valid City Names (Pune→Mumbai)",
                    False,
                    f"Expected route.origin_city='Pune', got {route.get('origin_city')}",
                    data
                )
                return False
            
            if route.get("destination_city") != "Mumbai":
                self.log_result(
                    "Valid City Names (Pune→Mumbai)",
                    False,
                    f"Expected route.destination_city='Mumbai', got {route.get('destination_city')}",
                    data
                )
                return False
            
            # Check offers structure
            offers = data.get("offers", [])
            if offers:
                first_offer = offers[0]
                required_offer_fields = ["train_number", "train_name", "departure_time", "arrival_time", "avg_price", "booking_partners"]
                missing_offer_fields = [field for field in required_offer_fields if field not in first_offer]
                
                if missing_offer_fields:
                    self.log_result(
                        "Valid City Names (Pune→Mumbai)",
                        False,
                        f"Missing required offer fields: {missing_offer_fields}",
                        first_offer
                    )
                    return False
            
            self.log_result(
                "Valid City Names (Pune→Mumbai)",
                True,
                f"Successfully returned {len(offers)} offers with correct city resolution"
            )
            return True
            
        except Exception as e:
            self.log_result("Valid City Names (Pune→Mumbai)", False, f"Exception: {str(e)}")
            return False
    
    async def test_alias_resolution(self):
        """Test 2: Alias Resolution - Bombay to Pune"""
        try:
            future_date = self.get_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Bombay",
                    "destination": "Pune", 
                    "departure_date": future_date
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Alias Resolution (Bombay→Pune)", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check status is success
            if data.get("status") != "success":
                self.log_result(
                    "Alias Resolution (Bombay→Pune)",
                    False,
                    f"Expected status='success', got {data.get('status')}",
                    data
                )
                return False
            
            # Check that Bombay was resolved to Mumbai
            route = data.get("route", {})
            if route.get("origin_city") != "Mumbai":
                self.log_result(
                    "Alias Resolution (Bombay→Pune)",
                    False,
                    f"Expected Bombay alias to resolve to Mumbai, got {route.get('origin_city')}",
                    data
                )
                return False
            
            # Should have multiple train results
            offers = data.get("offers", [])
            if len(offers) == 0:
                self.log_result(
                    "Alias Resolution (Bombay→Pune)",
                    False,
                    "Expected multiple train results, got 0 offers",
                    data
                )
                return False
            
            self.log_result(
                "Alias Resolution (Bombay→Pune)",
                True,
                f"Successfully resolved Bombay→Mumbai, returned {len(offers)} offers"
            )
            return True
            
        except Exception as e:
            self.log_result("Alias Resolution (Bombay→Pune)", False, f"Exception: {str(e)}")
            return False
    
    async def test_station_codes(self):
        """Test 3: Station Codes - CSMT to PUNE"""
        try:
            future_date = self.get_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "CSMT",
                    "destination": "PUNE", 
                    "departure_date": future_date
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Station Codes (CSMT→PUNE)", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check status is success
            if data.get("status") != "success":
                self.log_result(
                    "Station Codes (CSMT→PUNE)",
                    False,
                    f"Expected status='success', got {data.get('status')}",
                    data
                )
                return False
            
            # Check route city resolution
            route = data.get("route", {})
            if route.get("origin_city") != "Mumbai":
                self.log_result(
                    "Station Codes (CSMT→PUNE)",
                    False,
                    f"Expected route.origin_city='Mumbai' (from CSMT), got {route.get('origin_city')}",
                    data
                )
                return False
            
            if route.get("destination_city") != "Pune":
                self.log_result(
                    "Station Codes (CSMT→PUNE)",
                    False,
                    f"Expected route.destination_city='Pune' (from PUNE), got {route.get('destination_city')}",
                    data
                )
                return False
            
            self.log_result(
                "Station Codes (CSMT→PUNE)",
                True,
                f"Successfully resolved station codes to cities: Mumbai→Pune"
            )
            return True
            
        except Exception as e:
            self.log_result("Station Codes (CSMT→PUNE)", False, f"Exception: {str(e)}")
            return False
    
    async def test_invalid_origin(self):
        """Test 4: Invalid Origin - Should return 400 with suggestions"""
        try:
            future_date = self.get_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Punex",  # Invalid origin
                    "destination": "Mumbai", 
                    "departure_date": future_date
                }
            )
            
            # Should return 400, NOT 500
            if response.status_code != 400:
                self.log_result(
                    "Invalid Origin (Punex)", 
                    False, 
                    f"Expected 400 for invalid origin, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Handle FastAPI HTTPException format (error details in 'detail' field)
            error_data = data.get("detail", data)
            
            # Check error structure
            if error_data.get("status") != "error":
                self.log_result(
                    "Invalid Origin (Punex)",
                    False,
                    f"Expected status='error', got {error_data.get('status')}",
                    data
                )
                return False
            
            if error_data.get("error_type") != "INVALID_ORIGIN":
                self.log_result(
                    "Invalid Origin (Punex)",
                    False,
                    f"Expected error_type='INVALID_ORIGIN', got {error_data.get('error_type')}",
                    data
                )
                return False
            
            # Check suggestions array exists and has Pune as first suggestion
            suggestions = error_data.get("suggestions", [])
            if not suggestions:
                self.log_result(
                    "Invalid Origin (Punex)",
                    False,
                    "Expected suggestions array, got empty or missing",
                    data
                )
                return False
            
            # First suggestion should be Pune (closest match)
            first_suggestion = suggestions[0]
            if "pune" not in first_suggestion.get("display_name", "").lower():
                self.log_result(
                    "Invalid Origin (Punex)",
                    False,
                    f"Expected 'Pune' as first suggestion, got {first_suggestion.get('display_name')}",
                    data
                )
                return False
            
            self.log_result(
                "Invalid Origin (Punex)",
                True,
                f"Correctly returned 400 with error_type='INVALID_ORIGIN' and Pune as first suggestion"
            )
            return True
            
        except Exception as e:
            self.log_result("Invalid Origin (Punex)", False, f"Exception: {str(e)}")
            return False
    
    async def test_invalid_destination(self):
        """Test 5: Invalid Destination - Should return 400 with suggestions"""
        try:
            future_date = self.get_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Pune",
                    "destination": "Xyzzy",  # Invalid destination
                    "departure_date": future_date
                }
            )
            
            # Should return 400, NOT 500
            if response.status_code != 400:
                self.log_result(
                    "Invalid Destination (Xyzzy)", 
                    False, 
                    f"Expected 400 for invalid destination, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Handle FastAPI HTTPException format (error details in 'detail' field)
            error_data = data.get("detail", data)
            
            # Check error structure
            if error_data.get("status") != "error":
                self.log_result(
                    "Invalid Destination (Xyzzy)",
                    False,
                    f"Expected status='error', got {error_data.get('status')}",
                    data
                )
                return False
            
            if error_data.get("error_type") != "INVALID_DESTINATION":
                self.log_result(
                    "Invalid Destination (Xyzzy)",
                    False,
                    f"Expected error_type='INVALID_DESTINATION', got {error_data.get('error_type')}",
                    data
                )
                return False
            
            # Check suggestions array exists
            suggestions = error_data.get("suggestions", [])
            if not suggestions:
                self.log_result(
                    "Invalid Destination (Xyzzy)",
                    False,
                    "Expected suggestions array, got empty or missing",
                    data
                )
                return False
            
            self.log_result(
                "Invalid Destination (Xyzzy)",
                True,
                f"Correctly returned 400 with error_type='INVALID_DESTINATION' and {len(suggestions)} suggestions"
            )
            return True
            
        except Exception as e:
            self.log_result("Invalid Destination (Xyzzy)", False, f"Exception: {str(e)}")
            return False
    
    async def test_same_origin_destination(self):
        """Test 6: Same Origin/Destination - Should return 400"""
        try:
            future_date = self.get_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Pune",
                    "destination": "Pune",  # Same as origin
                    "departure_date": future_date
                }
            )
            
            # Should return 400
            if response.status_code != 400:
                self.log_result(
                    "Same Origin/Destination", 
                    False, 
                    f"Expected 400 for same origin/destination, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Handle FastAPI HTTPException format (error details in 'detail' field)
            error_data = data.get("detail", data)
            
            # Check error structure
            if error_data.get("status") != "error":
                self.log_result(
                    "Same Origin/Destination",
                    False,
                    f"Expected status='error', got {error_data.get('status')}",
                    data
                )
                return False
            
            if error_data.get("error_type") != "SAME_ORIGIN_DESTINATION":
                self.log_result(
                    "Same Origin/Destination",
                    False,
                    f"Expected error_type='SAME_ORIGIN_DESTINATION', got {error_data.get('error_type')}",
                    data
                )
                return False
            
            self.log_result(
                "Same Origin/Destination",
                True,
                "Correctly returned 400 with error_type='SAME_ORIGIN_DESTINATION'"
            )
            return True
            
        except Exception as e:
            self.log_result("Same Origin/Destination", False, f"Exception: {str(e)}")
            return False
    
    async def test_past_date(self):
        """Test 7: Past Date - Should return 400"""
        try:
            past_date = self.get_past_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Pune",
                    "destination": "Mumbai",
                    "departure_date": past_date
                }
            )
            
            # Should return 400
            if response.status_code != 400:
                self.log_result(
                    "Past Date Validation", 
                    False, 
                    f"Expected 400 for past date, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Handle FastAPI HTTPException format (error details in 'detail' field)
            error_data = data.get("detail", data)
            
            # Check error structure
            if error_data.get("status") != "error":
                self.log_result(
                    "Past Date Validation",
                    False,
                    f"Expected status='error', got {error_data.get('status')}",
                    data
                )
                return False
            
            if error_data.get("error_type") != "DATE_IN_PAST":
                self.log_result(
                    "Past Date Validation",
                    False,
                    f"Expected error_type='DATE_IN_PAST', got {error_data.get('error_type')}",
                    data
                )
                return False
            
            self.log_result(
                "Past Date Validation",
                True,
                "Correctly returned 400 with error_type='DATE_IN_PAST'"
            )
            return True
            
        except Exception as e:
            self.log_result("Past Date Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_future_date_too_far(self):
        """Test 8: Future Date >120 days - Should return 400"""
        try:
            far_future_date = self.get_far_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Pune",
                    "destination": "Mumbai",
                    "departure_date": far_future_date
                }
            )
            
            # Should return 400
            if response.status_code != 400:
                self.log_result(
                    "Future Date Too Far", 
                    False, 
                    f"Expected 400 for date >120 days, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check error structure
            if data.get("status") != "error":
                self.log_result(
                    "Future Date Too Far",
                    False,
                    f"Expected status='error', got {data.get('status')}",
                    data
                )
                return False
            
            if data.get("error_type") != "DATE_TOO_FAR":
                self.log_result(
                    "Future Date Too Far",
                    False,
                    f"Expected error_type='DATE_TOO_FAR', got {data.get('error_type')}",
                    data
                )
                return False
            
            self.log_result(
                "Future Date Too Far",
                True,
                "Correctly returned 400 with error_type='DATE_TOO_FAR'"
            )
            return True
            
        except Exception as e:
            self.log_result("Future Date Too Far", False, f"Exception: {str(e)}")
            return False
    
    async def test_response_structure_validation(self):
        """Test 9: Response Structure Validation - All required fields"""
        try:
            future_date = self.get_future_date()
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "Delhi",
                    "destination": "Mumbai", 
                    "departure_date": future_date
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Response Structure Validation", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check all required top-level fields
            required_fields = ["status", "search_id", "timestamp", "route", "offers", "total_results", "is_fallback", "disclaimer"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Response Structure Validation",
                    False,
                    f"Missing required top-level fields: {missing_fields}",
                    data
                )
                return False
            
            # Check route structure
            route = data.get("route", {})
            required_route_fields = ["origin_city", "destination_city"]
            missing_route_fields = [field for field in required_route_fields if field not in route]
            
            if missing_route_fields:
                self.log_result(
                    "Response Structure Validation",
                    False,
                    f"Missing required route fields: {missing_route_fields}",
                    route
                )
                return False
            
            # Check offer structure (if offers exist)
            offers = data.get("offers", [])
            if offers:
                first_offer = offers[0]
                required_offer_fields = ["train_number", "train_name", "departure_time", "arrival_time", "avg_price", "booking_partners"]
                missing_offer_fields = [field for field in required_offer_fields if field not in first_offer]
                
                if missing_offer_fields:
                    self.log_result(
                        "Response Structure Validation",
                        False,
                        f"Missing required offer fields: {missing_offer_fields}",
                        first_offer
                    )
                    return False
                
                # Check booking partners structure
                booking_partners = first_offer.get("booking_partners", [])
                if not booking_partners:
                    self.log_result(
                        "Response Structure Validation",
                        False,
                        "Missing booking_partners in offer",
                        first_offer
                    )
                    return False
            
            # Check fallback response structure (if fallback)
            if data.get("is_fallback"):
                if not offers:
                    self.log_result(
                        "Response Structure Validation",
                        False,
                        "Fallback response should have at least one offer with booking partner links",
                        data
                    )
                    return False
                
                fallback_offer = offers[0]
                if not fallback_offer.get("is_fallback"):
                    self.log_result(
                        "Response Structure Validation",
                        False,
                        "Fallback offer should have is_fallback=true",
                        fallback_offer
                    )
                    return False
            
            self.log_result(
                "Response Structure Validation",
                True,
                f"All required fields present. Response has {len(offers)} offers, is_fallback={data.get('is_fallback')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Response Structure Validation", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all train search tests"""
        print("🚆 Starting Train Search Endpoint Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Run all tests in order
        tests = [
            self.test_valid_city_names,
            self.test_alias_resolution,
            self.test_station_codes,
            self.test_invalid_origin,
            self.test_invalid_destination,
            self.test_same_origin_destination,
            self.test_past_date,
            self.test_future_date_too_far,
            self.test_response_structure_validation
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
        print("📊 TRAIN SEARCH ENDPOINT TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All train search tests passed!")
            print("📝 Defensive backend with city resolution working correctly")
            print("📝 All invalid inputs return 400 (not 500) with proper error types")
            print("📝 Response structure validation successful")
            print("📝 Alias resolution (Bombay→Mumbai) working")
            print("📝 Station code to city resolution working")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with TrainSearchTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())