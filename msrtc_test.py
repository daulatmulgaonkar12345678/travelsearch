#!/usr/bin/env python3
"""
MSRTC API Testing Suite
Tests the newly implemented MSRTC scraper API endpoints.

Test Coverage:
1. Bus Types API - GET /api/msrtc/bus-types
2. Stops API - GET /api/msrtc/stops with filters
3. Routes API - GET /api/msrtc/routes with phase filters
4. Search API - POST /api/msrtc/search with various scenarios
5. Variant-level data verification
6. Marathi input support
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# API Base URL - using production URL from frontend config
API_BASE_URL = "https://booking-ux-polish.preview.emergentagent.com/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test_header(test_name: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}🧪 {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.END}")

def make_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
    """Make HTTP request and return response data"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print_info(f"{method.upper()} {endpoint} -> Status: {response.status_code}")
        
        if response.status_code == 200:
            return {"success": True, "data": response.json(), "status_code": response.status_code}
        else:
            return {"success": False, "error": response.text, "status_code": response.status_code}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "status_code": 0}

def test_bus_types_api():
    """Test 1: Bus Types API - GET /api/msrtc/bus-types"""
    print_test_header("Test 1: MSRTC Bus Types API")
    
    result = make_request("GET", "/msrtc/bus-types")
    
    if not result["success"]:
        print_error(f"API request failed: {result['error']}")
        return False
    
    bus_types = result["data"]
    
    # Verify we have 6 bus types
    if len(bus_types) != 6:
        print_error(f"Expected 6 bus types, got {len(bus_types)}")
        return False
    
    print_success(f"Found {len(bus_types)} bus types")
    
    # Verify required fields for each bus type
    required_fields = ["code", "name_marathi", "name_english", "is_ac", "is_sleeper", "fare_multiplier"]
    expected_codes = ["ST", "SEMI_LUX", "ASIAD", "SHIVNERI", "SHIVSHAHI", "ASHWAMEDH"]
    
    found_codes = []
    for bus_type in bus_types:
        # Check required fields
        for field in required_fields:
            if field not in bus_type:
                print_error(f"Missing field '{field}' in bus type: {bus_type}")
                return False
        
        found_codes.append(bus_type["code"])
        print_info(f"Bus Type: {bus_type['code']} - {bus_type['name_english']} ({bus_type['name_marathi']}) - AC: {bus_type['is_ac']}, Sleeper: {bus_type['is_sleeper']}, Multiplier: {bus_type['fare_multiplier']}")
    
    # Verify all expected codes are present
    for code in expected_codes:
        if code not in found_codes:
            print_error(f"Missing expected bus type code: {code}")
            return False
    
    print_success("All bus types have required fields and expected codes")
    return True

def test_stops_api():
    """Test 2: Stops API - GET /api/msrtc/stops"""
    print_test_header("Test 2: MSRTC Stops API")
    
    # Test 2a: Get all stops
    print_info("Testing: Get all stops")
    result = make_request("GET", "/msrtc/stops")
    
    if not result["success"]:
        print_error(f"API request failed: {result['error']}")
        return False
    
    all_stops = result["data"]
    
    # Verify we have 17 stops
    if len(all_stops) != 17:
        print_error(f"Expected 17 stops, got {len(all_stops)}")
        return False
    
    print_success(f"Found {len(all_stops)} stops")
    
    # Verify required fields for each stop
    required_fields = ["value", "name_marathi", "name_english", "name_normalized", "stop_type", "district"]
    
    for stop in all_stops:
        for field in required_fields:
            if field not in stop:
                print_error(f"Missing field '{field}' in stop: {stop}")
                return False
    
    print_success("All stops have required fields")
    
    # Test 2b: Filter by query - Pune
    print_info("Testing: Filter by query 'pune'")
    result = make_request("GET", "/msrtc/stops", params={"query": "pune"})
    
    if not result["success"]:
        print_error(f"Query filter failed: {result['error']}")
        return False
    
    pune_stops = result["data"]
    
    # Should return Pune stops (PUNE and PUNE_SL)
    if len(pune_stops) < 1:
        print_error(f"Expected at least 1 Pune stop, got {len(pune_stops)}")
        return False
    
    print_success(f"Found {len(pune_stops)} Pune stops")
    
    # Verify Pune stops contain "pune" in name
    for stop in pune_stops:
        if "pune" not in stop["name_english"].lower() and "pune" not in stop["name_normalized"]:
            print_error(f"Stop doesn't match 'pune' query: {stop}")
            return False
    
    # Test 2c: Filter by stop_type - major
    print_info("Testing: Filter by stop_type 'major'")
    result = make_request("GET", "/msrtc/stops", params={"stop_type": "major"})
    
    if not result["success"]:
        print_error(f"Stop type filter failed: {result['error']}")
        return False
    
    major_stops = result["data"]
    
    # Should return only major stops
    if len(major_stops) == 0:
        print_error("Expected at least 1 major stop")
        return False
    
    print_success(f"Found {len(major_stops)} major stops")
    
    # Verify all returned stops are major
    for stop in major_stops:
        if stop["stop_type"] != "major":
            print_error(f"Non-major stop returned: {stop}")
            return False
    
    print_success("Stops API tests passed")
    return True

def test_routes_api():
    """Test 3: Routes API - GET /api/msrtc/routes"""
    print_test_header("Test 3: MSRTC Routes API")
    
    # Test 3a: Get all routes
    print_info("Testing: Get all routes")
    result = make_request("GET", "/msrtc/routes")
    
    if not result["success"]:
        print_error(f"API request failed: {result['error']}")
        return False
    
    all_routes = result["data"]
    
    # Should return 14+ routes (Phase 1 + Phase 2)
    if len(all_routes) < 14:
        print_error(f"Expected at least 14 routes, got {len(all_routes)}")
        return False
    
    print_success(f"Found {len(all_routes)} total routes")
    
    # Verify required fields for each route
    required_fields = ["route_id", "origin_english", "origin_marathi", "destination_english", "destination_marathi", "distance_km", "base_fare", "bus_types"]
    
    for route in all_routes:
        for field in required_fields:
            if field not in route:
                print_error(f"Missing field '{field}' in route: {route}")
                return False
    
    print_success("All routes have required fields")
    
    # Test 3b: Filter by phase 1
    print_info("Testing: Filter by phase=1")
    result = make_request("GET", "/msrtc/routes", params={"phase": 1})
    
    if not result["success"]:
        print_error(f"Phase filter failed: {result['error']}")
        return False
    
    phase1_routes = result["data"]
    
    # Should return only Phase 1 routes (10 routes: 5 bidirectional pairs)
    if len(phase1_routes) != 10:
        print_error(f"Expected 10 Phase 1 routes, got {len(phase1_routes)}")
        return False
    
    print_success(f"Found {len(phase1_routes)} Phase 1 routes")
    
    # Verify Phase 1 routes include Pune-Mumbai
    pune_mumbai_found = False
    for route in phase1_routes:
        if ("pune" in route["origin_english"].lower() and "mumbai" in route["destination_english"].lower()) or \
           ("mumbai" in route["origin_english"].lower() and "pune" in route["destination_english"].lower()):
            pune_mumbai_found = True
            print_info(f"Found Pune-Mumbai route: {route['route_id']}")
            break
    
    if not pune_mumbai_found:
        print_error("Pune-Mumbai route not found in Phase 1")
        return False
    
    print_success("Routes API tests passed")
    return True

def test_search_api():
    """Test 4: Search API - POST /api/msrtc/search"""
    print_test_header("Test 4: MSRTC Search API")
    
    # Get tomorrow's date for testing
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Test 4a: Valid search - Pune to Mumbai
    print_info("Testing: Valid search Pune → Mumbai")
    search_data = {
        "origin": "Pune",
        "destination": "Mumbai", 
        "departure_date": tomorrow
    }
    
    result = make_request("POST", "/msrtc/search", data=search_data)
    
    if not result["success"]:
        print_error(f"Search API failed: {result['error']}")
        return False
    
    search_response = result["data"]
    
    # Verify response structure
    required_fields = ["offers", "search_id", "origin", "destination", "departure_date", "is_msrtc"]
    for field in required_fields:
        if field not in search_response:
            print_error(f"Missing field '{field}' in search response")
            return False
    
    offers = search_response["offers"]
    
    # Should return 5 offers (one per bus type for Pune-Mumbai route)
    if len(offers) != 5:
        print_error(f"Expected 5 offers for Pune-Mumbai, got {len(offers)}")
        return False
    
    print_success(f"Found {len(offers)} offers for Pune → Mumbai")
    
    # Test 4b: Verify variant-level data
    print_info("Testing: Variant-level offer verification")
    
    bus_types_found = set()
    for offer in offers:
        # Verify required offer fields
        offer_fields = ["offer_id", "bus_type_label", "avg_price", "is_ac", "is_sleeper", "booking_partners"]
        for field in offer_fields:
            if field not in offer:
                print_error(f"Missing field '{field}' in offer: {offer}")
                return False
        
        # Verify booking partners
        booking_partners = offer["booking_partners"]
        if len(booking_partners) != 3:
            print_error(f"Expected 3 booking partners, got {len(booking_partners)}")
            return False
        
        expected_partners = ["MSRTC Official", "redBus", "AbhiBus"]
        found_partners = [p["name"] for p in booking_partners]
        for partner in expected_partners:
            if partner not in found_partners:
                print_error(f"Missing booking partner: {partner}")
                return False
        
        # Verify different bus types
        bus_types_found.add(offer["bus_type_label"])
        
        # Verify price is different based on fare multiplier
        if offer["avg_price"] <= 0:
            print_error(f"Invalid price: {offer['avg_price']}")
            return False
        
        print_info(f"Offer: {offer['bus_type_label']} - ₹{offer['avg_price']} - AC: {offer['is_ac']}, Sleeper: {offer['is_sleeper']}")
    
    # Should have 5 different bus types
    if len(bus_types_found) != 5:
        print_error(f"Expected 5 different bus types, got {len(bus_types_found)}")
        return False
    
    print_success("Variant-level data verification passed")
    
    # Test 4c: Marathi input support
    print_info("Testing: Marathi input support")
    marathi_search_data = {
        "origin": "पुणे",
        "destination": "मुंबई",
        "departure_date": tomorrow
    }
    
    result = make_request("POST", "/msrtc/search", data=marathi_search_data)
    
    if not result["success"]:
        print_error(f"Marathi search failed: {result['error']}")
        return False
    
    marathi_response = result["data"]
    marathi_offers = marathi_response["offers"]
    
    # Should return same 5 offers as English search
    if len(marathi_offers) != 5:
        print_error(f"Expected 5 offers for Marathi search, got {len(marathi_offers)}")
        return False
    
    print_success("Marathi input support working")
    
    # Test 4d: Validation tests
    print_info("Testing: Input validation")
    
    # Past date validation
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    past_search = {
        "origin": "Pune",
        "destination": "Mumbai",
        "departure_date": past_date
    }
    
    result = make_request("POST", "/msrtc/search", data=past_search)
    if result["success"] or result["status_code"] != 400:
        print_error("Past date validation failed - should return 400 error")
        return False
    
    print_success("Past date validation working")
    
    # Same origin/destination validation
    same_search = {
        "origin": "Pune",
        "destination": "Pune",
        "departure_date": tomorrow
    }
    
    result = make_request("POST", "/msrtc/search", data=same_search)
    if result["success"] or result["status_code"] != 400:
        print_error("Same origin/destination validation failed - should return 400 error")
        return False
    
    print_success("Same origin/destination validation working")
    
    # Test 4e: Invalid route
    print_info("Testing: Invalid route handling")
    invalid_search = {
        "origin": "Delhi",
        "destination": "Chennai",
        "departure_date": tomorrow
    }
    
    result = make_request("POST", "/msrtc/search", data=invalid_search)
    
    if not result["success"]:
        print_error(f"Invalid route search failed: {result['error']}")
        return False
    
    invalid_response = result["data"]
    
    # Should return empty offers with message
    if len(invalid_response["offers"]) != 0:
        print_error(f"Expected 0 offers for invalid route, got {len(invalid_response['offers'])}")
        return False
    
    if "message" not in invalid_response:
        print_error("Missing message for invalid route")
        return False
    
    print_success("Invalid route handling working")
    
    print_success("Search API tests passed")
    return True

def test_origin_destination_with_marathi_names():
    """Test 5: Verify origin/destination contain Marathi names in station_name"""
    print_test_header("Test 5: Marathi Station Names Verification")
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    search_data = {
        "origin": "Pune",
        "destination": "Mumbai",
        "departure_date": tomorrow
    }
    
    result = make_request("POST", "/msrtc/search", data=search_data)
    
    if not result["success"]:
        print_error(f"Search API failed: {result['error']}")
        return False
    
    offers = result["data"]["offers"]
    
    for offer in offers:
        # Check if station names contain Marathi text
        from_station = offer.get("from_station_name", "")
        to_station = offer.get("to_station_name", "")
        
        # Verify Marathi characters are present
        has_marathi_from = any(ord(char) > 127 for char in from_station)
        has_marathi_to = any(ord(char) > 127 for char in to_station)
        
        if not has_marathi_from:
            print_error(f"From station missing Marathi name: {from_station}")
            return False
        
        if not has_marathi_to:
            print_error(f"To station missing Marathi name: {to_station}")
            return False
        
        print_info(f"Station names: {from_station} → {to_station}")
    
    print_success("Marathi station names verification passed")
    return True

def run_all_tests():
    """Run all MSRTC API tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🚌 MSRTC API Testing Suite")
    print("=" * 60)
    print(f"{Colors.END}")
    
    tests = [
        ("Bus Types API", test_bus_types_api),
        ("Stops API", test_stops_api),
        ("Routes API", test_routes_api),
        ("Search API", test_search_api),
        ("Marathi Station Names", test_origin_destination_with_marathi_names),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print_success(f"{test_name} - PASSED")
            else:
                failed += 1
                print_error(f"{test_name} - FAILED")
        except Exception as e:
            failed += 1
            print_error(f"{test_name} - ERROR: {str(e)}")
    
    # Final summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}📊 TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! ({passed}/{passed + failed}){Colors.END}")
        return True
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ TESTS FAILED: {failed}/{passed + failed}{Colors.END}")
        print(f"{Colors.GREEN}✅ Tests passed: {passed}{Colors.END}")
        print(f"{Colors.RED}❌ Tests failed: {failed}{Colors.END}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)