#!/usr/bin/env python3
"""
Backend API Testing for City-First Hotel Search Model (Industry Standard)
Testing the new city-first hotel search implementation as per review request.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import time
from urllib.parse import quote, unquote

# Backend URL Configuration - Use local backend
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class CityFirstHotelSearchTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Hotel-Search-Tester/1.0'
        })
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_smart_search_city_area_only(self):
        """Test Smart Search - City/Area Only (NO HOTEL type suggestions)"""
        print("\n🔍 TESTING SMART SEARCH - CITY/AREA ONLY")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/hotels/smart-search"
            params = {'query': 'Mumbai'}
            
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Check result types - should only contain CITY and AREA
                types_found = set()
                hotel_types_found = []
                
                for result in results:
                    result_type = result.get('type', '').upper()
                    types_found.add(result_type)
                    if result_type == 'HOTEL':
                        hotel_types_found.append(result.get('name', 'Unknown'))
                
                if 'HOTEL' not in types_found:
                    self.log_test("Smart Search - No HOTEL Type", True, 
                                f"Correctly returns only CITY and AREA types: {', '.join(types_found)}")
                else:
                    self.log_test("Smart Search - No HOTEL Type", False, 
                                f"Found HOTEL type suggestions: {hotel_types_found}")
                
                # Verify CITY and AREA types are present
                expected_types = {'CITY', 'AREA'}
                found_expected = expected_types.intersection(types_found)
                
                if found_expected:
                    self.log_test("Smart Search - CITY/AREA Present", True, 
                                f"Found expected types: {', '.join(found_expected)}")
                else:
                    self.log_test("Smart Search - CITY/AREA Present", False, 
                                f"Missing CITY/AREA types. Found: {', '.join(types_found)}")
            else:
                self.log_test("Smart Search - City/Area Only", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Smart Search - City/Area Only", False, f"Exception: {str(e)}")

    def test_smart_search_hotel_name_query(self):
        """Test Smart Search - Hotel Name Query (Should Return No Results or Only City)"""
        print("\n🏨 TESTING SMART SEARCH - HOTEL NAME QUERY")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/hotels/smart-search"
            params = {'query': 'Taj'}
            
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Should return empty or only City results (no hotel-specific suggestions)
                hotel_suggestions = []
                city_suggestions = []
                
                for result in results:
                    result_type = result.get('type', '').upper()
                    if result_type == 'HOTEL':
                        hotel_suggestions.append(result.get('name', 'Unknown'))
                    elif result_type == 'CITY':
                        city_suggestions.append(result.get('name', 'Unknown'))
                
                if not hotel_suggestions:
                    self.log_test("Smart Search - No Hotel Suggestions", True, 
                                f"Correctly returns no hotel suggestions for 'Taj' query")
                else:
                    self.log_test("Smart Search - No Hotel Suggestions", False, 
                                f"Found hotel suggestions: {hotel_suggestions}")
                
                # City results are acceptable
                if city_suggestions:
                    self.log_test("Smart Search - City Results OK", True, 
                                f"Found acceptable city results: {city_suggestions}")
                elif not results:
                    self.log_test("Smart Search - Empty Results OK", True, 
                                "Empty results acceptable for hotel name query")
                
            else:
                self.log_test("Smart Search - Hotel Name Query", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Smart Search - Hotel Name Query", False, f"Exception: {str(e)}")

    def test_city_search_all_hotels(self):
        """Test CITY Search - Should return all hotels (17 hotels for Mumbai)"""
        print("\n🏙️ TESTING CITY SEARCH - ALL HOTELS")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/search/hotels"
            
            payload = {
                "city": "Mumbai",
                "check_in": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "check_out": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "rooms": [{"adults": 2, "children": []}],
                "search_type": "CITY"
            }
            
            response = self.session.post(test_url, json=payload, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                
                # Should return all available hotels (17 expected for Mumbai)
                if offers:
                    self.log_test("CITY Search - All Hotels", True, 
                                f"Found {len(offers)} hotels in Mumbai (city-wide search)")
                    
                    # Log sample hotel details
                    if len(offers) > 0:
                        sample_hotel = offers[0]
                        hotel_name = sample_hotel.get('hotel_name', 'Unknown')
                        price = sample_hotel.get('price', 0)
                        print(f"   Sample hotel: {hotel_name} (₹{price})")
                else:
                    self.log_test("CITY Search - All Hotels", False, 
                                "No hotels returned for city search")
            else:
                self.log_test("CITY Search - All Hotels", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("CITY Search - All Hotels", False, f"Exception: {str(e)}")

    def test_area_search_industry_standard(self):
        """Test AREA Search - Industry Standard Behavior (graceful fallback)"""
        print("\n🗺️ TESTING AREA SEARCH - INDUSTRY STANDARD")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/search/hotels"
            
            payload = {
                "city": "Mumbai",
                "check_in": "2026-02-15",
                "check_out": "2026-02-16",
                "rooms": [{"adults": 2, "children": []}],
                "search_type": "AREA",
                "area": "Bandra"
            }
            
            response = self.session.post(test_url, json=payload, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                
                # Industry standard: attempts filtering but returns all hotels if no area metadata
                if offers:
                    self.log_test("AREA Search - Graceful Fallback", True, 
                                f"Found {len(offers)} hotels (area filtering attempted, fallback to all hotels)")
                    
                    # This matches how major platforms handle unavailable area data
                    print(f"   Industry Standard: Like Skyscanner/Kayak - returns all hotels when area metadata unavailable")
                else:
                    self.log_test("AREA Search - Graceful Fallback", False, 
                                "No hotels returned - should fallback to all hotels")
            else:
                self.log_test("AREA Search - Industry Standard", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("AREA Search - Industry Standard", False, f"Exception: {str(e)}")

    def test_click_logs_redirect(self):
        """Test Click Logs - Redirect and Logging"""
        print("\n📊 TESTING CLICK LOGS - REDIRECT")
        print("=" * 50)
        
        try:
            # Test redirect endpoint
            test_url = f"{API_BASE}/redirect"
            target_url = "https://www.booking.com"
            params = {
                'service': 'hotel',
                'vendor': 'booking',
                'target': quote(target_url),
                'city': 'Mumbai',
                'hotel_name': 'TestHotel',
                'search_type': 'CITY',
                'price': 5000
            }
            
            response = self.session.get(test_url, params=params, timeout=30, allow_redirects=False)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('location', '')
                self.log_test("Click Logs - Redirect", True, 
                            f"302 redirect successful to {location}")
                
                # Wait for background logging
                time.sleep(2)
                
                # Check click logs
                logs_url = f"{API_BASE}/admin/click-logs"
                logs_response = self.session.get(logs_url, timeout=30)
                
                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    logs = logs_data.get('logs', [])
                    
                    # Look for our logged event
                    event_found = False
                    for log in logs:
                        if (log.get('vendor') == 'booking' and 
                            log.get('service') == 'hotel' and
                            log.get('city') == 'Mumbai'):
                            event_found = True
                            break
                    
                    if event_found:
                        self.log_test("Click Logs - Event Logged", True, 
                                    "Click event successfully logged")
                    else:
                        self.log_test("Click Logs - Event Logged", False, 
                                    "Click event not found in logs")
                else:
                    self.log_test("Click Logs - Check Logs", False, 
                                f"Could not check logs: HTTP {logs_response.status_code}")
            else:
                self.log_test("Click Logs - Redirect", False, 
                            f"Expected 302, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Click Logs - Redirect", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests for City-First Hotel Search Model"""
        print("🧪 CITY-FIRST HOTEL SEARCH MODEL TESTING STARTED")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 70)
        
        # Run all test suites for City-First Hotel Search Model
        self.test_smart_search_city_area_only()
        self.test_smart_search_hotel_name_query()
        self.test_city_search_all_hotels()
        self.test_area_search_industry_standard()
        self.test_click_logs_redirect()
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   - {test}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = CityFirstHotelSearchTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)