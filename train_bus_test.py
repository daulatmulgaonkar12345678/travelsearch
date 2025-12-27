#!/usr/bin/env python3
"""
Train & Bus Search API Testing
Tests the newly implemented Train and Bus Search endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta, date
import sys
import os

# Backend URL - using localhost as per system setup
BACKEND_URL = "http://localhost:8001"

class TrainBusSearchTester:
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
    
    def get_future_date(self, days_ahead=7):
        """Get a future date for testing"""
        return (date.today() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # ============================================================
    # TRAIN SEARCH TESTS
    # ============================================================
    
    async def test_train_search_popular_route(self):
        """Test train search with popular route (delhi to mumbai) - should return real offers"""
        try:
            future_date = self.get_future_date(7)
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "delhi",
                    "destination": "mumbai", 
                    "departure_date": future_date,
                    "passengers": 2
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Train Search Popular Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ["offers", "search_id", "is_fallback", "origin_city", "destination_city"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Train Search Popular Route",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Should have offers
            if not data.get("offers") or len(data["offers"]) == 0:
                self.log_result(
                    "Train Search Popular Route",
                    False,
                    "No offers returned - should never be empty",
                    data
                )
                return False
            
            # Should NOT be fallback for popular route
            if data.get("is_fallback") == True:
                self.log_result(
                    "Train Search Popular Route",
                    False,
                    "Popular route returned fallback - should have real data",
                    data
                )
                return False
            
            # Validate first offer structure
            first_offer = data["offers"][0]
            offer_required_fields = [
                "offer_id", "mode", "from_station", "to_station", 
                "departure_time", "arrival_time", "avg_price", "currency",
                "train_number", "train_name", "booking_partners"
            ]
            
            missing_offer_fields = [field for field in offer_required_fields if field not in first_offer]
            if missing_offer_fields:
                self.log_result(
                    "Train Search Popular Route",
                    False,
                    f"Missing offer fields: {missing_offer_fields}",
                    first_offer
                )
                return False
            
            # Validate booking partners
            if not first_offer.get("booking_partners") or len(first_offer["booking_partners"]) == 0:
                self.log_result(
                    "Train Search Popular Route",
                    False,
                    "No booking partners provided",
                    first_offer
                )
                return False
            
            # Check for IRCTC as first partner
            first_partner = first_offer["booking_partners"][0]
            if first_partner.get("name") != "IRCTC":
                self.log_result(
                    "Train Search Popular Route",
                    False,
                    f"Expected IRCTC as first partner, got {first_partner.get('name')}",
                    first_partner
                )
                return False
            
            self.log_result(
                "Train Search Popular Route",
                True,
                f"Found {len(data['offers'])} train offers for Delhi→Mumbai with real data"
            )
            return True
            
        except Exception as e:
            self.log_result("Train Search Popular Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_train_search_unknown_route(self):
        """Test train search with unknown route (varanasi to goa) - should return fallback redirect"""
        try:
            future_date = self.get_future_date(7)
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "varanasi",
                    "destination": "goa",
                    "departure_date": future_date,
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Train Search Unknown Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should have offers (never empty)
            if not data.get("offers") or len(data["offers"]) == 0:
                self.log_result(
                    "Train Search Unknown Route",
                    False,
                    "No offers returned - should never be empty",
                    data
                )
                return False
            
            # Should be fallback for unknown route
            if data.get("is_fallback") != True:
                self.log_result(
                    "Train Search Unknown Route",
                    False,
                    "Unknown route should return fallback=true",
                    data
                )
                return False
            
            # Should have fallback message
            if not data.get("fallback_message"):
                self.log_result(
                    "Train Search Unknown Route",
                    False,
                    "Fallback response missing fallback_message",
                    data
                )
                return False
            
            # Validate fallback offer
            fallback_offer = data["offers"][0]
            if not fallback_offer.get("booking_partners"):
                self.log_result(
                    "Train Search Unknown Route",
                    False,
                    "Fallback offer missing booking partners",
                    fallback_offer
                )
                return False
            
            self.log_result(
                "Train Search Unknown Route",
                True,
                f"Unknown route correctly returned fallback with {len(fallback_offer['booking_partners'])} booking partners"
            )
            return True
            
        except Exception as e:
            self.log_result("Train Search Unknown Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_train_search_date_validation(self):
        """Test train search date validation"""
        try:
            # Test past date
            past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "delhi",
                    "destination": "mumbai",
                    "departure_date": past_date
                }
            )
            
            if response.status_code != 400:
                self.log_result(
                    "Train Search Date Validation (Past)",
                    False,
                    f"Expected 400 for past date, got {response.status_code}",
                    response.text
                )
                return False
            
            # Test too far future date (121 days)
            far_future = (date.today() + timedelta(days=121)).strftime("%Y-%m-%d")
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "delhi",
                    "destination": "mumbai",
                    "departure_date": far_future
                }
            )
            
            if response.status_code != 400:
                self.log_result(
                    "Train Search Date Validation (Far Future)",
                    False,
                    f"Expected 400 for far future date, got {response.status_code}",
                    response.text
                )
                return False
            
            self.log_result(
                "Train Search Date Validation",
                True,
                "Past date and far future date correctly rejected with 400"
            )
            return True
            
        except Exception as e:
            self.log_result("Train Search Date Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_train_search_input_validation(self):
        """Test train search input validation"""
        try:
            future_date = self.get_future_date(7)
            
            # Test same origin/destination
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "delhi",
                    "destination": "delhi",
                    "departure_date": future_date
                }
            )
            
            if response.status_code != 400:
                self.log_result(
                    "Train Search Input Validation (Same Origin/Dest)",
                    False,
                    f"Expected 400 for same origin/destination, got {response.status_code}",
                    response.text
                )
                return False
            
            # Test missing required params
            response = await self.client.get(
                f"{self.backend_url}/api/search/trains",
                params={
                    "origin": "delhi",
                    # Missing destination
                    "departure_date": future_date
                }
            )
            
            if response.status_code != 422:
                self.log_result(
                    "Train Search Input Validation (Missing Params)",
                    False,
                    f"Expected 422 for missing params, got {response.status_code}",
                    response.text
                )
                return False
            
            self.log_result(
                "Train Search Input Validation",
                True,
                "Same origin/destination and missing params correctly rejected"
            )
            return True
            
        except Exception as e:
            self.log_result("Train Search Input Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_train_routes_endpoint(self):
        """Test GET /api/trains/routes endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/trains/routes")
            
            if response.status_code != 200:
                self.log_result(
                    "Train Routes Endpoint", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ["routes", "total", "message"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Train Routes Endpoint",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Should have routes
            if not data.get("routes") or len(data["routes"]) == 0:
                self.log_result(
                    "Train Routes Endpoint",
                    False,
                    "No routes returned",
                    data
                )
                return False
            
            # Validate route structure
            first_route = data["routes"][0]
            route_required_fields = ["route_key", "origin_code", "origin_city", "destination_code", "destination_city", "trains_count"]
            
            missing_route_fields = [field for field in route_required_fields if field not in first_route]
            if missing_route_fields:
                self.log_result(
                    "Train Routes Endpoint",
                    False,
                    f"Missing route fields: {missing_route_fields}",
                    first_route
                )
                return False
            
            self.log_result(
                "Train Routes Endpoint",
                True,
                f"Retrieved {data['total']} train routes successfully"
            )
            return True
            
        except Exception as e:
            self.log_result("Train Routes Endpoint", False, f"Exception: {str(e)}")
            return False
    
    # ============================================================
    # BUS SEARCH TESTS
    # ============================================================
    
    async def test_bus_search_popular_route(self):
        """Test bus search with popular route (mumbai to pune) - should return real offers"""
        try:
            future_date = self.get_future_date(7)
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "mumbai",
                    "destination": "pune",
                    "departure_date": future_date,
                    "passengers": 2
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Bus Search Popular Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ["offers", "search_id", "is_fallback", "origin_city", "destination_city"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Bus Search Popular Route",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Should have offers
            if not data.get("offers") or len(data["offers"]) == 0:
                self.log_result(
                    "Bus Search Popular Route",
                    False,
                    "No offers returned - should never be empty",
                    data
                )
                return False
            
            # Should NOT be fallback for popular route
            if data.get("is_fallback") == True:
                self.log_result(
                    "Bus Search Popular Route",
                    False,
                    "Popular route returned fallback - should have real data",
                    data
                )
                return False
            
            # Validate first offer structure
            first_offer = data["offers"][0]
            offer_required_fields = [
                "offer_id", "mode", "from_station", "to_station", 
                "departure_time", "arrival_time", "avg_price", "currency",
                "operator_name", "bus_type", "booking_partners"
            ]
            
            missing_offer_fields = [field for field in offer_required_fields if field not in first_offer]
            if missing_offer_fields:
                self.log_result(
                    "Bus Search Popular Route",
                    False,
                    f"Missing offer fields: {missing_offer_fields}",
                    first_offer
                )
                return False
            
            # Validate booking partners
            if not first_offer.get("booking_partners") or len(first_offer["booking_partners"]) == 0:
                self.log_result(
                    "Bus Search Popular Route",
                    False,
                    "No booking partners provided",
                    first_offer
                )
                return False
            
            # Check for redBus as first partner
            first_partner = first_offer["booking_partners"][0]
            if first_partner.get("name") != "redBus":
                self.log_result(
                    "Bus Search Popular Route",
                    False,
                    f"Expected redBus as first partner, got {first_partner.get('name')}",
                    first_partner
                )
                return False
            
            self.log_result(
                "Bus Search Popular Route",
                True,
                f"Found {len(data['offers'])} bus offers for Mumbai→Pune with real data"
            )
            return True
            
        except Exception as e:
            self.log_result("Bus Search Popular Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_bus_search_unknown_route(self):
        """Test bus search with unknown route (lucknow to trivandrum) - should return fallback redirect"""
        try:
            future_date = self.get_future_date(7)
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "lucknow",
                    "destination": "trivandrum",
                    "departure_date": future_date,
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Bus Search Unknown Route", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should have offers (never empty)
            if not data.get("offers") or len(data["offers"]) == 0:
                self.log_result(
                    "Bus Search Unknown Route",
                    False,
                    "No offers returned - should never be empty",
                    data
                )
                return False
            
            # Should be fallback for unknown route
            if data.get("is_fallback") != True:
                self.log_result(
                    "Bus Search Unknown Route",
                    False,
                    "Unknown route should return fallback=true",
                    data
                )
                return False
            
            # Should have fallback message
            if not data.get("fallback_message"):
                self.log_result(
                    "Bus Search Unknown Route",
                    False,
                    "Fallback response missing fallback_message",
                    data
                )
                return False
            
            # Validate fallback offer
            fallback_offer = data["offers"][0]
            if not fallback_offer.get("booking_partners"):
                self.log_result(
                    "Bus Search Unknown Route",
                    False,
                    "Fallback offer missing booking partners",
                    fallback_offer
                )
                return False
            
            self.log_result(
                "Bus Search Unknown Route",
                True,
                f"Unknown route correctly returned fallback with {len(fallback_offer['booking_partners'])} booking partners"
            )
            return True
            
        except Exception as e:
            self.log_result("Bus Search Unknown Route", False, f"Exception: {str(e)}")
            return False
    
    async def test_bus_search_filters(self):
        """Test bus search with filters (ac_only, sleeper_only)"""
        try:
            future_date = self.get_future_date(7)
            
            # Test AC only filter
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "mumbai",
                    "destination": "pune",
                    "departure_date": future_date,
                    "ac_only": True
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Bus Search AC Filter", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should have offers
            if not data.get("offers") or len(data["offers"]) == 0:
                self.log_result(
                    "Bus Search AC Filter",
                    False,
                    "No offers returned for AC filter",
                    data
                )
                return False
            
            # All offers should be AC
            non_ac_offers = [o for o in data["offers"] if not o.get("is_ac", False)]
            if non_ac_offers:
                self.log_result(
                    "Bus Search AC Filter",
                    False,
                    f"Found {len(non_ac_offers)} non-AC offers when ac_only=true",
                    non_ac_offers[0]
                )
                return False
            
            self.log_result(
                "Bus Search AC Filter",
                True,
                f"AC filter working - all {len(data['offers'])} offers are AC"
            )
            return True
            
        except Exception as e:
            self.log_result("Bus Search AC Filter", False, f"Exception: {str(e)}")
            return False
    
    async def test_bus_routes_endpoint(self):
        """Test GET /api/buses/routes endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/buses/routes")
            
            if response.status_code != 200:
                self.log_result(
                    "Bus Routes Endpoint", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ["routes", "total", "message"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Bus Routes Endpoint",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Should have routes
            if not data.get("routes") or len(data["routes"]) == 0:
                self.log_result(
                    "Bus Routes Endpoint",
                    False,
                    "No routes returned",
                    data
                )
                return False
            
            # Validate route structure
            first_route = data["routes"][0]
            route_required_fields = ["route_key", "origin_city", "destination_city", "distance_km", "operators_count", "bus_types"]
            
            missing_route_fields = [field for field in route_required_fields if field not in first_route]
            if missing_route_fields:
                self.log_result(
                    "Bus Routes Endpoint",
                    False,
                    f"Missing route fields: {missing_route_fields}",
                    first_route
                )
                return False
            
            self.log_result(
                "Bus Routes Endpoint",
                True,
                f"Retrieved {data['total']} bus routes successfully"
            )
            return True
            
        except Exception as e:
            self.log_result("Bus Routes Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_bus_search_date_validation(self):
        """Test bus search date validation"""
        try:
            # Test past date
            past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "mumbai",
                    "destination": "pune",
                    "departure_date": past_date
                }
            )
            
            if response.status_code != 400:
                self.log_result(
                    "Bus Search Date Validation (Past)",
                    False,
                    f"Expected 400 for past date, got {response.status_code}",
                    response.text
                )
                return False
            
            # Test too far future date (61 days)
            far_future = (date.today() + timedelta(days=61)).strftime("%Y-%m-%d")
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "mumbai",
                    "destination": "pune",
                    "departure_date": far_future
                }
            )
            
            if response.status_code != 400:
                self.log_result(
                    "Bus Search Date Validation (Far Future)",
                    False,
                    f"Expected 400 for far future date, got {response.status_code}",
                    response.text
                )
                return False
            
            self.log_result(
                "Bus Search Date Validation",
                True,
                "Past date and far future date correctly rejected with 400"
            )
            return True
            
        except Exception as e:
            self.log_result("Bus Search Date Validation", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all train and bus search tests"""
        print("🚀 Starting Train & Bus Search API Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Run all tests in order
        tests = [
            # Train tests
            self.test_train_search_popular_route,
            self.test_train_search_unknown_route,
            self.test_train_search_date_validation,
            self.test_train_search_input_validation,
            self.test_train_routes_endpoint,
            
            # Bus tests
            self.test_bus_search_popular_route,
            self.test_bus_search_unknown_route,
            self.test_bus_search_filters,
            self.test_bus_routes_endpoint,
            self.test_bus_search_date_validation,
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
        print("📊 TRAIN & BUS SEARCH TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All train & bus search tests passed!")
            print("📝 Popular routes return real data")
            print("📝 Unknown routes return fallback redirects")
            print("📝 Date validation working correctly")
            print("📝 Input validation working correctly")
            print("📝 Filters working correctly")
            print("📝 Routes endpoints working correctly")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with TrainBusSearchTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())