#!/usr/bin/env python3
"""
Additional Bus Search Edge Case Tests
====================================

Additional validation tests for the bus search fix to ensure robustness.
"""

import asyncio
import httpx
import json
from datetime import datetime, date, timedelta
import sys

BACKEND_URL = "http://localhost:8001"

class AdditionalBusTests:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_same_city_validation(self):
        """Test that same origin/destination is properly rejected"""
        try:
            tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Satara",
                    "destination": "Satara", 
                    "departure_date": tomorrow,
                    "passengers": 1
                }
            )
            
            if response.status_code != 400:
                print(f"❌ Same city validation failed: Expected 400, got {response.status_code}")
                return False
            
            error_data = response.json()
            error_detail = error_data.get("detail", "").lower()
            
            if "same" not in error_detail or ("origin" not in error_detail and "destination" not in error_detail):
                print(f"❌ Wrong error message for same city: {error_detail}")
                return False
            
            print("✅ Same city validation working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Same city test exception: {str(e)}")
            return False
    
    async def test_multiple_autocomplete_queries(self):
        """Test multiple autocomplete queries to ensure consistency"""
        test_queries = [
            ("sat", "satara"),
            ("kar", "karad"), 
            ("pune", "pune"),
            ("mumbai", "mumbai")
        ]
        
        all_passed = True
        
        for query, expected_city in test_queries:
            try:
                response = await self.client.get(
                    f"{self.backend_url}/api/autocomplete/bus",
                    params={"q": query, "mode": "bus", "limit": 5}
                )
                
                if response.status_code != 200:
                    print(f"❌ Autocomplete failed for '{query}': {response.status_code}")
                    all_passed = False
                    continue
                
                data = response.json()
                results = data.get("results", [])
                
                if len(results) == 0:
                    print(f"❌ No results for '{query}'")
                    all_passed = False
                    continue
                
                # Check if expected city is in results
                found = False
                for result in results:
                    if expected_city.lower() in result.get("label", "").lower() or \
                       expected_city.lower() in result.get("label_en", "").lower():
                        found = True
                        break
                
                if not found:
                    print(f"❌ Expected city '{expected_city}' not found for query '{query}'")
                    all_passed = False
                else:
                    print(f"✅ Query '{query}' → found '{expected_city}'")
                    
            except Exception as e:
                print(f"❌ Exception for query '{query}': {str(e)}")
                all_passed = False
        
        return all_passed
    
    async def run_additional_tests(self):
        """Run additional validation tests"""
        print("🔍 Running Additional Bus Search Validation Tests")
        print("=" * 60)
        
        tests = [
            self.test_same_city_validation,
            self.test_multiple_autocomplete_queries,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                results.append(False)
        
        passed = sum(results)
        total = len(results)
        
        print(f"\n🎯 Additional Tests: {passed}/{total} passed")
        return passed == total

async def main():
    """Main test runner"""
    async with AdditionalBusTests() as tester:
        success = await tester.run_additional_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())