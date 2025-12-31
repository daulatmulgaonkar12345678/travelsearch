#!/usr/bin/env python3
"""
Quick local test for the fixed click tracking system
"""

import requests
import time
from urllib.parse import quote

# Test locally
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

def test_response_time():
    """Test response time"""
    test_url = f"{API_BASE}/redirect"
    target_url = "https://www.booking.com"
    params = {
        'target': quote(target_url),
        'service': 'hotel',
        'vendor': 'booking',
        'city': 'Mumbai'
    }
    
    start_time = time.time()
    response = requests.get(test_url, params=params, timeout=10, allow_redirects=False)
    response_time = (time.time() - start_time) * 1000
    
    print(f"Response Time: {response_time:.2f}ms (Status: {response.status_code})")
    return response_time < 50, response_time

def test_service_normalization():
    """Test service normalization"""
    test_cases = [
        {'service': 'flights', 'expected': 'flight'},
        {'service': 'buses', 'expected': 'bus'},
        {'service': 'flight', 'expected': 'flight'},
        {'service': 'bus', 'expected': 'bus'}
    ]
    
    results = []
    
    for test_case in test_cases:
        test_url = f"{API_BASE}/redirect"
        target_url = "https://www.example.com"
        
        unique_price = int(time.time() * 1000) % 100000
        
        params = {
            'target': quote(target_url),
            'service': test_case['service'],
            'vendor': 'testvendor',
            'price': unique_price
        }
        
        response = requests.get(test_url, params=params, timeout=10, allow_redirects=False)
        
        if response.status_code == 302:
            time.sleep(1)  # Wait for logging
            
            logs_url = f"{API_BASE}/admin/click-logs"
            logs_response = requests.get(logs_url, timeout=30)
            
            if logs_response.status_code == 200:
                logs_data = logs_response.json()
                logs = logs_data.get('logs', [])
                
                found_log = None
                for log in logs:
                    if log.get('price') == unique_price and log.get('vendor') == 'testvendor':
                        found_log = log
                        break
                
                if found_log:
                    logged_service = found_log.get('service')
                    expected_service = test_case['expected']
                    
                    success = logged_service == expected_service
                    print(f"{test_case['service']} -> {logged_service} (expected: {expected_service}) {'✅' if success else '❌'}")
                    results.append(success)
                else:
                    print(f"{test_case['service']}: Log entry not found ❌")
                    results.append(False)
            else:
                print(f"{test_case['service']}: Could not check logs ❌")
                results.append(False)
        else:
            print(f"{test_case['service']}: Redirect failed ({response.status_code}) ❌")
            results.append(False)
    
    return all(results)

if __name__ == "__main__":
    print("🧪 QUICK LOCAL CLICK TRACKING TEST")
    print("=" * 40)
    
    # Test response time
    print("\n⚡ Response Time Test:")
    time_ok, response_time = test_response_time()
    
    # Test service normalization
    print("\n🔄 Service Normalization Test:")
    norm_ok = test_service_normalization()
    
    print(f"\n📊 Results:")
    print(f"Response Time < 50ms: {'✅' if time_ok else '❌'} ({response_time:.2f}ms)")
    print(f"Service Normalization: {'✅' if norm_ok else '❌'}")
    
    if time_ok and norm_ok:
        print("\n✅ ALL LOCAL TESTS PASSED!")
    else:
        print("\n❌ Some tests failed")