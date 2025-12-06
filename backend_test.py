#!/usr/bin/env python3
"""
Backend API Testing for TravelSearch Metasearch Platform
Tests real Amadeus and Aviasales provider integrations
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Backend URL - using localhost as specified in review request
BACKEND_URL = "http://localhost:8001"

class TravelSearchAPITester:
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
    
    async def test_health_check(self):
        """Test basic health endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Health Check", 
                    True, 
                    f"Backend is healthy - {data.get('status', 'unknown')}"
                )
                return True
            else:
                self.log_result(
                    "Health Check", 
                    False, 
                    f"Health check failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Health Check", False, f"Health check error: {str(e)}")
            return False
    
    async def test_flight_search_oneway(self):
        """Test oneway flight search: BOM -> DEL on 2025-12-20, 1 adult, economy"""
        try:
            payload = {
                "trip_type": "oneway",
                "origin": "BOM",
                "destination": "DEL", 
                "departure_date": "2025-12-20",
                "adults": 1,
                "cabin_class": "economy"
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/search/flights",
                json=payload
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    f"API returned status {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            # Check if we got real Amadeus offers (not mock)
            if not offers:
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    "No flight offers returned - likely in mock mode or API issue"
                )
                return False
            
            # Validate offer structure
            first_offer = offers[0]
            required_fields = ["offer_id", "provider", "price", "currency", "segments"]
            missing_fields = [field for field in required_fields if field not in first_offer]
            
            if missing_fields:
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    f"Missing required fields in offer: {missing_fields}",
                    first_offer
                )
                return False
            
            # Check if provider is Amadeus (not mock)
            if first_offer.get("provider") != "amadeus":
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    f"Expected provider 'amadeus', got '{first_offer.get('provider')}'",
                    first_offer
                )
                return False
            
            # Validate segments have required data
            segments = first_offer.get("segments", [])
            if not segments:
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    "No flight segments in offer",
                    first_offer
                )
                return False
            
            first_segment = segments[0]
            segment_fields = ["departure_airport", "arrival_airport", "departure_time", "arrival_time", "carrier_code"]
            missing_segment_fields = [field for field in segment_fields if not first_segment.get(field)]
            
            if missing_segment_fields:
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    f"Missing segment fields: {missing_segment_fields}",
                    first_segment
                )
                return False
            
            # Check price and currency
            price = first_offer.get("price")
            currency = first_offer.get("currency")
            
            if not isinstance(price, (int, float)) or price <= 0:
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    f"Invalid price: {price}",
                    first_offer
                )
                return False
            
            if not currency:
                self.log_result(
                    "Flight Search - Oneway",
                    False,
                    "Missing currency in offer",
                    first_offer
                )
                return False
            
            self.log_result(
                "Flight Search - Oneway",
                True,
                f"Found {len(offers)} real Amadeus offers, price: {price} {currency}, segments: {len(segments)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Flight Search - Oneway", False, f"Exception: {str(e)}")
            return False
    
    async def test_flight_search_roundtrip(self):
        """Test roundtrip flight: DEL -> BLR, depart 2025-12-25, return 2025-12-28, 2 adults"""
        try:
            payload = {
                "trip_type": "roundtrip",
                "origin": "DEL",
                "destination": "BLR",
                "departure_date": "2025-12-25",
                "return_date": "2025-12-28",
                "adults": 2,
                "cabin_class": "economy"
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/search/flights",
                json=payload
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Flight Search - Roundtrip",
                    False,
                    f"API returned status {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "Flight Search - Roundtrip",
                    False,
                    "No roundtrip flight offers returned"
                )
                return False
            
            first_offer = offers[0]
            
            # Validate it's from Amadeus
            if first_offer.get("provider") != "amadeus":
                self.log_result(
                    "Flight Search - Roundtrip",
                    False,
                    f"Expected Amadeus provider, got '{first_offer.get('provider')}'",
                    first_offer
                )
                return False
            
            # Check segments (roundtrip should have segments for both directions)
            segments = first_offer.get("segments", [])
            if len(segments) < 1:
                self.log_result(
                    "Flight Search - Roundtrip",
                    False,
                    f"Expected at least 1 segment for roundtrip, got {len(segments)}",
                    first_offer
                )
                return False
            
            self.log_result(
                "Flight Search - Roundtrip",
                True,
                f"Found {len(offers)} roundtrip offers from Amadeus, segments: {len(segments)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Flight Search - Roundtrip", False, f"Exception: {str(e)}")
            return False
    
    async def test_hotel_search(self):
        """Test hotel search: Mumbai, check-in 2025-12-20, check-out 2025-12-22, 1 room with 2 adults"""
        try:
            payload = {
                "city": "Mumbai",
                "check_in": "2025-12-20",
                "check_out": "2025-12-22",
                "rooms": [{"adults": 2, "children": []}]
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/search/hotels",
                json=payload
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Hotel Search",
                    False,
                    f"API returned status {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "Hotel Search",
                    False,
                    "No hotel offers returned"
                )
                return False
            
            first_offer = offers[0]
            required_fields = ["hotel_name", "total_price", "provider"]
            missing_fields = [field for field in required_fields if field not in first_offer]
            
            if missing_fields:
                self.log_result(
                    "Hotel Search",
                    False,
                    f"Missing required fields: {missing_fields}",
                    first_offer
                )
                return False
            
            # Check if provider is Amadeus
            if first_offer.get("provider") != "amadeus":
                self.log_result(
                    "Hotel Search",
                    False,
                    f"Expected Amadeus provider, got '{first_offer.get('provider')}'",
                    first_offer
                )
                return False
            
            # Validate price
            price = first_offer.get("total_price")
            if not isinstance(price, (int, float)) or price <= 0:
                self.log_result(
                    "Hotel Search",
                    False,
                    f"Invalid hotel price: {price}",
                    first_offer
                )
                return False
            
            self.log_result(
                "Hotel Search",
                True,
                f"Found {len(offers)} Amadeus hotel offers, first hotel: {first_offer.get('hotel_name')}, price: {price}"
            )
            return True
            
        except Exception as e:
            self.log_result("Hotel Search", False, f"Exception: {str(e)}")
            return False
    
    async def test_aviasales_redirect(self):
        """Test Aviasales affiliate redirect: BOM -> DEL, depart 2025-12-20, 1 adult"""
        try:
            params = {
                "origin": "BOM",
                "destination": "DEL", 
                "depart": "2025-12-20",
                "adults": 1
            }
            
            # Use follow_redirects=False to check the redirect response
            response = await self.client.get(
                f"{self.backend_url}/api/redirect/aviasales",
                params=params,
                follow_redirects=False
            )
            
            if response.status_code != 302:
                self.log_result(
                    "Aviasales Redirect",
                    False,
                    f"Expected 302 redirect, got {response.status_code}",
                    response.text
                )
                return False
            
            # Check Location header
            location = response.headers.get("location")
            if not location:
                self.log_result(
                    "Aviasales Redirect",
                    False,
                    "No Location header in redirect response",
                    dict(response.headers)
                )
                return False
            
            # Validate redirect URL contains aviasales.tpx.lt and marker
            if "aviasales.tpx.lt" not in location:
                self.log_result(
                    "Aviasales Redirect",
                    False,
                    f"Redirect URL doesn't contain aviasales.tpx.lt: {location}"
                )
                return False
            
            if "marker=689331" not in location:
                self.log_result(
                    "Aviasales Redirect",
                    False,
                    f"Redirect URL doesn't contain marker=689331: {location}"
                )
                return False
            
            # Check if route parameters are included
            if "origin_iata=BOM" not in location or "destination_iata=DEL" not in location:
                self.log_result(
                    "Aviasales Redirect",
                    False,
                    f"Redirect URL missing route parameters: {location}"
                )
                return False
            
            self.log_result(
                "Aviasales Redirect",
                True,
                f"Redirect working correctly to: {location}"
            )
            return True
            
        except Exception as e:
            self.log_result("Aviasales Redirect", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting TravelSearch Backend API Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Test health first
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ Backend health check failed - stopping tests")
            return False
        
        # Run all API tests
        tests = [
            self.test_flight_search_oneway,
            self.test_flight_search_roundtrip,
            self.test_hotel_search,
            self.test_aviasales_redirect
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
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend APIs are working with real providers.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with TravelSearchAPITester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())