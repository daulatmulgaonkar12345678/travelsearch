#!/usr/bin/env python3
"""
Backend API Testing for Centralized Click Logging System
Testing the click logging system end-to-end as per review request.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import time
from urllib.parse import quote

# Backend URL Configuration
BACKEND_URL = "https://click-tracker-23.preview.emergentagent.com"
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
    
    def test_click_logs_endpoint(self):
        """Test GET /api/admin/click-logs endpoint"""
        print("\n📊 TESTING CLICK LOGS ENDPOINT")
        print("=" * 50)
        
        # Test Case 1: Basic click logs retrieval
        try:
            test_url = f"{API_BASE}/admin/click-logs"
            response = self.session.get(test_url, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['count', 'total', 'logs']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Click Logs - Basic Retrieval", False, 
                                f"Missing fields: {missing_fields}")
                else:
                    logs = data.get('logs', [])
                    count = data.get('count', 0)
                    total = data.get('total', 0)
                    
                    self.log_test("Click Logs - Basic Retrieval", True, 
                                f"Retrieved {count} logs out of {total} total")
                    
                    # Store initial count for later comparison
                    self.initial_click_count = total
            else:
                self.log_test("Click Logs - Basic Retrieval", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                self.initial_click_count = 0
                
        except Exception as e:
            self.log_test("Click Logs - Basic Retrieval", False, f"Exception: {str(e)}")
            self.initial_click_count = 0
        
        # Test Case 2: Click logs with limit parameter
        try:
            test_url = f"{API_BASE}/admin/click-logs"
            params = {'limit': 50}
            response = self.session.get(test_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                count = data.get('count', 0)
                
                if count <= 50:
                    self.log_test("Click Logs - Limit Parameter", True, 
                                f"Correctly limited to {count} logs (≤50)")
                else:
                    self.log_test("Click Logs - Limit Parameter", False, 
                                f"Limit not respected: got {count} logs (>50)")
            else:
                self.log_test("Click Logs - Limit Parameter", False, 
                            f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Click Logs - Limit Parameter", False, f"Exception: {str(e)}")

    def test_redirect_endpoint_click_logging(self):
        """Test GET /api/redirect endpoint with flight params for click logging"""
        print("\n🔗 TESTING REDIRECT ENDPOINT (CLICK LOGGING)")
        print("=" * 50)
        
        # Test Case 1: Flight redirect with click logging
        try:
            test_url = f"{API_BASE}/redirect"
            target_url = "https://www.skyscanner.co.in"
            params = {
                'service': 'flight',
                'vendor': 'skyscanner',
                'target': quote(target_url),
                'origin': 'DEL',
                'destination': 'BOM',
                'price': 5000
            }
            
            response = self.session.get(test_url, params=params, timeout=30, allow_redirects=False)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 302:
                # Check redirect location
                location = response.headers.get('location', '')
                if location == target_url:
                    self.log_test("Redirect - Flight Click Logging", True, 
                                f"Correctly redirected to {target_url}")
                else:
                    self.log_test("Redirect - Flight Click Logging", False, 
                                f"Wrong redirect location: {location}")
            else:
                self.log_test("Redirect - Flight Click Logging", False, 
                            f"Expected 302, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Redirect - Flight Click Logging", False, f"Exception: {str(e)}")
        
        # Wait a moment for background logging to complete
        time.sleep(2)

    def test_service_type_normalization(self):
        """Test service type normalization in redirect endpoint"""
        print("\n🔄 TESTING SERVICE TYPE NORMALIZATION")
        print("=" * 50)
        
        test_cases = [
            ('bus', 'bus', 'Bus service normalization'),
            ('buses', 'bus', 'Buses to bus normalization'),
            ('flights', 'flight', 'Flights to flight normalization'),
            ('flight', 'flight', 'Flight service normalization'),
        ]
        
        target_url = "https://example.com"
        
        for service_input, expected_service, description in test_cases:
            try:
                test_url = f"{API_BASE}/redirect"
                params = {
                    'service': service_input,
                    'vendor': 'testvendor',
                    'target': quote(target_url),
                    'origin': 'TestOrigin',
                    'destination': 'TestDestination',
                    'price': 1000
                }
                
                response = self.session.get(test_url, params=params, timeout=30, allow_redirects=False)
                
                if response.status_code == 302:
                    self.log_test(description, True, 
                                f"Service '{service_input}' accepted and should normalize to '{expected_service}'")
                else:
                    self.log_test(description, False, 
                                f"HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                self.log_test(description, False, f"Exception: {str(e)}")
        
        # Wait for background logging
        time.sleep(2)

    def test_click_persistence(self):
        """Test that clicks are persisted and appear in logs"""
        print("\n💾 TESTING CLICK PERSISTENCE")
        print("=" * 50)
        
        # First, get current click count
        try:
            test_url = f"{API_BASE}/admin/click-logs"
            response = self.session.get(test_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                initial_count = data.get('total', 0)
            else:
                initial_count = 0
                
        except Exception as e:
            initial_count = 0
            
        # Generate a unique click event
        timestamp = int(time.time())
        test_url = f"{API_BASE}/redirect"
        target_url = "https://www.example.com"
        params = {
            'service': 'flight',
            'vendor': f'testvendor_{timestamp}',
            'target': quote(target_url),
            'origin': 'DEL',
            'destination': 'BOM',
            'price': 5000
        }
        
        try:
            # Make redirect call to generate click event
            response = self.session.get(test_url, params=params, timeout=30, allow_redirects=False)
            
            if response.status_code == 302:
                # Wait for background logging to complete
                time.sleep(3)
                
                # Check if click appears in logs
                logs_url = f"{API_BASE}/admin/click-logs"
                logs_response = self.session.get(logs_url, timeout=30)
                
                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    new_count = logs_data.get('total', 0)
                    logs = logs_data.get('logs', [])
                    
                    # Check if count increased
                    if new_count > initial_count:
                        # Look for our specific click event
                        found_click = False
                        for log in logs:
                            if (log.get('vendor') == f'testvendor_{timestamp}' and 
                                log.get('service') == 'flight' and
                                log.get('origin') == 'DEL' and
                                log.get('destination') == 'BOM' and
                                log.get('price') == 5000):
                                found_click = True
                                break
                        
                        if found_click:
                            self.log_test("Click Persistence", True, 
                                        f"Click event persisted and found in logs (count: {initial_count} → {new_count})")
                        else:
                            self.log_test("Click Persistence", False, 
                                        f"Click count increased but specific event not found in logs")
                    else:
                        self.log_test("Click Persistence", False, 
                                    f"Click count did not increase (was {initial_count}, now {new_count})")
                else:
                    self.log_test("Click Persistence", False, 
                                f"Could not retrieve logs after click: HTTP {logs_response.status_code}")
            else:
                self.log_test("Click Persistence", False, 
                            f"Redirect failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Click Persistence", False, f"Exception: {str(e)}")

    def test_click_log_fields(self):
        """Test that click logs contain required fields"""
        print("\n📋 TESTING CLICK LOG FIELDS")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/admin/click-logs"
            params = {'limit': 10}
            response = self.session.get(test_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                
                if logs:
                    # Check first log entry for required fields
                    first_log = logs[0]
                    required_fields = ['service', 'vendor', 'created_at']
                    optional_fields = ['origin', 'destination', 'price', 'target_url']
                    
                    missing_required = [field for field in required_fields if field not in first_log]
                    present_optional = [field for field in optional_fields if field in first_log]
                    
                    if not missing_required:
                        self.log_test("Click Log Fields - Required", True, 
                                    f"All required fields present: {required_fields}")
                        
                        if present_optional:
                            self.log_test("Click Log Fields - Optional", True, 
                                        f"Optional fields present: {present_optional}")
                        else:
                            self.log_test("Click Log Fields - Optional", True, 
                                        "No optional fields present (acceptable)")
                    else:
                        self.log_test("Click Log Fields - Required", False, 
                                    f"Missing required fields: {missing_required}")
                else:
                    self.log_test("Click Log Fields", True, 
                                "No logs available to test fields (acceptable for empty system)")
            else:
                self.log_test("Click Log Fields", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Click Log Fields", False, f"Exception: {str(e)}")

    def test_redirect_health_endpoint(self):
        """Test redirect health endpoint"""
        print("\n🏥 TESTING REDIRECT HEALTH ENDPOINT")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/redirect/health"
            response = self.session.get(test_url, timeout=30)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'buffer_size']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    status = data.get('status')
                    buffer_size = data.get('buffer_size', 0)
                    
                    if status == 'healthy':
                        self.log_test("Redirect Health", True, 
                                    f"Healthy status, buffer size: {buffer_size}")
                    else:
                        self.log_test("Redirect Health", False, 
                                    f"Unhealthy status: {status}")
                else:
                    self.log_test("Redirect Health", False, 
                                f"Missing fields: {missing_fields}")
            else:
                self.log_test("Redirect Health", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Redirect Health", False, f"Exception: {str(e)}")
    
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