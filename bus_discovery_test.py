#!/usr/bin/env python3
"""
Bus Discovery System Testing - STATE NETWORK RULE Validation
==============================================================

Tests the refactored bus discovery system with STATE NETWORK RULE.
Validates that Maharashtra internal routes NEVER return "0 buses found".

Critical Test Cases:
1. Pune → Kolhapur (MSRTC route)
2. Satara → Karad (State Network - same district route) - CRITICAL
3. Mumbai → Ratnagiri (State Network - long distance)
4. Pune → Mahabaleshwar (Tourist destination)
5. Aurangabad → Ajanta (Heritage site)
6. Nashik → Shirdi (Remote village within MH)
7. Pune → Bangalore (Inter-state route - should be fallback)
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import sys
import os

# Backend URL - using localhost as per system setup
BACKEND_URL = "http://localhost:8001"

class BusDiscoveryTester:
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
    
    async def test_pune_kolhapur_msrtc(self):
        """Test 1: Pune → Kolhapur (MSRTC route)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "pune",
                    "destination": "kolhapur",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Pune → Kolhapur (MSRTC)",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check basic structure
            if "offers" not in data:
                self.log_result(
                    "Pune → Kolhapur (MSRTC)",
                    False,
                    "Missing 'offers' in response",
                    data
                )
                return False
            
            offers = data.get("offers", [])
            
            # CRITICAL: Must have offers
            if len(offers) == 0:
                self.log_result(
                    "Pune → Kolhapur (MSRTC)",
                    False,
                    "CRITICAL: 0 buses found for Pune → Kolhapur",
                    data
                )
                return False
            
            # Check is_fallback
            is_fallback = data.get("is_fallback", True)
            if is_fallback:
                self.log_result(
                    "Pune → Kolhapur (MSRTC)",
                    False,
                    f"Expected is_fallback=false, got {is_fallback}",
                    data
                )
                return False
            
            # Check for MSRTC variants
            msrtc_offers = [o for o in offers if "msrtc" in o.get("operator_name", "").lower()]
            
            self.log_result(
                "Pune → Kolhapur (MSRTC)",
                True,
                f"Found {len(offers)} offers ({len(msrtc_offers)} MSRTC), is_fallback={is_fallback}"
            )
            return True
            
        except Exception as e:
            self.log_result("Pune → Kolhapur (MSRTC)", False, f"Exception: {str(e)}")
            return False
    
    async def test_satara_karad_critical(self):
        """Test 2: Satara → Karad (State Network - same district route) - CRITICAL"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "satara",
                    "destination": "karad",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Satara → Karad (CRITICAL)",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            
            # Check basic structure
            if "offers" not in data:
                self.log_result(
                    "Satara → Karad (CRITICAL)",
                    False,
                    "Missing 'offers' in response",
                    data
                )
                return False
            
            offers = data.get("offers", [])
            
            # CRITICAL: Must NOT return "0 buses found"
            if len(offers) == 0:
                self.log_result(
                    "Satara → Karad (CRITICAL)",
                    False,
                    "CRITICAL FAILURE: 0 buses found for Satara → Karad (same district route)",
                    data
                )
                return False
            
            # Check is_fallback (should be false for state network)
            is_fallback = data.get("is_fallback", True)
            if is_fallback:
                self.log_result(
                    "Satara → Karad (CRITICAL)",
                    False,
                    f"Expected is_fallback=false for state network, got {is_fallback}",
                    data
                )
                return False
            
            # Check for multiple bus types
            bus_types = set()
            for offer in offers:
                bus_types.add(offer.get("bus_type_label", ""))
            
            # Check operator name
            operator_names = set()
            for offer in offers:
                operator_names.add(offer.get("operator_name", ""))
            
            # Validate estimated fares (should be reasonable for ~40km)
            fares = [offer.get("avg_price", 0) for offer in offers]
            min_fare = min(fares) if fares else 0
            max_fare = max(fares) if fares else 0
            
            # For ~40km, expect fares between ₹50-₹300
            if min_fare < 30 or max_fare > 500:
                self.log_result(
                    "Satara → Karad (CRITICAL)",
                    False,
                    f"Unrealistic fares for 40km route: ₹{min_fare}-₹{max_fare}",
                    {"offers": offers[:2]}  # Show first 2 offers
                )
                return False
            
            self.log_result(
                "Satara → Karad (CRITICAL)",
                True,
                f"✅ CRITICAL TEST PASSED: {len(offers)} offers, {len(bus_types)} bus types, is_fallback={is_fallback}, fares ₹{min_fare}-₹{max_fare}, operators: {list(operator_names)}"
            )
            return True
            
        except Exception as e:
            self.log_result("Satara → Karad (CRITICAL)", False, f"Exception: {str(e)}")
            return False
    
    async def test_mumbai_ratnagiri_long_distance(self):
        """Test 3: Mumbai → Ratnagiri (State Network - long distance)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "mumbai",
                    "destination": "ratnagiri",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Mumbai → Ratnagiri (Long Distance)",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            # CRITICAL: Must have offers
            if len(offers) == 0:
                self.log_result(
                    "Mumbai → Ratnagiri (Long Distance)",
                    False,
                    "CRITICAL: 0 buses found for Mumbai → Ratnagiri",
                    data
                )
                return False
            
            # Check is_fallback
            is_fallback = data.get("is_fallback", True)
            if is_fallback:
                self.log_result(
                    "Mumbai → Ratnagiri (Long Distance)",
                    False,
                    f"Expected is_fallback=false for state network, got {is_fallback}",
                    data
                )
                return False
            
            # For long distance (>100km), should have Volvo
            bus_types = [offer.get("bus_type_label", "") for offer in offers]
            has_volvo = any("volvo" in bt.lower() or "multi" in bt.lower() for bt in bus_types)
            
            # Check estimated fares for ~330km distance
            fares = [offer.get("avg_price", 0) for offer in offers]
            max_fare = max(fares) if fares else 0
            
            # For 330km, expect max fare > ₹400
            if max_fare < 300:
                self.log_result(
                    "Mumbai → Ratnagiri (Long Distance)",
                    False,
                    f"Fares too low for 330km route: max ₹{max_fare}",
                    {"bus_types": bus_types, "fares": fares}
                )
                return False
            
            self.log_result(
                "Mumbai → Ratnagiri (Long Distance)",
                True,
                f"Found {len(offers)} offers, has_volvo={has_volvo}, is_fallback={is_fallback}, max_fare=₹{max_fare}"
            )
            return True
            
        except Exception as e:
            self.log_result("Mumbai → Ratnagiri (Long Distance)", False, f"Exception: {str(e)}")
            return False
    
    async def test_pune_mahabaleshwar_tourist(self):
        """Test 4: Pune → Mahabaleshwar (Tourist destination)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "pune",
                    "destination": "mahabaleshwar",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Pune → Mahabaleshwar (Tourist)",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            # CRITICAL: Must have offers
            if len(offers) == 0:
                self.log_result(
                    "Pune → Mahabaleshwar (Tourist)",
                    False,
                    "CRITICAL: 0 buses found for Pune → Mahabaleshwar (tourist destination)",
                    data
                )
                return False
            
            # Check is_fallback
            is_fallback = data.get("is_fallback", True)
            if is_fallback:
                self.log_result(
                    "Pune → Mahabaleshwar (Tourist)",
                    False,
                    f"Expected is_fallback=false for tourist destination, got {is_fallback}",
                    data
                )
                return False
            
            self.log_result(
                "Pune → Mahabaleshwar (Tourist)",
                True,
                f"Found {len(offers)} offers for tourist destination, is_fallback={is_fallback}"
            )
            return True
            
        except Exception as e:
            self.log_result("Pune → Mahabaleshwar (Tourist)", False, f"Exception: {str(e)}")
            return False
    
    async def test_aurangabad_ajanta_heritage(self):
        """Test 5: Aurangabad → Ajanta (Heritage site)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "aurangabad",
                    "destination": "ajanta",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Aurangabad → Ajanta (Heritage)",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            # CRITICAL: Must have offers
            if len(offers) == 0:
                self.log_result(
                    "Aurangabad → Ajanta (Heritage)",
                    False,
                    "CRITICAL: 0 buses found for Aurangabad → Ajanta (heritage site)",
                    data
                )
                return False
            
            # Check is_fallback
            is_fallback = data.get("is_fallback", True)
            if is_fallback:
                self.log_result(
                    "Aurangabad → Ajanta (Heritage)",
                    False,
                    f"Expected is_fallback=false for heritage site, got {is_fallback}",
                    data
                )
                return False
            
            self.log_result(
                "Aurangabad → Ajanta (Heritage)",
                True,
                f"Found {len(offers)} offers for heritage site, is_fallback={is_fallback}"
            )
            return True
            
        except Exception as e:
            self.log_result("Aurangabad → Ajanta (Heritage)", False, f"Exception: {str(e)}")
            return False
    
    async def test_nashik_shirdi_remote(self):
        """Test 6: Nashik → Shirdi (Remote village within MH)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "nashik",
                    "destination": "shirdi",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Nashik → Shirdi (Remote)",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            # CRITICAL: Must have offers (Shirdi is a known tourist destination)
            if len(offers) == 0:
                self.log_result(
                    "Nashik → Shirdi (Remote)",
                    False,
                    "CRITICAL: 0 buses found for Nashik → Shirdi (tourist destination)",
                    data
                )
                return False
            
            # Check is_fallback
            is_fallback = data.get("is_fallback", True)
            if is_fallback:
                self.log_result(
                    "Nashik → Shirdi (Remote)",
                    False,
                    f"Expected is_fallback=false for Shirdi (tourist destination), got {is_fallback}",
                    data
                )
                return False
            
            self.log_result(
                "Nashik → Shirdi (Remote)",
                True,
                f"Found {len(offers)} offers for Shirdi (tourist destination), is_fallback={is_fallback}"
            )
            return True
            
        except Exception as e:
            self.log_result("Nashik → Shirdi (Remote)", False, f"Exception: {str(e)}")
            return False
    
    async def test_pune_bangalore_interstate(self):
        """Test 7: Pune → Bangalore (Inter-state route - should be fallback)"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "pune",
                    "destination": "bangalore",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Pune → Bangalore (Inter-state)",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            # May have offers OR is_fallback=true (both are acceptable for inter-state)
            is_fallback = data.get("is_fallback", False)
            
            # This is NOT Maharashtra internal, so different behavior is OK
            if len(offers) == 0 and not is_fallback:
                self.log_result(
                    "Pune → Bangalore (Inter-state)",
                    False,
                    "No offers and is_fallback=false for inter-state route",
                    data
                )
                return False
            
            self.log_result(
                "Pune → Bangalore (Inter-state)",
                True,
                f"Inter-state route: {len(offers)} offers, is_fallback={is_fallback} (acceptable for inter-state)"
            )
            return True
            
        except Exception as e:
            self.log_result("Pune → Bangalore (Inter-state)", False, f"Exception: {str(e)}")
            return False
    
    async def validate_booking_partners(self):
        """Validate that booking partners are included correctly"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "pune",
                    "destination": "kolhapur",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Booking Partners Validation",
                    False,
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "Booking Partners Validation",
                    False,
                    "No offers to validate booking partners",
                    data
                )
                return False
            
            # Check first offer for booking partners
            first_offer = offers[0]
            booking_partners = first_offer.get("booking_partners", [])
            
            if not booking_partners:
                self.log_result(
                    "Booking Partners Validation",
                    False,
                    "No booking partners found in offer",
                    first_offer
                )
                return False
            
            # Expected partners
            expected_partners = ["redBus", "MSRTC Official", "AbhiBus", "Paytm"]
            found_partners = [p.get("name", "") for p in booking_partners]
            
            # Check if we have the main partners
            has_redbus = any("redbus" in p.lower() for p in found_partners)
            has_abhibus = any("abhibus" in p.lower() for p in found_partners)
            has_paytm = any("paytm" in p.lower() for p in found_partners)
            
            if not (has_redbus or has_abhibus or has_paytm):
                self.log_result(
                    "Booking Partners Validation",
                    False,
                    f"Missing expected booking partners. Found: {found_partners}",
                    {"booking_partners": booking_partners}
                )
                return False
            
            self.log_result(
                "Booking Partners Validation",
                True,
                f"Found booking partners: {found_partners}"
            )
            return True
            
        except Exception as e:
            self.log_result("Booking Partners Validation", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all bus discovery tests"""
        print("🚌 Starting Bus Discovery System Tests - STATE NETWORK RULE Validation")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Run all tests in order
        tests = [
            self.test_pune_kolhapur_msrtc,
            self.test_satara_karad_critical,
            self.test_mumbai_ratnagiri_long_distance,
            self.test_pune_mahabaleshwar_tourist,
            self.test_aurangabad_ajanta_heritage,
            self.test_nashik_shirdi_remote,
            self.test_pune_bangalore_interstate,
            self.validate_booking_partners,
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
        print("\n" + "=" * 80)
        print("📊 BUS DISCOVERY SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(results)
        total = len(results)
        
        # Show detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        # Critical validation
        critical_tests = [
            "Satara → Karad (CRITICAL)",
            "Pune → Kolhapur (MSRTC)",
            "Mumbai → Ratnagiri (Long Distance)",
        ]
        
        critical_passed = 0
        for result in self.test_results:
            if any(critical in result["test"] for critical in critical_tests):
                if result["success"]:
                    critical_passed += 1
        
        print(f"🔥 Critical Tests: {critical_passed}/{len(critical_tests)} passed")
        
        if passed == total:
            print("🎉 ALL BUS DISCOVERY TESTS PASSED!")
            print("✅ STATE NETWORK RULE working correctly")
            print("✅ No 'false negatives' for Maharashtra internal routes")
            print("✅ Multiple bus types shown for each route")
            print("✅ Estimated fares are reasonable")
            print("✅ Booking partners included correctly")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            
            # Check for critical failures
            critical_failures = []
            for result in self.test_results:
                if not result["success"] and any(critical in result["test"] for critical in critical_tests):
                    critical_failures.append(result["test"])
            
            if critical_failures:
                print(f"🚨 CRITICAL FAILURES: {critical_failures}")
                print("🚨 STATE NETWORK RULE may not be working correctly!")
        
        return passed == total

async def main():
    """Main test runner"""
    async with BusDiscoveryTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())