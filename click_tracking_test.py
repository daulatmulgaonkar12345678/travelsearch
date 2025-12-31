#!/usr/bin/env python3
"""
Industry-Proven Click Tracking (Redirect-First Model) Testing
Testing the redirect-first, non-blocking click tracking implementation.
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import quote, unquote
import concurrent.futures
import threading

# Backend URL Configuration - Use production URL from review request
BACKEND_URL = "https://click-logging.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ClickTrackingTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Click-Tracking-Tester/1.0'
        })
        self.test_results = []
        self.failed_tests = []
        self.response_times = []
        
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
    
    def test_redirect_response_validation(self):
        """Test Redirect Response Validation - HTTP 302 and correct URL"""
        print("\n🔄 TESTING REDIRECT RESPONSE VALIDATION")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/redirect"
            target_url = "https://www.booking.com"
            params = {
                'target': quote(target_url),
                'service': 'hotel',
                'vendor': 'booking',
                'city': 'Mumbai'
            }
            
            start_time = time.time()
            response = self.session.get(test_url, params=params, timeout=10, allow_redirects=False)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {response_time:.2f}ms")
            
            # Test HTTP 302 status code
            if response.status_code == 302:
                self.log_test("Redirect - HTTP 302 Status", True, 
                            f"Correct 302 redirect status code")
            else:
                self.log_test("Redirect - HTTP 302 Status", False, 
                            f"Expected 302, got {response.status_code}")
                return
            
            # Test redirect URL is correct
            location = response.headers.get('location', '')
            if location == target_url:
                self.log_test("Redirect - Correct URL", True, 
                            f"Redirects to correct URL: {location}")
            else:
                self.log_test("Redirect - Correct URL", False, 
                            f"Expected {target_url}, got {location}")
            
            # Test response time < 50ms (target: instant redirect)
            if response_time < 50:
                self.log_test("Redirect - Response Time < 50ms", True, 
                            f"Response time: {response_time:.2f}ms (target: < 50ms)")
            else:
                self.log_test("Redirect - Response Time < 50ms", False, 
                            f"Response time: {response_time:.2f}ms (exceeds 50ms target)")
            
            self.response_times.append(response_time)
                
        except Exception as e:
            self.log_test("Redirect Response Validation", False, f"Exception: {str(e)}")

    def test_response_time_under_load(self):
        """Test Response Time Under Load - 5 consecutive calls"""
        print("\n⚡ TESTING RESPONSE TIME UNDER LOAD")
        print("=" * 50)
        
        try:
            test_url = f"{API_BASE}/redirect"
            target_url = "https://www.skyscanner.co.in"
            
            response_times = []
            all_success = True
            
            for i in range(5):
                params = {
                    'target': quote(target_url),
                    'service': 'flight',
                    'vendor': 'skyscanner',
                    'origin': 'DEL',
                    'destination': 'BOM',
                    'price': 5000 + i  # Vary price to ensure different requests
                }
                
                start_time = time.time()
                response = self.session.get(test_url, params=params, timeout=10, allow_redirects=False)
                response_time = (time.time() - start_time) * 1000
                
                response_times.append(response_time)
                print(f"   Call {i+1}: {response_time:.2f}ms - Status: {response.status_code}")
                
                if response.status_code != 302:
                    all_success = False
            
            # Test all responses < 100ms
            max_time = max(response_times)
            avg_time = sum(response_times) / len(response_times)
            
            if max_time < 100:
                self.log_test("Load Test - All Responses < 100ms", True, 
                            f"Max: {max_time:.2f}ms, Avg: {avg_time:.2f}ms")
            else:
                self.log_test("Load Test - All Responses < 100ms", False, 
                            f"Max: {max_time:.2f}ms exceeds 100ms limit")
            
            # Test no blocking behavior (all requests successful)
            if all_success:
                self.log_test("Load Test - No Blocking", True, 
                            "All 5 requests returned 302 successfully")
            else:
                self.log_test("Load Test - No Blocking", False, 
                            "Some requests failed - possible blocking detected")
                
        except Exception as e:
            self.log_test("Response Time Under Load", False, f"Exception: {str(e)}")

    def test_click_logging_verification(self):
        """Test Click Logging Verification - Background logging with all parameters"""
        print("\n📊 TESTING CLICK LOGGING VERIFICATION")
        print("=" * 50)
        
        try:
            # Make a redirect call with all parameters
            test_url = f"{API_BASE}/redirect"
            target_url = "https://www.skyscanner.co.in"
            
            unique_price = int(time.time()) % 10000  # Unique price for identification
            
            params = {
                'target': quote(target_url),
                'service': 'flight',
                'vendor': 'skyscanner',
                'origin': 'DEL',
                'destination': 'BOM',
                'price': unique_price,
                'search_type': 'CITY'
            }
            
            print(f"Making redirect call with unique price: {unique_price}")
            response = self.session.get(test_url, params=params, timeout=10, allow_redirects=False)
            
            if response.status_code == 302:
                self.log_test("Click Logging - Redirect Success", True, 
                            "Redirect call successful")
                
                # Wait for background task to complete
                print("   Waiting 3 seconds for background logging...")
                time.sleep(3)
                
                # Check click logs
                logs_url = f"{API_BASE}/admin/click-logs"
                logs_response = self.session.get(logs_url, timeout=30)
                
                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    logs = logs_data.get('logs', [])
                    
                    print(f"   Found {len(logs)} total click logs")
                    
                    # Look for our logged event
                    event_found = False
                    matching_log = None
                    
                    for log in logs:
                        if (log.get('vendor') == 'skyscanner' and 
                            log.get('service') == 'flight' and
                            log.get('origin') == 'DEL' and
                            log.get('destination') == 'BOM' and
                            log.get('price') == unique_price):
                            event_found = True
                            matching_log = log
                            break
                    
                    if event_found:
                        self.log_test("Click Logging - Event Found", True, 
                                    f"Click event found with unique price {unique_price}")
                        
                        # Verify all required fields are present
                        required_fields = ['service', 'vendor', 'origin', 'destination', 'price', 'search_type']
                        missing_fields = []
                        
                        for field in required_fields:
                            if field not in matching_log or matching_log[field] is None:
                                missing_fields.append(field)
                        
                        if not missing_fields:
                            self.log_test("Click Logging - All Fields Present", True, 
                                        f"All required fields present: {', '.join(required_fields)}")
                        else:
                            self.log_test("Click Logging - All Fields Present", False, 
                                        f"Missing fields: {', '.join(missing_fields)}")
                        
                        # Show sample log structure
                        print(f"   Sample log: {json.dumps(matching_log, indent=2)}")
                        
                    else:
                        self.log_test("Click Logging - Event Found", False, 
                                    f"Click event with unique price {unique_price} not found in logs")
                        
                        # Show recent logs for debugging
                        print("   Recent logs for debugging:")
                        for i, log in enumerate(logs[:3]):
                            print(f"     Log {i+1}: service={log.get('service')}, vendor={log.get('vendor')}, price={log.get('price')}")
                else:
                    self.log_test("Click Logging - Check Logs", False, 
                                f"Could not check logs: HTTP {logs_response.status_code}")
            else:
                self.log_test("Click Logging - Redirect Success", False, 
                            f"Redirect failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Click Logging Verification", False, f"Exception: {str(e)}")

    def test_error_resilience(self):
        """Test Error Resilience - Redirect works even with potential DB issues"""
        print("\n🛡️ TESTING ERROR RESILIENCE")
        print("=" * 50)
        
        try:
            # Test with various edge cases that might cause DB issues
            test_cases = [
                {
                    'name': 'Very Long Vendor Name',
                    'params': {
                        'target': quote('https://www.example.com'),
                        'service': 'flight',
                        'vendor': 'a' * 100,  # Very long vendor name
                        'origin': 'DEL',
                        'destination': 'BOM'
                    }
                },
                {
                    'name': 'Special Characters',
                    'params': {
                        'target': quote('https://www.example.com'),
                        'service': 'hotel',
                        'vendor': 'test-vendor',
                        'city': 'Mumbai & Delhi',  # Special characters
                        'hotel_name': 'Hotel "Test" & Spa'
                    }
                },
                {
                    'name': 'Large Price Value',
                    'params': {
                        'target': quote('https://www.example.com'),
                        'service': 'flight',
                        'vendor': 'testvendor',
                        'price': 999999999  # Very large price
                    }
                }
            ]
            
            all_redirects_work = True
            no_500_errors = True
            
            for test_case in test_cases:
                test_url = f"{API_BASE}/redirect"
                
                try:
                    response = self.session.get(test_url, params=test_case['params'], 
                                             timeout=10, allow_redirects=False)
                    
                    print(f"   {test_case['name']}: Status {response.status_code}")
                    
                    if response.status_code != 302:
                        all_redirects_work = False
                    
                    if response.status_code == 500:
                        no_500_errors = False
                        
                except Exception as e:
                    print(f"   {test_case['name']}: Exception {str(e)}")
                    all_redirects_work = False
            
            if all_redirects_work:
                self.log_test("Error Resilience - Redirects Work", True, 
                            "All edge case redirects returned 302")
            else:
                self.log_test("Error Resilience - Redirects Work", False, 
                            "Some edge case redirects failed")
            
            if no_500_errors:
                self.log_test("Error Resilience - No 500 Errors", True, 
                            "No 500 errors from redirect endpoint")
            else:
                self.log_test("Error Resilience - No 500 Errors", False, 
                            "500 errors detected from redirect endpoint")
                
        except Exception as e:
            self.log_test("Error Resilience", False, f"Exception: {str(e)}")

    def test_service_type_normalization(self):
        """Test Service Type Normalization - flights->flight, buses->bus"""
        print("\n🔄 TESTING SERVICE TYPE NORMALIZATION")
        print("=" * 50)
        
        try:
            test_cases = [
                {'service': 'flights', 'expected': 'flight'},
                {'service': 'buses', 'expected': 'bus'},
                {'service': 'flight', 'expected': 'flight'},
                {'service': 'bus', 'expected': 'bus'}
            ]
            
            all_normalized = True
            
            for test_case in test_cases:
                test_url = f"{API_BASE}/redirect"
                target_url = "https://www.example.com"
                
                unique_price = int(time.time() * 1000) % 100000  # Unique identifier
                
                params = {
                    'target': quote(target_url),
                    'service': test_case['service'],
                    'vendor': 'testvendor',
                    'price': unique_price
                }
                
                response = self.session.get(test_url, params=params, timeout=10, allow_redirects=False)
                
                if response.status_code == 302:
                    # Wait for logging
                    time.sleep(1)
                    
                    # Check if service was normalized in logs
                    logs_url = f"{API_BASE}/admin/click-logs"
                    logs_response = self.session.get(logs_url, timeout=30)
                    
                    if logs_response.status_code == 200:
                        logs_data = logs_response.json()
                        logs = logs_data.get('logs', [])
                        
                        # Find our log entry
                        found_log = None
                        for log in logs:
                            if log.get('price') == unique_price and log.get('vendor') == 'testvendor':
                                found_log = log
                                break
                        
                        if found_log:
                            logged_service = found_log.get('service')
                            expected_service = test_case['expected']
                            
                            print(f"   {test_case['service']} -> {logged_service} (expected: {expected_service})")
                            
                            if logged_service != expected_service:
                                all_normalized = False
                        else:
                            print(f"   {test_case['service']}: Log entry not found")
                            all_normalized = False
                else:
                    print(f"   {test_case['service']}: Redirect failed ({response.status_code})")
                    all_normalized = False
            
            if all_normalized:
                self.log_test("Service Normalization", True, 
                            "All service types normalized correctly")
            else:
                self.log_test("Service Normalization", False, 
                            "Service type normalization issues detected")
                
        except Exception as e:
            self.log_test("Service Type Normalization", False, f"Exception: {str(e)}")

    def test_health_endpoint(self):
        """Test Health Endpoint - buffer_size and last_click"""
        print("\n🏥 TESTING HEALTH ENDPOINT")
        print("=" * 50)
        
        try:
            health_url = f"{API_BASE}/redirect/health"
            response = self.session.get(health_url, timeout=30)
            
            print(f"Request URL: {health_url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'buffer_size']
                missing_fields = []
                
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log_test("Health Endpoint - Required Fields", True, 
                                f"All required fields present: {', '.join(required_fields)}")
                    
                    # Check buffer_size is a number
                    buffer_size = data.get('buffer_size')
                    if isinstance(buffer_size, int) and buffer_size >= 0:
                        self.log_test("Health Endpoint - Buffer Size", True, 
                                    f"Buffer size: {buffer_size}")
                    else:
                        self.log_test("Health Endpoint - Buffer Size", False, 
                                    f"Invalid buffer size: {buffer_size}")
                    
                    # Check last_click (optional but should be valid if present)
                    last_click = data.get('last_click')
                    if last_click is None or isinstance(last_click, dict):
                        self.log_test("Health Endpoint - Last Click", True, 
                                    "Last click field valid")
                    else:
                        self.log_test("Health Endpoint - Last Click", False, 
                                    f"Invalid last_click format: {type(last_click)}")
                    
                    print(f"   Health data: {json.dumps(data, indent=2)}")
                    
                else:
                    self.log_test("Health Endpoint - Required Fields", False, 
                                f"Missing fields: {', '.join(missing_fields)}")
            else:
                self.log_test("Health Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Exception: {str(e)}")

    def test_concurrent_redirects(self):
        """Test Multiple Concurrent Redirects - No blocking"""
        print("\n🚀 TESTING CONCURRENT REDIRECTS")
        print("=" * 50)
        
        def make_redirect_call(call_id):
            """Make a single redirect call"""
            try:
                test_url = f"{API_BASE}/redirect"
                target_url = f"https://www.example{call_id}.com"
                
                params = {
                    'target': quote(target_url),
                    'service': 'flight',
                    'vendor': f'vendor{call_id}',
                    'origin': 'DEL',
                    'destination': 'BOM',
                    'price': 5000 + call_id
                }
                
                start_time = time.time()
                response = self.session.get(test_url, params=params, timeout=10, allow_redirects=False)
                response_time = (time.time() - start_time) * 1000
                
                return {
                    'call_id': call_id,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 302
                }
            except Exception as e:
                return {
                    'call_id': call_id,
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                }
        
        try:
            # Make 5 concurrent redirect calls
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_redirect_call, i) for i in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_calls = [r for r in results if r['success']]
            response_times = [r['response_time'] for r in successful_calls]
            
            print(f"   Successful calls: {len(successful_calls)}/5")
            if response_times:
                print(f"   Response times: {[f'{t:.2f}ms' for t in response_times]}")
                print(f"   Max response time: {max(response_times):.2f}ms")
                print(f"   Avg response time: {sum(response_times)/len(response_times):.2f}ms")
            
            # Test all calls successful (no blocking)
            if len(successful_calls) == 5:
                self.log_test("Concurrent Redirects - No Blocking", True, 
                            "All 5 concurrent calls successful")
            else:
                self.log_test("Concurrent Redirects - No Blocking", False, 
                            f"Only {len(successful_calls)}/5 calls successful")
            
            # Test response times reasonable
            if response_times and max(response_times) < 200:
                self.log_test("Concurrent Redirects - Response Times", True, 
                            f"Max response time: {max(response_times):.2f}ms")
            else:
                self.log_test("Concurrent Redirects - Response Times", False, 
                            f"Response times too high or no successful calls")
                
        except Exception as e:
            self.log_test("Concurrent Redirects", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all click tracking tests"""
        print("🧪 INDUSTRY-PROVEN CLICK TRACKING TESTING STARTED")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 70)
        
        # Run all test suites
        self.test_redirect_response_validation()
        self.test_response_time_under_load()
        self.test_click_logging_verification()
        self.test_error_resilience()
        self.test_service_type_normalization()
        self.test_health_endpoint()
        self.test_concurrent_redirects()
        
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
        
        # Response time analysis
        if self.response_times:
            print(f"\n⚡ RESPONSE TIME ANALYSIS")
            print(f"Average: {sum(self.response_times)/len(self.response_times):.2f}ms")
            print(f"Max: {max(self.response_times):.2f}ms")
            print(f"Min: {min(self.response_times):.2f}ms")
            print(f"Target: < 50ms")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   - {test}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = ClickTrackingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)