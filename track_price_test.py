#!/usr/bin/env python3
"""
Track Price System Testing
==========================
Tests the Track Price and Refresh Live Price functionality as requested.

Endpoints to Test:
1. GET /api/track-price/status
2. POST /api/track-price/check-all  
3. POST /api/track-price/check-single
4. GET /api/saved-searches (prerequisite)
5. GET /api/internal/search-stats

Validation:
- price_drop_threshold_percent should be 5.0
- min_price_drop_amount should be 500
- Background job should start without errors
- Single search check should return current_price, previous_price, price_changed status
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Backend URL - using localhost as per system setup
BACKEND_URL = "http://localhost:8001"

class TrackPriceTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.test_email = "trackprice@example.com"
        self.saved_search_id = None
        
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
    
    async def setup_saved_search(self):
        """Create a saved search for testing track price functionality"""
        try:
            payload = {
                "email": self.test_email,
                "search": {
                    "origin": "DEL",
                    "destination": "BOM",
                    "departure_date": "2026-02-20",
                    "adults": 1,
                    "cabin_class": "economy",
                    "trip_type": "oneway"
                },
                "last_known_price": 8500,
                "last_known_currency": "INR"
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/saved-searches",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.saved_search_id = data.get("id")
                self.log_result(
                    "Setup Saved Search",
                    True,
                    f"Created saved search with ID: {self.saved_search_id}"
                )
                return True
            else:
                self.log_result(
                    "Setup Saved Search",
                    False,
                    f"Failed to create saved search: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Setup Saved Search", False, f"Exception: {str(e)}")
            return False
    
    async def test_track_price_status(self):
        """Test GET /api/track-price/status"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/track-price/status")
            
            if response.status_code != 200:
                self.log_result(
                    "Track Price Status",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = [
                "status", "active_searches_future", "active_searches_total",
                "price_drop_threshold_percent", "min_price_drop_amount", "recent_alerts"
            ]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Track Price Status",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Validate specific values as per requirements
            if data.get("price_drop_threshold_percent") != 5.0:
                self.log_result(
                    "Track Price Status",
                    False,
                    f"Expected price_drop_threshold_percent=5.0, got {data.get('price_drop_threshold_percent')}",
                    data
                )
                return False
            
            if data.get("min_price_drop_amount") != 500:
                self.log_result(
                    "Track Price Status",
                    False,
                    f"Expected min_price_drop_amount=500, got {data.get('min_price_drop_amount')}",
                    data
                )
                return False
            
            # Check data types
            if not isinstance(data.get("active_searches_future"), int):
                self.log_result(
                    "Track Price Status",
                    False,
                    f"active_searches_future should be int, got {type(data.get('active_searches_future'))}",
                    data
                )
                return False
            
            if not isinstance(data.get("active_searches_total"), int):
                self.log_result(
                    "Track Price Status",
                    False,
                    f"active_searches_total should be int, got {type(data.get('active_searches_total'))}",
                    data
                )
                return False
            
            if not isinstance(data.get("recent_alerts"), list):
                self.log_result(
                    "Track Price Status",
                    False,
                    f"recent_alerts should be list, got {type(data.get('recent_alerts'))}",
                    data
                )
                return False
            
            self.log_result(
                "Track Price Status",
                True,
                f"Status endpoint working correctly. Active searches: {data.get('active_searches_total')}, Future: {data.get('active_searches_future')}"
            )
            return True
            
        except Exception as e:
            self.log_result("Track Price Status", False, f"Exception: {str(e)}")
            return False
    
    async def test_trigger_price_check_all(self):
        """Test POST /api/track-price/check-all"""
        try:
            response = await self.client.post(f"{self.backend_url}/api/track-price/check-all")
            
            if response.status_code != 200:
                self.log_result(
                    "Trigger Price Check All",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["status", "message", "timestamp"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Trigger Price Check All",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Check status is "started"
            if data.get("status") != "started":
                self.log_result(
                    "Trigger Price Check All",
                    False,
                    f"Expected status='started', got '{data.get('status')}'",
                    data
                )
                return False
            
            # Check message contains background job info
            message = data.get("message", "").lower()
            if "background" not in message or "started" not in message:
                self.log_result(
                    "Trigger Price Check All",
                    False,
                    f"Message should indicate background job started: {data.get('message')}",
                    data
                )
                return False
            
            self.log_result(
                "Trigger Price Check All",
                True,
                "Background price check job started successfully"
            )
            return True
            
        except Exception as e:
            self.log_result("Trigger Price Check All", False, f"Exception: {str(e)}")
            return False
    
    async def test_get_saved_searches(self):
        """Test GET /api/saved-searches (prerequisite for single check)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/saved-searches",
                params={"email": self.test_email}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Get Saved Searches",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if "searches" not in data or "count" not in data:
                self.log_result(
                    "Get Saved Searches",
                    False,
                    "Missing 'searches' or 'count' in response",
                    data
                )
                return False
            
            searches = data.get("searches", [])
            count = data.get("count", 0)
            
            if len(searches) != count:
                self.log_result(
                    "Get Saved Searches",
                    False,
                    f"Count mismatch: {count} reported but {len(searches)} searches returned",
                    data
                )
                return False
            
            # Find our test search
            test_search = None
            for search in searches:
                if search.get("email") == self.test_email:
                    test_search = search
                    self.saved_search_id = search.get("id")
                    break
            
            if not test_search:
                self.log_result(
                    "Get Saved Searches",
                    False,
                    f"Could not find saved search for {self.test_email}",
                    data
                )
                return False
            
            self.log_result(
                "Get Saved Searches",
                True,
                f"Retrieved {count} saved searches, found test search ID: {self.saved_search_id}"
            )
            return True
            
        except Exception as e:
            self.log_result("Get Saved Searches", False, f"Exception: {str(e)}")
            return False
    
    async def test_check_single_search(self):
        """Test POST /api/track-price/check-single"""
        try:
            if not self.saved_search_id:
                self.log_result(
                    "Check Single Search",
                    False,
                    "No saved search ID available for testing"
                )
                return False
            
            payload = {
                "search_id": self.saved_search_id,
                "email": self.test_email
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/track-price/check-single",
                json=payload
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Check Single Search",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = [
                "status", "search_id", "route", "current_price", 
                "currency", "price_changed", "checked_at"
            ]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Check Single Search",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Validate data types and values
            if data.get("search_id") != self.saved_search_id:
                self.log_result(
                    "Check Single Search",
                    False,
                    f"Search ID mismatch: expected {self.saved_search_id}, got {data.get('search_id')}",
                    data
                )
                return False
            
            if not isinstance(data.get("current_price"), (int, float)):
                self.log_result(
                    "Check Single Search",
                    False,
                    f"current_price should be numeric, got {type(data.get('current_price'))}",
                    data
                )
                return False
            
            if not isinstance(data.get("price_changed"), bool):
                self.log_result(
                    "Check Single Search",
                    False,
                    f"price_changed should be boolean, got {type(data.get('price_changed'))}",
                    data
                )
                return False
            
            # Check route format
            route = data.get("route", "")
            if "→" not in route or "DEL" not in route or "BOM" not in route:
                self.log_result(
                    "Check Single Search",
                    False,
                    f"Invalid route format: {route}",
                    data
                )
                return False
            
            # Check status
            status = data.get("status")
            if status not in ["checked", "no_data"]:
                self.log_result(
                    "Check Single Search",
                    False,
                    f"Unexpected status: {status}",
                    data
                )
                return False
            
            if status == "no_data":
                self.log_result(
                    "Check Single Search",
                    True,
                    "Single search check completed - no current price data available (expected for test route)"
                )
            else:
                self.log_result(
                    "Check Single Search",
                    True,
                    f"Single search check completed successfully. Current price: {data.get('current_price')} {data.get('currency')}, Price changed: {data.get('price_changed')}"
                )
            
            return True
            
        except Exception as e:
            self.log_result("Check Single Search", False, f"Exception: {str(e)}")
            return False
    
    async def test_internal_search_stats(self):
        """Test GET /api/internal/search-stats (Cost Control)"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/internal/search-stats")
            
            if response.status_code != 200:
                self.log_result(
                    "Internal Search Stats",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields
            required_fields = ["status", "timestamp", "statistics"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Internal Search Stats",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Check statistics structure
            stats = data.get("statistics", {})
            expected_stats_fields = ["searches_today", "daily_cap", "remaining_today"]
            missing_stats = [field for field in expected_stats_fields if field not in stats]
            
            if missing_stats:
                self.log_result(
                    "Internal Search Stats",
                    False,
                    f"Missing statistics fields: {missing_stats}",
                    stats
                )
                return False
            
            # Validate data types
            if not isinstance(stats.get("searches_today"), int):
                self.log_result(
                    "Internal Search Stats",
                    False,
                    f"searches_today should be int, got {type(stats.get('searches_today'))}",
                    stats
                )
                return False
            
            if not isinstance(stats.get("daily_cap"), int):
                self.log_result(
                    "Internal Search Stats",
                    False,
                    f"daily_cap should be int, got {type(stats.get('daily_cap'))}",
                    stats
                )
                return False
            
            # Check that daily quota tracking is working
            searches_today = stats.get("searches_today", 0)
            daily_cap = stats.get("daily_cap", 0)
            remaining = stats.get("remaining_today", 0)
            
            if daily_cap > 0 and remaining != (daily_cap - searches_today):
                self.log_result(
                    "Internal Search Stats",
                    False,
                    f"Quota calculation error: {daily_cap} - {searches_today} != {remaining}",
                    stats
                )
                return False
            
            self.log_result(
                "Internal Search Stats",
                True,
                f"Daily quota tracking working. Today: {searches_today}/{daily_cap}, Remaining: {remaining}"
            )
            return True
            
        except Exception as e:
            self.log_result("Internal Search Stats", False, f"Exception: {str(e)}")
            return False
    
    async def cleanup_test_data(self):
        """Clean up test saved search"""
        try:
            if self.saved_search_id:
                response = await self.client.delete(
                    f"{self.backend_url}/api/saved-searches/{self.saved_search_id}",
                    params={"email": self.test_email}
                )
                
                if response.status_code == 200:
                    self.log_result(
                        "Cleanup Test Data",
                        True,
                        f"Successfully cleaned up test search {self.saved_search_id}"
                    )
                else:
                    self.log_result(
                        "Cleanup Test Data",
                        False,
                        f"Failed to cleanup test search: {response.status_code}"
                    )
        except Exception as e:
            self.log_result("Cleanup Test Data", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all track price tests"""
        print("🚀 Starting Track Price System Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Setup phase
        setup_success = await self.setup_saved_search()
        if not setup_success:
            print("❌ Setup failed, cannot continue with tests")
            return False
        
        # Run all tests in order
        tests = [
            self.test_track_price_status,
            self.test_trigger_price_check_all,
            self.test_get_saved_searches,
            self.test_check_single_search,
            self.test_internal_search_stats
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                results.append(False)
        
        # Cleanup
        await self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TRACK PRICE SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Track Price system tests passed!")
            print("📝 Price drop thresholds correctly configured (5.0%, ₹500)")
            print("📝 Background job triggering working")
            print("📝 Single search price checking functional")
            print("📝 Daily quota tracking operational")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with TrackPriceTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())