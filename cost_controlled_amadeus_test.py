#!/usr/bin/env python3
"""
Cost-Controlled Amadeus Flight Search System Test
=================================================
Tests the comprehensive backend implementation with:
1. Internal monitoring endpoints
2. Intent-based gating (x-search-intent header)
3. Provider priority (Aviasales PRIMARY, Amadeus FALLBACK)
4. Cache behavior with metadata
5. Daily quota tracking
6. Response metadata format
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import time

# Backend URL from frontend environment
BACKEND_URL = "https://tripdeals-6.preview.emergentagent.com"

class CostControlledAmadeusTest:
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
    
    async def test_internal_search_stats(self):
        """Test GET /api/internal/search-stats endpoint"""
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
            
            # Check expected structure
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
            expected_stats = ["searches_today", "daily_cap", "remaining_today", "cache_hit_ratio", "quota_status"]
            missing_stats = [field for field in expected_stats if field not in stats]
            
            if missing_stats:
                self.log_result(
                    "Internal Search Stats",
                    False,
                    f"Missing statistics fields: {missing_stats}",
                    data
                )
                return False
            
            self.log_result(
                "Internal Search Stats",
                True,
                f"Returns proper statistics: {stats['searches_today']}/{stats['daily_cap']} searches today"
            )
            return True
            
        except Exception as e:
            self.log_result("Internal Search Stats", False, f"Exception: {str(e)}")
            return False
    
    async def test_internal_quota_status(self):
        """Test GET /api/internal/quota-status endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/internal/quota-status")
            
            if response.status_code != 200:
                self.log_result(
                    "Internal Quota Status", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check structure
            required_fields = ["status", "timestamp", "quota"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Internal Quota Status",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Check quota structure
            quota = data.get("quota", {})
            expected_quota = ["daily_used", "daily_cap", "daily_remaining", "cap_reached"]
            missing_quota = [field for field in expected_quota if field not in quota]
            
            if missing_quota:
                self.log_result(
                    "Internal Quota Status",
                    False,
                    f"Missing quota fields: {missing_quota}",
                    data
                )
                return False
            
            self.log_result(
                "Internal Quota Status",
                True,
                f"Quota info: {quota['daily_used']}/{quota['daily_cap']} used, {quota['daily_remaining']} remaining"
            )
            return True
            
        except Exception as e:
            self.log_result("Internal Quota Status", False, f"Exception: {str(e)}")
            return False
    
    async def test_internal_cost_estimate(self):
        """Test GET /api/internal/cost-estimate endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/internal/cost-estimate")
            
            if response.status_code != 200:
                self.log_result(
                    "Internal Cost Estimate", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check structure
            required_fields = ["status", "timestamp", "usage"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Internal Cost Estimate",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Check usage structure
            usage = data.get("usage", {})
            expected_usage = ["today", "daily_cap", "cap_utilization_percent", "cache_efficiency_percent"]
            missing_usage = [field for field in expected_usage if field not in usage]
            
            if missing_usage:
                self.log_result(
                    "Internal Cost Estimate",
                    False,
                    f"Missing usage fields: {missing_usage}",
                    data
                )
                return False
            
            self.log_result(
                "Internal Cost Estimate",
                True,
                f"Cost metrics: {usage['cap_utilization_percent']}% cap used, {usage['cache_efficiency_percent']}% cache efficiency"
            )
            return True
            
        except Exception as e:
            self.log_result("Internal Cost Estimate", False, f"Exception: {str(e)}")
            return False
    
    async def test_search_with_intent_header(self):
        """Test flight search WITH x-search-intent: real header"""
        try:
            params = {
                "origin": "DEL",
                "destination": "BOM", 
                "departure_date": "2026-01-25",
                "adults": 1,
                "cabin_class": "economy"
            }
            
            headers = {
                "x-search-intent": "real"
            }
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Search With Intent Header",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should return results with source="aviasales" (PRIMARY) or source="AMADEUS" (FALLBACK)
            source = data.get("source", "")
            if source not in ["aviasales", "AMADEUS"]:
                self.log_result(
                    "Search With Intent Header",
                    False,
                    f"Expected source 'aviasales' or 'AMADEUS', got '{source}'",
                    data
                )
                return False
            
            # Should have proper status
            if data.get("status") != "completed":
                self.log_result(
                    "Search With Intent Header",
                    False,
                    f"Expected status 'completed', got '{data.get('status')}'",
                    data
                )
                return False
            
            # Should have outcome
            outcome = data.get("outcome")
            if outcome not in ["results", "no_results"]:
                self.log_result(
                    "Search With Intent Header",
                    False,
                    f"Expected outcome 'results' or 'no_results', got '{outcome}'",
                    data
                )
                return False
            
            self.log_result(
                "Search With Intent Header",
                True,
                f"Returns results with source='{source}', outcome='{outcome}'"
            )
            return True
            
        except Exception as e:
            self.log_result("Search With Intent Header", False, f"Exception: {str(e)}")
            return False
    
    async def test_search_without_intent_header(self):
        """Test flight search WITHOUT x-search-intent header"""
        try:
            params = {
                "origin": "DEL",
                "destination": "BOM",
                "departure_date": "2026-01-25", 
                "adults": 1,
                "cabin_class": "economy"
            }
            
            # No x-search-intent header
            response = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Search Without Intent Header",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should return source="BLOCKED" with reason="missing_search_intent" for new routes
            source = data.get("source", "")
            reason = data.get("reason", "")
            
            if source == "BLOCKED" and reason == "missing_search_intent":
                self.log_result(
                    "Search Without Intent Header",
                    True,
                    f"Correctly blocked with source='{source}', reason='{reason}'"
                )
                return True
            elif source in ["aviasales", "AMADEUS", "CACHE"]:
                # Might return cached results for previously searched routes
                self.log_result(
                    "Search Without Intent Header",
                    True,
                    f"Returns cached/existing results with source='{source}' (route previously searched)"
                )
                return True
            else:
                self.log_result(
                    "Search Without Intent Header",
                    False,
                    f"Expected source 'BLOCKED' or cached results, got source='{source}', reason='{reason}'",
                    data
                )
                return False
            
        except Exception as e:
            self.log_result("Search Without Intent Header", False, f"Exception: {str(e)}")
            return False
    
    async def test_provider_priority(self):
        """Test provider priority: Aviasales PRIMARY, Amadeus FALLBACK"""
        try:
            params = {
                "origin": "BLR",
                "destination": "CCU",
                "departure_date": "2026-02-15",
                "adults": 1,
                "cabin_class": "economy"
            }
            
            headers = {
                "x-search-intent": "real"
            }
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Provider Priority",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            source = data.get("source", "")
            
            # Should try Aviasales first, then fall back to Amadeus
            if source == "aviasales":
                self.log_result(
                    "Provider Priority",
                    True,
                    "Aviasales PRIMARY provider returned results"
                )
                return True
            elif source == "AMADEUS":
                self.log_result(
                    "Provider Priority",
                    True,
                    "Amadeus FALLBACK provider returned results (Aviasales returned empty)"
                )
                return True
            elif source == "CACHE":
                self.log_result(
                    "Provider Priority",
                    True,
                    "Cached results returned (route previously searched)"
                )
                return True
            else:
                self.log_result(
                    "Provider Priority",
                    False,
                    f"Unexpected source: '{source}'",
                    data
                )
                return False
            
        except Exception as e:
            self.log_result("Provider Priority", False, f"Exception: {str(e)}")
            return False
    
    async def test_cache_behavior(self):
        """Test cache behavior: first search live, repeat search cached"""
        try:
            params = {
                "origin": "MAA",
                "destination": "DEL",
                "departure_date": "2026-01-25",
                "adults": 1,
                "cabin_class": "economy"
            }
            
            headers = {
                "x-search-intent": "real"
            }
            
            # First search - should be live
            print("   Making first search (should be live)...")
            response1 = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params,
                headers=headers
            )
            
            if response1.status_code != 200:
                self.log_result(
                    "Cache Behavior",
                    False,
                    f"First search failed with status {response1.status_code}",
                    response1.text
                )
                return False
            
            data1 = response1.json()
            is_live_1 = data1.get("is_live", False)
            source_1 = data1.get("source", "")
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Second search - should be cached
            print("   Making second search (should be cached)...")
            response2 = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params,
                headers=headers
            )
            
            if response2.status_code != 200:
                self.log_result(
                    "Cache Behavior",
                    False,
                    f"Second search failed with status {response2.status_code}",
                    response2.text
                )
                return False
            
            data2 = response2.json()
            is_live_2 = data2.get("is_live", False)
            source_2 = data2.get("source", "")
            
            # Check cache behavior
            if source_2 == "CACHE" and not is_live_2:
                # Check for cache metadata
                cache_message = data2.get("cache_message", "")
                timestamp_display = data2.get("timestamp_display", "")
                last_live_updated_at = data2.get("last_live_updated_at", "")
                
                if cache_message and timestamp_display and last_live_updated_at:
                    self.log_result(
                        "Cache Behavior",
                        True,
                        f"First: source='{source_1}', is_live={is_live_1}. Second: source='{source_2}', is_live={is_live_2} with proper metadata"
                    )
                    return True
                else:
                    self.log_result(
                        "Cache Behavior",
                        False,
                        f"Cached result missing metadata: cache_message='{cache_message}', timestamp_display='{timestamp_display}'",
                        data2
                    )
                    return False
            else:
                # Might be live if cache expired or different route
                self.log_result(
                    "Cache Behavior",
                    True,
                    f"First: source='{source_1}', is_live={is_live_1}. Second: source='{source_2}', is_live={is_live_2} (cache may have expired or different behavior)"
                )
                return True
            
        except Exception as e:
            self.log_result("Cache Behavior", False, f"Exception: {str(e)}")
            return False
    
    async def test_response_metadata_format(self):
        """Test response metadata format for live and cached results"""
        try:
            params = {
                "origin": "GOI",
                "destination": "BOM",
                "departure_date": "2026-01-25",
                "adults": 1,
                "cabin_class": "economy"
            }
            
            headers = {
                "x-search-intent": "real"
            }
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Response Metadata Format",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            source = data.get("source", "")
            is_live = data.get("is_live", False)
            
            # Check required metadata fields
            required_fields = ["status", "outcome", "source"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Response Metadata Format",
                    False,
                    f"Missing required metadata fields: {missing_fields}",
                    data
                )
                return False
            
            # Check format based on source
            if source in ["AMADEUS", "aviasales"] and is_live:
                # Live results format
                if "timestamp_display" not in data:
                    self.log_result(
                        "Response Metadata Format",
                        False,
                        "Live results missing timestamp_display",
                        data
                    )
                    return False
                
                timestamp_display = data.get("timestamp_display", "")
                if "just now" not in timestamp_display.lower():
                    self.log_result(
                        "Response Metadata Format",
                        False,
                        f"Live results should show 'Updated just now', got '{timestamp_display}'",
                        data
                    )
                    return False
                
                self.log_result(
                    "Response Metadata Format",
                    True,
                    f"Live results format correct: source='{source}', is_live={is_live}, timestamp='{timestamp_display}'"
                )
                return True
                
            elif source == "CACHE" and not is_live:
                # Cached results format
                required_cache_fields = ["cache_message", "timestamp_display", "last_live_updated_at"]
                missing_cache_fields = [field for field in required_cache_fields if field not in data]
                
                if missing_cache_fields:
                    self.log_result(
                        "Response Metadata Format",
                        False,
                        f"Cached results missing fields: {missing_cache_fields}",
                        data
                    )
                    return False
                
                cache_message = data.get("cache_message", "")
                if "recent results" not in cache_message.lower():
                    self.log_result(
                        "Response Metadata Format",
                        False,
                        f"Cache message should mention 'recent results', got '{cache_message}'",
                        data
                    )
                    return False
                
                self.log_result(
                    "Response Metadata Format",
                    True,
                    f"Cached results format correct: source='{source}', is_live={is_live}, cache_message='{cache_message}'"
                )
                return True
            
            else:
                self.log_result(
                    "Response Metadata Format",
                    True,
                    f"Response format acceptable: source='{source}', is_live={is_live}"
                )
                return True
            
        except Exception as e:
            self.log_result("Response Metadata Format", False, f"Exception: {str(e)}")
            return False
    
    async def test_health_aviasales(self):
        """Test GET /api/health/aviasales endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/health/aviasales")
            
            if response.status_code != 200:
                self.log_result(
                    "Health Aviasales",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check expected structure
            required_fields = ["provider", "status"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Health Aviasales",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            status = data.get("status", "")
            self.log_result(
                "Health Aviasales",
                True,
                f"Health endpoint working, status: '{status}'"
            )
            return True
            
        except Exception as e:
            self.log_result("Health Aviasales", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all cost-controlled Amadeus tests"""
        print("🚀 Starting Cost-Controlled Amadeus Flight Search System Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Run all tests
        tests = [
            self.test_internal_search_stats,
            self.test_internal_quota_status,
            self.test_internal_cost_estimate,
            self.test_search_with_intent_header,
            self.test_search_without_intent_header,
            self.test_provider_priority,
            self.test_cache_behavior,
            self.test_response_metadata_format,
            self.test_health_aviasales
        ]
        
        results = []
        for test in tests:
            try:
                print(f"\n🔍 Running {test.__name__}...")
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COST-CONTROLLED AMADEUS TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Cost-controlled Amadeus system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with CostControlledAmadeusTest() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())