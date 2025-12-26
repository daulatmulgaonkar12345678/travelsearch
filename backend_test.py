#!/usr/bin/env python3
"""
Backend API Testing for Search Persistence System
Tests the Saved Searches (Backend - MongoDB) functionality
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Backend URL - using localhost as per system setup
BACKEND_URL = "http://localhost:8001"

class SavedSearchesTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.created_search_ids = []  # Track created searches for cleanup
        
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
    
    async def test_save_search_valid(self):
        """Test POST /api/saved-searches with valid data"""
        try:
            payload = {
                "email": "test2@example.com",
                "search": {
                    "origin": "BLR",
                    "destination": "CCU",
                    "departure_date": "2026-02-15",
                    "adults": 2,
                    "cabin_class": "economy",
                    "trip_type": "oneway"
                },
                "last_known_price": 12500,
                "last_known_currency": "INR"
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/saved-searches",
                json=payload
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Save Search Valid", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check required fields in response
            required_fields = ["id", "message", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Save Search Valid",
                    False,
                    f"Missing required fields in response: {missing_fields}",
                    data
                )
                return False
            
            # Validate response structure
            if not isinstance(data.get("id"), str) or len(data["id"]) < 10:
                self.log_result(
                    "Save Search Valid",
                    False,
                    f"Invalid search ID format: {data.get('id')}",
                    data
                )
                return False
            
            if "saved" not in data.get("message", "").lower():
                self.log_result(
                    "Save Search Valid",
                    False,
                    f"Unexpected message format: {data.get('message')}",
                    data
                )
                return False
            
            # Store search ID for later tests
            self.created_search_ids.append(data["id"])
            
            self.log_result(
                "Save Search Valid",
                True,
                f"Successfully saved search with ID: {data['id']}"
            )
            return True
            
        except Exception as e:
            self.log_result("Save Search Valid", False, f"Exception: {str(e)}")
            return False
    
    async def test_get_saved_searches(self):
        """Test GET /api/saved-searches?email=test2@example.com"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/saved-searches",
                params={"email": "test2@example.com"}
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
            
            # If we have searches, validate structure
            if searches:
                first_search = searches[0]
                required_fields = ["id", "email", "search", "created_at", "is_active"]
                missing_fields = [field for field in required_fields if field not in first_search]
                
                if missing_fields:
                    self.log_result(
                        "Get Saved Searches",
                        False,
                        f"Missing required fields in search: {missing_fields}",
                        first_search
                    )
                    return False
                
                # Check MongoDB schema fields
                expected_schema_fields = ["notification_count", "last_notified_at"]
                for field in expected_schema_fields:
                    if field not in first_search:
                        self.log_result(
                            "Get Saved Searches",
                            False,
                            f"Missing MongoDB schema field: {field}",
                            first_search
                        )
                        return False
                
                # Validate initial values
                if first_search.get("notification_count") != 0:
                    self.log_result(
                        "Get Saved Searches",
                        False,
                        f"Expected notification_count=0, got {first_search.get('notification_count')}",
                        first_search
                    )
                    return False
                
                if first_search.get("last_notified_at") is not None:
                    self.log_result(
                        "Get Saved Searches",
                        False,
                        f"Expected last_notified_at=null, got {first_search.get('last_notified_at')}",
                        first_search
                    )
                    return False
                
                if first_search.get("is_active") != True:
                    self.log_result(
                        "Get Saved Searches",
                        False,
                        f"Expected is_active=true, got {first_search.get('is_active')}",
                        first_search
                    )
                    return False
            
            self.log_result(
                "Get Saved Searches",
                True,
                f"Retrieved {count} saved searches with correct schema"
            )
            return True
            
        except Exception as e:
            self.log_result("Get Saved Searches", False, f"Exception: {str(e)}")
            return False
    
    async def test_duplicate_prevention(self):
        """Test saving same search twice should update, not create duplicate"""
        try:
            # Save the same search again
            payload = {
                "email": "test2@example.com",
                "search": {
                    "origin": "BLR",
                    "destination": "CCU",
                    "departure_date": "2026-02-15",
                    "adults": 2,
                    "cabin_class": "economy",
                    "trip_type": "oneway"
                },
                "last_known_price": 13000,  # Different price
                "last_known_currency": "INR"
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/saved-searches",
                json=payload
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Duplicate Prevention", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Should get "updated" message
            if "updated" not in data.get("message", "").lower():
                self.log_result(
                    "Duplicate Prevention",
                    False,
                    f"Expected 'updated' message, got: {data.get('message')}",
                    data
                )
                return False
            
            # Verify only one search exists for this route
            get_response = await self.client.get(
                f"{self.backend_url}/api/saved-searches",
                params={"email": "test2@example.com"}
            )
            
            if get_response.status_code != 200:
                self.log_result(
                    "Duplicate Prevention",
                    False,
                    f"Failed to verify duplicate prevention: {get_response.status_code}",
                    get_response.text
                )
                return False
            
            get_data = get_response.json()
            blr_ccu_searches = [
                s for s in get_data.get("searches", [])
                if s.get("search", {}).get("origin") == "BLR" 
                and s.get("search", {}).get("destination") == "CCU"
                and s.get("search", {}).get("departure_date") == "2026-02-15"
            ]
            
            if len(blr_ccu_searches) != 1:
                self.log_result(
                    "Duplicate Prevention",
                    False,
                    f"Expected 1 BLR-CCU search, found {len(blr_ccu_searches)}",
                    get_data
                )
                return False
            
            # Check that price was updated
            updated_search = blr_ccu_searches[0]
            if updated_search.get("last_known_price") != 13000:
                self.log_result(
                    "Duplicate Prevention",
                    False,
                    f"Price not updated: expected 13000, got {updated_search.get('last_known_price')}",
                    updated_search
                )
                return False
            
            self.log_result(
                "Duplicate Prevention",
                True,
                "Duplicate search correctly updated existing record"
            )
            return True
            
        except Exception as e:
            self.log_result("Duplicate Prevention", False, f"Exception: {str(e)}")
            return False
    
    async def test_delete_saved_search(self):
        """Test DELETE /api/saved-searches/{search_id}?email=test2@example.com"""
        try:
            if not self.created_search_ids:
                self.log_result(
                    "Delete Saved Search",
                    False,
                    "No search ID available for deletion test"
                )
                return False
            
            search_id = self.created_search_ids[0]
            
            response = await self.client.delete(
                f"{self.backend_url}/api/saved-searches/{search_id}",
                params={"email": "test2@example.com"}
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Delete Saved Search", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if "message" not in data or "id" not in data:
                self.log_result(
                    "Delete Saved Search",
                    False,
                    "Missing 'message' or 'id' in delete response",
                    data
                )
                return False
            
            if data.get("id") != search_id:
                self.log_result(
                    "Delete Saved Search",
                    False,
                    f"ID mismatch: expected {search_id}, got {data.get('id')}",
                    data
                )
                return False
            
            # Verify soft delete - search should not appear in active searches
            get_response = await self.client.get(
                f"{self.backend_url}/api/saved-searches",
                params={"email": "test2@example.com"}
            )
            
            if get_response.status_code == 200:
                get_data = get_response.json()
                active_searches = get_data.get("searches", [])
                deleted_search = next((s for s in active_searches if s.get("id") == search_id), None)
                
                if deleted_search:
                    self.log_result(
                        "Delete Saved Search",
                        False,
                        f"Deleted search {search_id} still appears in active searches",
                        deleted_search
                    )
                    return False
            
            self.log_result(
                "Delete Saved Search",
                True,
                f"Successfully soft-deleted search {search_id}"
            )
            return True
            
        except Exception as e:
            self.log_result("Delete Saved Search", False, f"Exception: {str(e)}")
            return False
    
    async def test_invalid_email_validation(self):
        """Test validation with invalid email"""
        try:
            payload = {
                "email": "invalid-email",  # Invalid email format
                "search": {
                    "origin": "BLR",
                    "destination": "CCU",
                    "departure_date": "2026-02-15",
                    "adults": 2,
                    "cabin_class": "economy",
                    "trip_type": "oneway"
                },
                "last_known_price": 12500,
                "last_known_currency": "INR"
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/saved-searches",
                json=payload
            )
            
            # Should return validation error (422)
            if response.status_code != 422:
                self.log_result(
                    "Invalid Email Validation", 
                    False, 
                    f"Expected 422 for invalid email, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check that it's a validation error
            if "detail" not in data:
                self.log_result(
                    "Invalid Email Validation",
                    False,
                    "Missing validation error details",
                    data
                )
                return False
            
            self.log_result(
                "Invalid Email Validation",
                True,
                "Invalid email correctly rejected with 422"
            )
            return True
            
        except Exception as e:
            self.log_result("Invalid Email Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        try:
            payload = {
                "email": "test@example.com",
                "search": {
                    "origin": "BLR",
                    # Missing destination
                    "departure_date": "2026-02-15",
                    "adults": 2,
                    "cabin_class": "economy",
                    "trip_type": "oneway"
                },
                "last_known_price": 12500,
                "last_known_currency": "INR"
            }
            
            response = await self.client.post(
                f"{self.backend_url}/api/saved-searches",
                json=payload
            )
            
            # Should return validation error (422)
            if response.status_code != 422:
                self.log_result(
                    "Missing Required Fields", 
                    False, 
                    f"Expected 422 for missing fields, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check that it's a validation error
            if "detail" not in data:
                self.log_result(
                    "Missing Required Fields",
                    False,
                    "Missing validation error details",
                    data
                )
                return False
            
            self.log_result(
                "Missing Required Fields",
                True,
                "Missing required fields correctly rejected with 422"
            )
            return True
            
        except Exception as e:
            self.log_result("Missing Required Fields", False, f"Exception: {str(e)}")
            return False
    
    async def test_delete_nonexistent_search(self):
        """Test deleting a non-existent search"""
        try:
            fake_id = "00000000-0000-0000-0000-000000000000"
            
            response = await self.client.delete(
                f"{self.backend_url}/api/saved-searches/{fake_id}",
                params={"email": "test2@example.com"}
            )
            
            # Should return 404 for non-existent search
            if response.status_code != 404:
                self.log_result(
                    "Delete Nonexistent Search", 
                    False, 
                    f"Expected 404 for non-existent search, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            if "detail" not in data:
                self.log_result(
                    "Delete Nonexistent Search",
                    False,
                    "Missing error details for 404",
                    data
                )
                return False
            
            self.log_result(
                "Delete Nonexistent Search",
                True,
                "Non-existent search correctly returns 404"
            )
            return True
            
        except Exception as e:
            self.log_result("Delete Nonexistent Search", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all saved searches tests"""
        print("🚀 Starting Saved Searches Backend Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Run all tests in order
        tests = [
            self.test_save_search_valid,
            self.test_get_saved_searches,
            self.test_duplicate_prevention,
            self.test_delete_saved_search,
            self.test_invalid_email_validation,
            self.test_missing_required_fields,
            self.test_delete_nonexistent_search
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SAVED SEARCHES TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All saved searches tests passed!")
            print("📝 MongoDB schema validation successful")
            print("📝 Duplicate prevention working correctly")
            print("📝 Soft delete functionality verified")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with SavedSearchesTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())