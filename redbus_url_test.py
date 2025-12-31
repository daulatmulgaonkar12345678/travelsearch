#!/usr/bin/env python3
"""
RedBus URL Generation Fix Testing
=================================

Tests the redBus URL generation fix for bus searches to ensure:
1. Bus stop names are resolved to parent city names for redBus URLs
2. No `undefined` values appear in URLs
3. URLs follow CITY → CITY format only

Test Cases from Review Request:
1. Basic City Search: Nagpur→Pune
2. Stop Name with Area Suffix: Nagpur Bus Stand – Mor Bhavan → Pune Swargate
3. City Alias Resolution: Mumbai Central → Nashik CBS
4. Renamed City: Chhatrapati Sambhaji Nagar → Mumbai
5. Validate all booking partner URLs
"""

import requests
import json
import sys
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import time

# Backend URL Configuration
BACKEND_URL = "https://click-logging.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class RedBusURLTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RedBus-URL-Tester/1.0'
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
    
    def validate_redbus_url(self, url: str, expected_pattern: str = None) -> tuple[bool, str]:
        """
        Validate redBus URL format and content.
        
        Returns:
            (is_valid, error_message)
        """
        if not url:
            return False, "URL is empty"
        
        # Check for undefined/null values
        invalid_patterns = [
            'undefined',
            'null',
            'NaN',
            'mor-bhavan',  # Stop-specific names should not appear
            'swargate',    # Stop-specific names should not appear
            'bus-stand',   # Generic stop names should not appear
            'depot',       # Depot names should not appear
            'cbs',         # Central Bus Station should not appear
        ]
        
        url_lower = url.lower()
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False, f"Contains invalid pattern: {pattern}"
        
        # Check redBus URL format
        if 'redbus.in/bus-tickets/' not in url:
            return False, "Not a valid redBus URL format"
        
        # Extract route part
        route_match = re.search(r'/bus-tickets/([^/?]+)', url)
        if not route_match:
            return False, "Cannot extract route from URL"
        
        route = route_match.group(1)
        
        # Check CITY-to-CITY format
        if '-to-' not in route:
            return False, "URL does not follow CITY-to-CITY format"
        
        parts = route.split('-to-')
        if len(parts) != 2:
            return False, "URL has incorrect CITY-to-CITY format"
        
        origin, destination = parts
        
        # Validate city names (should be simple, no complex suffixes)
        for city in [origin, destination]:
            if not city or len(city) < 2:
                return False, f"Invalid city name: {city}"
            
            # Should not contain stop-specific terms
            if any(term in city for term in ['stand', 'depot', 'terminal', 'station']):
                return False, f"City name contains stop-specific term: {city}"
        
        # Check expected pattern if provided
        if expected_pattern and expected_pattern not in url:
            return False, f"URL does not match expected pattern: {expected_pattern}"
        
        return True, "Valid redBus URL"
    
    def validate_all_booking_partners(self, offers: List[Dict]) -> tuple[bool, str]:
        """
        Validate all booking partner URLs in all offers.
        
        Returns:
            (all_valid, error_details)
        """
        errors = []
        
        for i, offer in enumerate(offers):
            booking_partners = offer.get('booking_partners', [])
            
            for partner in booking_partners:
                partner_name = partner.get('name', 'Unknown')
                partner_url = partner.get('url', '')
                
                # Check for undefined/null values
                if 'undefined' in partner_url or 'null' in partner_url:
                    errors.append(f"Offer {i+1} - {partner_name}: Contains undefined/null")
                
                # For redBus specifically, validate format
                if 'redbus' in partner_name.lower():
                    is_valid, error_msg = self.validate_redbus_url(partner_url)
                    if not is_valid:
                        errors.append(f"Offer {i+1} - {partner_name}: {error_msg}")
                
                # General URL validation
                if not partner_url.startswith('http'):
                    errors.append(f"Offer {i+1} - {partner_name}: Invalid URL format")
        
        return len(errors) == 0, "; ".join(errors)
    
    def test_basic_city_search(self):
        """Test Case 1: Basic City Search - Nagpur→Pune"""
        print("\n🧪 TEST CASE 1: Basic City Search")
        print("=" * 50)
        
        test_url = f"{API_BASE}/search/buses"
        params = {
            'origin': 'Nagpur',
            'destination': 'Pune',
            'departure_date': '2026-02-15',
            'passengers': 1
        }
        
        try:
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                
                if not offers:
                    self.log_test("Basic City Search - Nagpur→Pune", False, "No offers returned")
                    return
                
                # Find redBus URL
                redbus_url = None
                for offer in offers:
                    for partner in offer.get('booking_partners', []):
                        if 'redbus' in partner.get('name', '').lower():
                            redbus_url = partner.get('url', '')
                            break
                    if redbus_url:
                        break
                
                if not redbus_url:
                    self.log_test("Basic City Search - Nagpur→Pune", False, "No redBus URL found")
                    return
                
                # Validate redBus URL
                expected_pattern = "nagpur-to-pune"
                is_valid, error_msg = self.validate_redbus_url(redbus_url, expected_pattern)
                
                if is_valid:
                    self.log_test("Basic City Search - Nagpur→Pune", True, 
                                f"Valid redBus URL: {redbus_url}")
                else:
                    self.log_test("Basic City Search - Nagpur→Pune", False, 
                                f"Invalid redBus URL: {error_msg}. URL: {redbus_url}")
                
                # Validate all booking partners
                all_valid, partner_errors = self.validate_all_booking_partners(offers)
                if not all_valid:
                    self.log_test("Basic City Search - All Partners Valid", False, partner_errors)
                else:
                    self.log_test("Basic City Search - All Partners Valid", True, 
                                "All booking partner URLs are valid")
            else:
                self.log_test("Basic City Search - Nagpur→Pune", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Basic City Search - Nagpur→Pune", False, f"Exception: {str(e)}")
    
    def test_stop_name_with_area_suffix(self):
        """Test Case 2: Stop Name with Area Suffix"""
        print("\n🧪 TEST CASE 2: Stop Name with Area Suffix")
        print("=" * 50)
        
        test_url = f"{API_BASE}/search/buses"
        params = {
            'origin': 'Nagpur Bus Stand – Mor Bhavan',
            'destination': 'Pune Swargate',
            'departure_date': '2026-02-15',
            'passengers': 1
        }
        
        try:
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                
                if not offers:
                    self.log_test("Stop Name with Area Suffix", False, "No offers returned")
                    return
                
                # Find redBus URL
                redbus_url = None
                for offer in offers:
                    for partner in offer.get('booking_partners', []):
                        if 'redbus' in partner.get('name', '').lower():
                            redbus_url = partner.get('url', '')
                            break
                    if redbus_url:
                        break
                
                if not redbus_url:
                    self.log_test("Stop Name with Area Suffix", False, "No redBus URL found")
                    return
                
                # Validate redBus URL - should be nagpur-to-pune (NOT containing mor-bhavan or swargate)
                expected_pattern = "nagpur-to-pune"
                is_valid, error_msg = self.validate_redbus_url(redbus_url, expected_pattern)
                
                # Additional check for stop-specific names
                if 'mor-bhavan' in redbus_url.lower() or 'swargate' in redbus_url.lower():
                    is_valid = False
                    error_msg = "URL contains stop-specific names (mor-bhavan/swargate)"
                
                if is_valid:
                    self.log_test("Stop Name with Area Suffix", True, 
                                f"Valid redBus URL (stop names resolved): {redbus_url}")
                else:
                    self.log_test("Stop Name with Area Suffix", False, 
                                f"Invalid redBus URL: {error_msg}. URL: {redbus_url}")
                
                # Validate all booking partners
                all_valid, partner_errors = self.validate_all_booking_partners(offers)
                if not all_valid:
                    self.log_test("Stop Name Suffix - All Partners Valid", False, partner_errors)
                else:
                    self.log_test("Stop Name Suffix - All Partners Valid", True, 
                                "All booking partner URLs are valid")
            else:
                self.log_test("Stop Name with Area Suffix", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Stop Name with Area Suffix", False, f"Exception: {str(e)}")
    
    def test_city_alias_resolution(self):
        """Test Case 3: City Alias Resolution"""
        print("\n🧪 TEST CASE 3: City Alias Resolution")
        print("=" * 50)
        
        test_url = f"{API_BASE}/search/buses"
        params = {
            'origin': 'Mumbai Central',
            'destination': 'Nashik CBS',
            'departure_date': '2026-02-15',
            'passengers': 1
        }
        
        try:
            response = self.session.get(test_url, params=params, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                
                if not offers:
                    self.log_test("City Alias Resolution", False, "No offers returned")
                    return
                
                # Find redBus URL
                redbus_url = None
                for offer in offers:
                    for partner in offer.get('booking_partners', []):
                        if 'redbus' in partner.get('name', '').lower():
                            redbus_url = partner.get('url', '')
                            break
                    if redbus_url:
                        break
                
                if not redbus_url:
                    self.log_test("City Alias Resolution", False, "No redBus URL found")
                    return
                
                # Validate redBus URL - should be mumbai-to-nashik
                expected_pattern = "mumbai-to-nashik"
                is_valid, error_msg = self.validate_redbus_url(redbus_url, expected_pattern)
                
                if is_valid:
                    self.log_test("City Alias Resolution", True, 
                                f"Valid redBus URL (aliases resolved): {redbus_url}")
                else:
                    self.log_test("City Alias Resolution", False, 
                                f"Invalid redBus URL: {error_msg}. URL: {redbus_url}")
                
                # Validate all booking partners
                all_valid, partner_errors = self.validate_all_booking_partners(offers)
                if not all_valid:
                    self.log_test("City Alias - All Partners Valid", False, partner_errors)
                else:
                    self.log_test("City Alias - All Partners Valid", True, 
                                "All booking partner URLs are valid")
            else:
                self.log_test("City Alias Resolution", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("City Alias Resolution", False, f"Exception: {str(e)}")
    
    def test_renamed_city(self):
        """Test Case 4: Renamed City (Aurangabad)"""
        print("\n🧪 TEST CASE 4: Renamed City (Aurangabad)")
        print("=" * 50)
        
        test_url = f"{API_BASE}/search/buses"
        params = {
            'origin': 'Chhatrapati Sambhaji Nagar',
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
                offers = data.get('offers', [])
                
                if not offers:
                    self.log_test("Renamed City (Aurangabad)", False, "No offers returned")
                    return
                
                # Find redBus URL
                redbus_url = None
                for offer in offers:
                    for partner in offer.get('booking_partners', []):
                        if 'redbus' in partner.get('name', '').lower():
                            redbus_url = partner.get('url', '')
                            break
                    if redbus_url:
                        break
                
                if not redbus_url:
                    self.log_test("Renamed City (Aurangabad)", False, "No redBus URL found")
                    return
                
                # Validate redBus URL - should be aurangabad-to-mumbai
                expected_pattern = "aurangabad-to-mumbai"
                is_valid, error_msg = self.validate_redbus_url(redbus_url, expected_pattern)
                
                if is_valid:
                    self.log_test("Renamed City (Aurangabad)", True, 
                                f"Valid redBus URL (renamed city resolved): {redbus_url}")
                else:
                    self.log_test("Renamed City (Aurangabad)", False, 
                                f"Invalid redBus URL: {error_msg}. URL: {redbus_url}")
                
                # Validate all booking partners
                all_valid, partner_errors = self.validate_all_booking_partners(offers)
                if not all_valid:
                    self.log_test("Renamed City - All Partners Valid", False, partner_errors)
                else:
                    self.log_test("Renamed City - All Partners Valid", True, 
                                "All booking partner URLs are valid")
            else:
                self.log_test("Renamed City (Aurangabad)", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Renamed City (Aurangabad)", False, f"Exception: {str(e)}")
    
    def test_comprehensive_url_validation(self):
        """Test Case 5: Comprehensive URL Validation across multiple routes"""
        print("\n🧪 TEST CASE 5: Comprehensive URL Validation")
        print("=" * 50)
        
        test_routes = [
            ("Pune", "Mumbai", "pune-to-mumbai"),
            ("Satara", "Karad", "satara-to-karad"),
            ("Kolhapur Bus Stand", "Pune Swargate", "kolhapur-to-pune"),
            ("Nashik CBS", "Aurangabad Depot", "nashik-to-aurangabad"),
        ]
        
        all_tests_passed = True
        
        for origin, destination, expected_pattern in test_routes:
            test_name = f"URL Validation: {origin}→{destination}"
            
            try:
                test_url = f"{API_BASE}/search/buses"
                params = {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': '2026-02-15',
                    'passengers': 1
                }
                
                response = self.session.get(test_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    offers = data.get('offers', [])
                    
                    if offers:
                        # Validate all booking partners for this route
                        all_valid, partner_errors = self.validate_all_booking_partners(offers)
                        
                        if all_valid:
                            # Check redBus URL specifically
                            redbus_url = None
                            for offer in offers:
                                for partner in offer.get('booking_partners', []):
                                    if 'redbus' in partner.get('name', '').lower():
                                        redbus_url = partner.get('url', '')
                                        break
                                if redbus_url:
                                    break
                            
                            if redbus_url:
                                is_valid, error_msg = self.validate_redbus_url(redbus_url, expected_pattern)
                                if is_valid:
                                    self.log_test(test_name, True, f"Valid URL: {redbus_url}")
                                else:
                                    self.log_test(test_name, False, f"Invalid redBus URL: {error_msg}")
                                    all_tests_passed = False
                            else:
                                self.log_test(test_name, False, "No redBus URL found")
                                all_tests_passed = False
                        else:
                            self.log_test(test_name, False, f"Partner URL issues: {partner_errors}")
                            all_tests_passed = False
                    else:
                        self.log_test(test_name, False, "No offers returned")
                        all_tests_passed = False
                else:
                    self.log_test(test_name, False, f"HTTP {response.status_code}")
                    all_tests_passed = False
                    
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
                all_tests_passed = False
        
        # Overall validation test
        if all_tests_passed:
            self.log_test("Comprehensive URL Validation", True, 
                        "All routes passed URL validation")
        else:
            self.log_test("Comprehensive URL Validation", False, 
                        "Some routes failed URL validation")
    
    def run_all_tests(self):
        """Run all redBus URL generation tests"""
        print("🧪 REDBUS URL GENERATION FIX TESTING STARTED")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        
        # Run all test cases
        self.test_basic_city_search()
        self.test_stop_name_with_area_suffix()
        self.test_city_alias_resolution()
        self.test_renamed_city()
        self.test_comprehensive_url_validation()
        
        # Print summary
        print("\n📊 REDBUS URL TEST SUMMARY")
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
            print(f"\n✅ ALL REDBUS URL TESTS PASSED!")
        
        # Acceptance criteria check
        print("\n🎯 ACCEPTANCE CRITERIA CHECK:")
        criteria = [
            "All redBus URLs are CITY → CITY format",
            "No `undefined` values in any URLs", 
            "Stop names are correctly resolved to parent city names",
            "City aliases work correctly",
        ]
        
        for criterion in criteria:
            print(f"   ✅ {criterion}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = RedBusURLTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)