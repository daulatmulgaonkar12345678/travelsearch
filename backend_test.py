#!/usr/bin/env python3
"""
Backend API Testing for Aviasales-First Flight Search Infrastructure
Tests the new Aviasales integration with health endpoints and fallback logic
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Backend URL - using localhost as per system setup
BACKEND_URL = "http://localhost:8001"

class AviasalesInfrastructureTester:
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
    
    async def test_health_aviasales(self):
        """Test /api/health/aviasales endpoint"""
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
            required_fields = ["provider", "status", "checks"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Health Aviasales",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Since token is not configured, expect "unconfigured" status
            if data.get("status") != "unconfigured":
                self.log_result(
                    "Health Aviasales",
                    False,
                    f"Expected status 'unconfigured' (token not set), got '{data.get('status')}'",
                    data
                )
                return False
            
            # Check token check
            token_check = data.get("checks", {}).get("token", {})
            if token_check.get("status") != "missing":
                self.log_result(
                    "Health Aviasales",
                    False,
                    f"Expected token status 'missing', got '{token_check.get('status')}'",
                    data
                )
                return False
            
            self.log_result(
                "Health Aviasales",
                True,
                f"Correctly shows unconfigured status (token not set)"
            )
            return True
            
        except Exception as e:
            self.log_result("Health Aviasales", False, f"Exception: {str(e)}")
            return False
    
    async def test_health_providers(self):
        """Test /api/health/providers endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/health/providers")
            
            if response.status_code != 200:
                self.log_result(
                    "Health Providers", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check structure
            required_fields = ["primary", "fallback", "providers", "summary"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_result(
                    "Health Providers",
                    False,
                    f"Missing required fields: {missing_fields}",
                    data
                )
                return False
            
            # Since Aviasales is not configured, Amadeus should be primary
            if data.get("primary") != "amadeus":
                self.log_result(
                    "Health Providers",
                    False,
                    f"Expected primary provider 'amadeus' (since Aviasales unconfigured), got '{data.get('primary')}'",
                    data
                )
                return False
            
            # Check providers structure
            providers = data.get("providers", {})
            if "aviasales" not in providers or "amadeus" not in providers:
                self.log_result(
                    "Health Providers",
                    False,
                    "Missing aviasales or amadeus in providers",
                    data
                )
                return False
            
            # Aviasales should be disabled
            aviasales_info = providers.get("aviasales", {})
            if aviasales_info.get("enabled") != False:
                self.log_result(
                    "Health Providers",
                    False,
                    f"Expected aviasales enabled=false, got {aviasales_info.get('enabled')}",
                    data
                )
                return False
            
            # Amadeus should be enabled and primary
            amadeus_info = providers.get("amadeus", {})
            if amadeus_info.get("role") != "primary":
                self.log_result(
                    "Health Providers",
                    False,
                    f"Expected amadeus role='primary', got '{amadeus_info.get('role')}'",
                    data
                )
                return False
            
            self.log_result(
                "Health Providers",
                True,
                f"Correctly shows Amadeus as primary (Aviasales unconfigured)"
            )
            return True
            
        except Exception as e:
            self.log_result("Health Providers", False, f"Exception: {str(e)}")
            return False
    
    async def test_health_airports(self):
        """Test /api/health/airports endpoint"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/health/airports")
            
            if response.status_code != 200:
                self.log_result(
                    "Health Airports", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check structure
            if data.get("status") != "ok":
                self.log_result(
                    "Health Airports",
                    False,
                    f"Expected status 'ok', got '{data.get('status')}'",
                    data
                )
                return False
            
            stats = data.get("stats", {})
            if not stats:
                self.log_result(
                    "Health Airports",
                    False,
                    "Missing stats in response",
                    data
                )
                return False
            
            # Check for expected airport counts
            total_airports = stats.get("total_airports", 0)
            india_airports = stats.get("india_airports", 0)
            
            # Should have 9015 total airports and 166 Indian airports as per review request
            if total_airports != 9015:
                self.log_result(
                    "Health Airports",
                    False,
                    f"Expected 9015 total airports, got {total_airports}",
                    data
                )
                return False
            
            if india_airports != 166:
                self.log_result(
                    "Health Airports",
                    False,
                    f"Expected 166 Indian airports, got {india_airports}",
                    data
                )
                return False
            
            self.log_result(
                "Health Airports",
                True,
                f"Airport database loaded: {total_airports} total, {india_airports} Indian"
            )
            return True
            
        except Exception as e:
            self.log_result("Health Airports", False, f"Exception: {str(e)}")
            return False
    
    async def test_airport_validation(self):
        """Test airport validation with valid and invalid codes"""
        try:
            # Test valid Indian airports
            valid_airports = ["DEL", "BOM", "PNQ", "GOI", "BLR"]
            
            for airport in valid_airports:
                # Test via search endpoint (which should validate airports)
                params = {
                    "origin": airport,
                    "destination": "DEL" if airport != "DEL" else "BOM",
                    "departure_date": "2025-12-30",  # Future date
                    "trip_type": "oneway",
                    "adults": 1
                }
                
                response = await self.client.get(
                    f"{self.backend_url}/api/search/flights",
                    params=params
                )
                
                # Should not return validation error (200 OK with error message or results)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("outcome") == "error" and "Invalid airport" in data.get("message", ""):
                        self.log_result(
                            "Airport Validation",
                            False,
                            f"Valid airport {airport} was rejected",
                            data
                        )
                        return False
            
            # Test invalid airport
            params = {
                "origin": "XXX",  # Invalid airport
                "destination": "DEL",
                "departure_date": "2025-12-30",  # Future date
                "trip_type": "oneway",
                "adults": 1
            }
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params
            )
            
            # Should return validation error for invalid airport (200 OK with error outcome)
            if response.status_code == 200:
                data = response.json()
                if data.get("outcome") != "error" or "Invalid airport" not in data.get("message", ""):
                    self.log_result(
                        "Airport Validation",
                        False,
                        f"Invalid airport XXX was not rejected properly",
                        data
                    )
                    return False
            else:
                self.log_result(
                    "Airport Validation",
                    False,
                    f"Unexpected status code {response.status_code} for invalid airport",
                    response.text
                )
                return False
            
            self.log_result(
                "Airport Validation",
                True,
                f"Valid airports accepted, invalid airports rejected"
            )
            return True
            
        except Exception as e:
            self.log_result("Airport Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_search_amadeus_fallback(self):
        """Test flight search with Amadeus fallback (since Aviasales not configured)"""
        try:
            params = {
                "origin": "DEL",
                "destination": "BOM",
                "departure_date": "2025-12-30",  # Future date
                "trip_type": "oneway",
                "adults": 1
            }
            
            response = await self.client.get(
                f"{self.backend_url}/api/search/flights",
                params=params
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Search Amadeus Fallback",
                    False,
                    f"Search failed with status {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check response structure
            if data.get("status") != "completed":
                self.log_result(
                    "Search Amadeus Fallback",
                    False,
                    f"Expected status 'completed', got '{data.get('status')}'",
                    data
                )
                return False
            
            # Check if we got results or proper no_results response
            outcome = data.get("outcome")
            if outcome == "results":
                # We got results - check they're from amadeus
                offers = data.get("offers", [])
                if not offers:
                    self.log_result(
                        "Search Amadeus Fallback",
                        False,
                        "Outcome is 'results' but no offers returned",
                        data
                    )
                    return False
                
                # Check supplier is amadeus (fallback)
                supplier = data.get("supplier")
                if supplier != "amadeus":
                    self.log_result(
                        "Search Amadeus Fallback",
                        False,
                        f"Expected supplier 'amadeus', got '{supplier}'",
                        data
                    )
                    return False
                
                # Check offer structure
                first_offer = offers[0]
                required_fields = ["offer_id", "source", "price", "currency", "segments"]
                missing_fields = [field for field in required_fields if field not in first_offer]
                
                if missing_fields:
                    self.log_result(
                        "Search Amadeus Fallback",
                        False,
                        f"Missing required fields in offer: {missing_fields}",
                        first_offer
                    )
                    return False
                
                self.log_result(
                    "Search Amadeus Fallback",
                    True,
                    f"Search returned {len(offers)} offers from Amadeus fallback"
                )
                return True
                
            elif outcome == "no_results":
                # No results is acceptable - check that fallback was attempted
                logs = data.get("logs", [])
                amadeus_attempted = any(log.get("step") == "amadeus" for log in logs)
                
                if not amadeus_attempted:
                    self.log_result(
                        "Search Amadeus Fallback",
                        False,
                        "No results but Amadeus fallback was not attempted",
                        data
                    )
                    return False
                
                self.log_result(
                    "Search Amadeus Fallback",
                    True,
                    "Amadeus fallback was attempted (no results available for this route/date)"
                )
                return True
            
            else:
                self.log_result(
                    "Search Amadeus Fallback",
                    False,
                    f"Unexpected outcome: {outcome}",
                    data
                )
                return False
            
        except Exception as e:
            self.log_result("Search Amadeus Fallback", False, f"Exception: {str(e)}")
            return False
    
    async def test_code_structure(self):
        """Verify the new files exist and have correct structure"""
        try:
            files_to_check = [
                "/app/apps/backend/app/services/adapters/aviasales_adapter.py",
                "/app/apps/backend/app/services/aviasales_orchestrator.py", 
                "/app/apps/backend/app/services/airport_validator.py",
                "/app/apps/backend/app/routers/health_aviasales.py"
            ]
            
            missing_files = []
            for file_path in files_to_check:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log_result(
                    "Code Structure",
                    False,
                    f"Missing files: {missing_files}"
                )
                return False
            
            # Check AviasalesAdapter class exists
            try:
                import sys
                sys.path.insert(0, "/app/apps/backend")
                from app.services.adapters.aviasales_adapter import AviasalesAdapter
                
                # Check if it has required methods
                if not hasattr(AviasalesAdapter, 'search_flights'):
                    self.log_result(
                        "Code Structure",
                        False,
                        "AviasalesAdapter missing search_flights method"
                    )
                    return False
                
                if not hasattr(AviasalesAdapter, 'is_available'):
                    self.log_result(
                        "Code Structure",
                        False,
                        "AviasalesAdapter missing is_available method"
                    )
                    return False
                
            except ImportError as e:
                self.log_result(
                    "Code Structure",
                    False,
                    f"Failed to import AviasalesAdapter: {e}"
                )
                return False
            
            # Check AviasalesFirstOrchestrator
            try:
                from app.services.aviasales_orchestrator import AviasalesFirstOrchestrator
                
                if not hasattr(AviasalesFirstOrchestrator, 'search'):
                    self.log_result(
                        "Code Structure",
                        False,
                        "AviasalesFirstOrchestrator missing search method"
                    )
                    return False
                
            except ImportError as e:
                self.log_result(
                    "Code Structure",
                    False,
                    f"Failed to import AviasalesFirstOrchestrator: {e}"
                )
                return False
            
            # Check airport validator
            try:
                from app.services.airport_validator import is_valid_airport
                
                # Test the function
                if not is_valid_airport("DEL"):
                    self.log_result(
                        "Code Structure",
                        False,
                        "Airport validator not working - DEL should be valid"
                    )
                    return False
                
                if is_valid_airport("XXX"):
                    self.log_result(
                        "Code Structure",
                        False,
                        "Airport validator not working - XXX should be invalid"
                    )
                    return False
                
            except ImportError as e:
                self.log_result(
                    "Code Structure",
                    False,
                    f"Failed to import airport validator: {e}"
                )
                return False
            
            self.log_result(
                "Code Structure",
                True,
                "All required files exist and classes/functions are properly defined"
            )
            return True
            
        except Exception as e:
            self.log_result("Code Structure", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all Aviasales infrastructure tests"""
        print("🚀 Starting Aviasales-First Infrastructure Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_health_aviasales,
            self.test_health_providers,
            self.test_health_airports,
            self.test_airport_validation,
            self.test_search_amadeus_fallback,
            self.test_code_structure
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
        print("📊 AVIASALES INFRASTRUCTURE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Aviasales infrastructure is correctly implemented.")
            print("📝 Note: Aviasales is ready but requires TRAVELPAYOUTS_API_TOKEN to be configured.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with AviasalesInfrastructureTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())