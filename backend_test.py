#!/usr/bin/env python3
"""
Backend API Testing for Train and Bus Search with Frontend Animations Support
Testing the APIs mentioned in the review request to ensure they work correctly.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import time

# Backend URL Configuration
BACKEND_URL = "https://stationapi.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Backend-Tester/1.0'
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
    
    def test_train_search_api(self):
        """Test Train Search API with specific parameters from review request"""
        print("\n🚆 TESTING TRAIN SEARCH API")
        print("=" * 50)
        
        # Test Case 1: Valid station codes (PUNE to CSMT)
        test_url = f"{API_BASE}/search/trains"
        params = {
            'origin': 'PUNE',
            'destination': 'CSMT', 
            'departure_date': '2026-02-15',
            'passengers': 1
        }
        
        try:
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['offers', 'route']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Train Search - Response Structure", False, 
                                f"Missing fields: {missing_fields}")
                else:
                    # Check route object
                    route = data.get('route', {})
                    has_route_fields = all(field in route for field in 
                                         ['origin_city', 'destination_city', 'distance_km'])
                    
                    # Check offers structure
                    offers = data.get('offers', [])
                    offers_valid = True
                    if offers:
                        first_offer = offers[0]
                        required_offer_fields = ['booking_partners']
                        offers_valid = all(field in first_offer for field in required_offer_fields)
                        
                        # Check booking partners
                        if 'booking_partners' in first_offer:
                            partners = first_offer['booking_partners']
                            if isinstance(partners, list) and len(partners) > 0:
                                partner = partners[0]
                                partner_valid = all(field in partner for field in ['name', 'url', 'priority'])
                            else:
                                partner_valid = False
                        else:
                            partner_valid = False
                    
                    # Check is_fallback field
                    has_fallback = 'is_fallback' in data
                    
                    if has_route_fields and offers_valid and partner_valid and has_fallback:
                        self.log_test("Train Search PUNE→CSMT", True, 
                                    f"Found {len(offers)} offers, route distance: {route.get('distance_km')}km")
                    else:
                        issues = []
                        if not has_route_fields: issues.append("route fields missing")
                        if not offers_valid: issues.append("offers structure invalid")
                        if not partner_valid: issues.append("booking partners invalid")
                        if not has_fallback: issues.append("is_fallback missing")
                        self.log_test("Train Search PUNE→CSMT", False, f"Issues: {', '.join(issues)}")
            else:
                self.log_test("Train Search PUNE→CSMT", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Train Search PUNE→CSMT", False, f"Exception: {str(e)}")
        
        # Test Case 2: Test with other valid station codes
        test_cases = [
            ('NDLS', 'BCT', 'New Delhi to Mumbai Central'),
            ('CSMT', 'PUNE', 'Mumbai to Pune (reverse)')
        ]
        
        for origin, dest, description in test_cases:
            try:
                params = {
                    'origin': origin,
                    'destination': dest,
                    'departure_date': '2026-02-15',
                    'passengers': 1
                }
                response = self.session.get(test_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    offers = data.get('offers', [])
                    route = data.get('route', {})
                    self.log_test(f"Train Search {description}", True, 
                                f"Found {len(offers)} offers")
                else:
                    self.log_test(f"Train Search {description}", False, 
                                f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Train Search {description}", False, f"Exception: {str(e)}")
    
    def test_train_autocomplete_api(self):
        """Test Train Autocomplete API for CITY_ALL tokens"""
        print("\n🔍 TESTING TRAIN AUTOCOMPLETE API")
        print("=" * 50)
        
        test_url = f"{API_BASE}/trains/autocomplete"
        
        # Test Case 1: Search for "mumbai" should return MUMBAI_ALL
        try:
            params = {'q': 'mumbai'}
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Look for MUMBAI_ALL token
                mumbai_all_found = False
                city_all_first = False
                
                if results:
                    first_result = results[0]
                    if first_result.get('value') == 'MUMBAI_ALL' and first_result.get('type') == 'city_all':
                        mumbai_all_found = True
                        city_all_first = True
                        if '⭐' in first_result.get('label', ''):
                            star_found = True
                        else:
                            star_found = False
                    
                    # Check if any result has MUMBAI_ALL
                    for result in results:
                        if result.get('value') == 'MUMBAI_ALL':
                            mumbai_all_found = True
                            break
                
                if mumbai_all_found and city_all_first:
                    self.log_test("Train Autocomplete Mumbai→MUMBAI_ALL", True, 
                                f"Found MUMBAI_ALL as first result with {len(results)} total results")
                else:
                    issues = []
                    if not mumbai_all_found: issues.append("MUMBAI_ALL not found")
                    if not city_all_first: issues.append("MUMBAI_ALL not first")
                    self.log_test("Train Autocomplete Mumbai→MUMBAI_ALL", False, 
                                f"Issues: {', '.join(issues)}")
            else:
                self.log_test("Train Autocomplete Mumbai→MUMBAI_ALL", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Train Autocomplete Mumbai→MUMBAI_ALL", False, f"Exception: {str(e)}")
        
        # Test Case 2: Search for specific station code
        try:
            params = {'q': 'CSMT'}
            response = self.session.get(test_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                # Look for exact CSMT match
                csmt_found = False
                if results:
                    for result in results:
                        if result.get('value') == 'CSMT' and result.get('type') == 'station':
                            csmt_found = True
                            break
                
                if csmt_found:
                    self.log_test("Train Autocomplete CSMT Station", True, 
                                f"Found CSMT station in {len(results)} results")
                else:
                    self.log_test("Train Autocomplete CSMT Station", False, 
                                "CSMT station not found in results")
            else:
                self.log_test("Train Autocomplete CSMT Station", False, 
                            f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Train Autocomplete CSMT Station", False, f"Exception: {str(e)}")
    
    def test_bus_search_api(self):
        """Test Bus Search API with specific parameters"""
        print("\n🚌 TESTING BUS SEARCH API")
        print("=" * 50)
        
        test_url = f"{API_BASE}/search/buses"
        params = {
            'origin': 'Pune',
            'destination': 'Mumbai',
            'departure_date': '2026-02-15',
            'passengers': 1
        }
        
        try:
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['offers', 'origin_city', 'destination_city', 'distance_km']
                
                # Check if we have route object or direct fields
                if 'route' in data:
                    route = data['route']
                    has_route_fields = all(field in route for field in 
                                         ['origin_city', 'destination_city', 'distance_km'])
                else:
                    has_route_fields = all(field in data for field in required_fields)
                
                # Check offers structure
                offers = data.get('offers', [])
                offers_valid = True
                booking_partners_valid = True
                
                if offers:
                    first_offer = offers[0]
                    required_offer_fields = ['booking_partners']
                    offers_valid = all(field in first_offer for field in required_offer_fields)
                    
                    # Check booking partners (should include redBus, AbhiBus, etc.)
                    if 'booking_partners' in first_offer:
                        partners = first_offer['booking_partners']
                        if isinstance(partners, list) and len(partners) > 0:
                            partner_names = [p.get('name', '') for p in partners]
                            expected_partners = ['redBus', 'AbhiBus', 'Paytm']
                            has_expected = any(expected in str(partner_names) for expected in expected_partners)
                            booking_partners_valid = has_expected
                        else:
                            booking_partners_valid = False
                    else:
                        booking_partners_valid = False
                
                if has_route_fields and offers_valid and booking_partners_valid:
                    self.log_test("Bus Search Pune→Mumbai", True, 
                                f"Found {len(offers)} offers with valid booking partners")
                else:
                    issues = []
                    if not has_route_fields: issues.append("route fields missing")
                    if not offers_valid: issues.append("offers structure invalid")
                    if not booking_partners_valid: issues.append("booking partners invalid")
                    self.log_test("Bus Search Pune→Mumbai", False, f"Issues: {', '.join(issues)}")
            else:
                self.log_test("Bus Search Pune→Mumbai", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Bus Search Pune→Mumbai", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for invalid dates and missing parameters"""
        print("\n⚠️  TESTING ERROR HANDLING")
        print("=" * 50)
        
        # Test Case 1: Past date for train search
        try:
            test_url = f"{API_BASE}/search/trains"
            past_date = (date.today() - timedelta(days=1)).isoformat()
            params = {
                'origin': 'PUNE',
                'destination': 'CSMT',
                'departure_date': past_date,
                'passengers': 1
            }
            
            response = self.session.get(test_url, params=params, timeout=30)
            
            if response.status_code == 400:
                data = response.json()
                if 'error_type' in data and 'DATE_IN_PAST' in str(data.get('error_type')):
                    self.log_test("Train Search Past Date Error", True, 
                                "Correctly rejected past date with 400 error")
                else:
                    self.log_test("Train Search Past Date Error", False, 
                                f"Wrong error format: {data}")
            else:
                self.log_test("Train Search Past Date Error", False, 
                            f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Train Search Past Date Error", False, f"Exception: {str(e)}")
        
        # Test Case 2: Missing parameters for train search
        try:
            test_url = f"{API_BASE}/search/trains"
            params = {
                'origin': 'PUNE',
                # Missing destination and departure_date
                'passengers': 1
            }
            
            response = self.session.get(test_url, params=params, timeout=30)
            
            if response.status_code == 422:  # FastAPI validation error
                self.log_test("Train Search Missing Params", True, 
                            "Correctly rejected missing parameters with 422 error")
            else:
                self.log_test("Train Search Missing Params", False, 
                            f"Expected 422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Train Search Missing Params", False, f"Exception: {str(e)}")
        
        # Test Case 3: Past date for bus search
        try:
            test_url = f"{API_BASE}/search/buses"
            past_date = (date.today() - timedelta(days=1)).isoformat()
            params = {
                'origin': 'Pune',
                'destination': 'Mumbai',
                'departure_date': past_date,
                'passengers': 1
            }
            
            response = self.session.get(test_url, params=params, timeout=30)
            
            if response.status_code == 400:
                self.log_test("Bus Search Past Date Error", True, 
                            "Correctly rejected past date with 400 error")
            else:
                self.log_test("Bus Search Past Date Error", False, 
                            f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Bus Search Past Date Error", False, f"Exception: {str(e)}")
        
        # Test Case 4: Missing parameters for bus search
        try:
            test_url = f"{API_BASE}/search/buses"
            params = {
                'origin': 'Pune',
                # Missing destination and departure_date
                'passengers': 1
            }
            
            response = self.session.get(test_url, params=params, timeout=30)
            
            if response.status_code == 422:  # FastAPI validation error
                self.log_test("Bus Search Missing Params", True, 
                            "Correctly rejected missing parameters with 422 error")
            else:
                self.log_test("Bus Search Missing Params", False, 
                            f"Expected 422, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Bus Search Missing Params", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 BACKEND API TESTING STARTED")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        
        # Run all test suites
        self.test_train_search_api()
        self.test_train_autocomplete_api()
        self.test_bus_search_api()
        self.test_error_handling()
        
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
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)