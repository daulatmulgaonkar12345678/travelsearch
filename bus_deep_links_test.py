#!/usr/bin/env python3
"""
Bus Booking Deep Link Fix Testing
Tests the centralized deep link generator and integration with bus search services
"""

import asyncio
import httpx
import json
import re
from datetime import datetime
import sys
import os

# Backend URL - using localhost as per system setup
BACKEND_URL = "http://localhost:8001"

class BusDeepLinkTester:
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
    
    def validate_booking_partner_url(self, url: str, partner_name: str) -> tuple[bool, str]:
        """
        Validate that a booking partner URL is properly formatted.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL is empty"
        
        # Check for common issues
        invalid_patterns = [
            'undefined',
            'null',
            'NaN',
            'cityId=',
            'fromCityId=',
            'toCityId=',
            'srcId=',
            'destId=',
            '-to-$',  # Missing destination
            '--',     # Double hyphens
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False, f"Contains invalid pattern: {pattern}"
        
        # Check for proper slug format (lowercase, hyphenated)
        if partner_name != "MSRTC Official":  # MSRTC Official uses homepage
            # Extract route part from URL
            route_patterns = [
                r'/bus-tickets/([^/?]+)',  # redBus, AbhiBus
                r'/bus/([^/?]+)',          # Paytm
            ]
            
            route_match = None
            for pattern in route_patterns:
                match = re.search(pattern, url)
                if match:
                    route_match = match.group(1)
                    break
            
            if route_match:
                # Should be in format: origin-to-destination
                if not re.match(r'^[a-z0-9]+-to-[a-z0-9-]+$', route_match):
                    return False, f"Invalid route format: {route_match} (should be lowercase slug format)"
        
        return True, ""
    
    def validate_all_booking_partners(self, offers: list) -> tuple[bool, list]:
        """
        Validate all booking partner URLs in all offers.
        
        Returns:
            Tuple of (all_valid, error_list)
        """
        errors = []
        
        for i, offer in enumerate(offers):
            booking_partners = offer.get("booking_partners", [])
            
            if not booking_partners:
                errors.append(f"Offer {i+1}: No booking partners found")
                continue
            
            for partner in booking_partners:
                partner_name = partner.get("name", "Unknown")
                partner_url = partner.get("url", "")
                
                is_valid, error_msg = self.validate_booking_partner_url(partner_url, partner_name)
                
                if not is_valid:
                    errors.append(f"Offer {i+1} - {partner_name}: {error_msg} (URL: {partner_url})")
        
        return len(errors) == 0, errors
    
    async def test_basic_slug_url_validation(self):
        """Test GET /api/search/buses?origin=Pune&destination=Kolhapur - booking_partners URLs should be slug-based"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Pune",
                    "destination": "Kolhapur",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Basic Slug URL Validation", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "Basic Slug URL Validation",
                    False,
                    "No offers returned for Pune → Kolhapur",
                    data
                )
                return False
            
            # Validate all booking partner URLs
            all_valid, errors = self.validate_all_booking_partners(offers)
            
            if not all_valid:
                self.log_result(
                    "Basic Slug URL Validation",
                    False,
                    f"URL validation failed: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}",
                    {"errors": errors, "sample_offer": offers[0] if offers else None}
                )
                return False
            
            # Check specific expected URLs
            first_offer = offers[0]
            booking_partners = first_offer.get("booking_partners", [])
            
            expected_patterns = {
                "redBus": r"https://www\.redbus\.in/bus-tickets/pune-to-kolhapur",
                "AbhiBus": r"https://www\.abhibus\.com/bus-tickets/pune-to-kolhapur",
                "Paytm Bus": r"https://tickets\.paytm\.com/bus/pune-to-kolhapur",
                "MSRTC Official": r"https://public\.msrtcors\.com/ticket/"
            }
            
            found_partners = {p["name"]: p["url"] for p in booking_partners}
            
            for partner_name, expected_pattern in expected_patterns.items():
                if partner_name in found_partners:
                    url = found_partners[partner_name]
                    if not re.match(expected_pattern, url):
                        self.log_result(
                            "Basic Slug URL Validation",
                            False,
                            f"{partner_name} URL doesn't match expected pattern. Got: {url}",
                            {"expected_pattern": expected_pattern, "actual_url": url}
                        )
                        return False
            
            self.log_result(
                "Basic Slug URL Validation",
                True,
                f"All {len(offers)} offers have properly formatted booking partner URLs"
            )
            return True
            
        except Exception as e:
            self.log_result("Basic Slug URL Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_state_network_route_validation(self):
        """Test GET /api/search/buses?origin=Satara&destination=Karad - URLs should NOT contain 'undefined', 'NaN', or query params with IDs"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Satara",
                    "destination": "Karad",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "State Network Route Validation", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "State Network Route Validation",
                    False,
                    "No offers returned for Satara → Karad",
                    data
                )
                return False
            
            # Validate all booking partner URLs
            all_valid, errors = self.validate_all_booking_partners(offers)
            
            if not all_valid:
                self.log_result(
                    "State Network Route Validation",
                    False,
                    f"URL validation failed: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}",
                    {"errors": errors}
                )
                return False
            
            # Check that URLs contain expected slug format
            for offer in offers:
                booking_partners = offer.get("booking_partners", [])
                for partner in booking_partners:
                    url = partner.get("url", "")
                    partner_name = partner.get("name", "")
                    
                    if partner_name != "MSRTC Official":  # MSRTC Official uses homepage
                        if "satara-to-karad" not in url.lower():
                            self.log_result(
                                "State Network Route Validation",
                                False,
                                f"{partner_name} URL doesn't contain expected route slug 'satara-to-karad': {url}",
                                {"partner": partner}
                            )
                            return False
            
            self.log_result(
                "State Network Route Validation",
                True,
                f"All {len(offers)} offers have clean URLs without undefined/NaN values"
            )
            return True
            
        except Exception as e:
            self.log_result("State Network Route Validation", False, f"Exception: {str(e)}")
            return False
    
    async def test_city_alias_resolution(self):
        """Test GET /api/search/buses?origin=Ajanta%20Caves&destination=Mumbai - Ajanta should resolve to 'aurangabad' in URLs"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Ajanta Caves",
                    "destination": "Mumbai",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "City Alias Resolution", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "City Alias Resolution",
                    False,
                    "No offers returned for Ajanta Caves → Mumbai",
                    data
                )
                return False
            
            # Check that URLs contain aurangabad-to-mumbai (not ajanta-caves-to-mumbai)
            for offer in offers:
                booking_partners = offer.get("booking_partners", [])
                for partner in booking_partners:
                    url = partner.get("url", "")
                    partner_name = partner.get("name", "")
                    
                    if partner_name == "redBus":
                        expected_url = "https://www.redbus.in/bus-tickets/aurangabad-to-mumbai"
                        if url != expected_url:
                            self.log_result(
                                "City Alias Resolution",
                                False,
                                f"redBus URL doesn't show alias resolution. Expected: {expected_url}, Got: {url}",
                                {"partner": partner}
                            )
                            return False
                        break
            
            self.log_result(
                "City Alias Resolution",
                True,
                "Ajanta Caves correctly resolved to 'aurangabad' in booking URLs"
            )
            return True
            
        except Exception as e:
            self.log_result("City Alias Resolution", False, f"Exception: {str(e)}")
            return False
    
    async def test_suffix_normalization_bus_stand(self):
        """Test GET /api/search/buses?origin=Kolhapur%20Bus%20Stand&destination=Pune%20Swargate - suffixes should be stripped"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Kolhapur Bus Stand",
                    "destination": "Pune Swargate",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Suffix Normalization (Bus Stand)", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "Suffix Normalization (Bus Stand)",
                    False,
                    "No offers returned for Kolhapur Bus Stand → Pune Swargate",
                    data
                )
                return False
            
            # Check that URLs contain kolhapur-to-pune (not kolhapur-bus-stand-to-pune-swargate)
            for offer in offers:
                booking_partners = offer.get("booking_partners", [])
                for partner in booking_partners:
                    url = partner.get("url", "")
                    partner_name = partner.get("name", "")
                    
                    if partner_name == "redBus":
                        expected_url = "https://www.redbus.in/bus-tickets/kolhapur-to-pune"
                        if url != expected_url:
                            self.log_result(
                                "Suffix Normalization (Bus Stand)",
                                False,
                                f"redBus URL shows suffixes not stripped. Expected: {expected_url}, Got: {url}",
                                {"partner": partner}
                            )
                            return False
                        break
            
            self.log_result(
                "Suffix Normalization (Bus Stand)",
                True,
                "Bus Stand and Swargate suffixes correctly stripped from URLs"
            )
            return True
            
        except Exception as e:
            self.log_result("Suffix Normalization (Bus Stand)", False, f"Exception: {str(e)}")
            return False
    
    async def test_suffix_normalization_cbs_depot(self):
        """Test GET /api/search/buses?origin=Nashik%20CBS&destination=Aurangabad%20Depot - CBS/Depot suffixes should be stripped"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Nashik CBS",
                    "destination": "Aurangabad Depot",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Suffix Normalization (CBS/Depot)", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "Suffix Normalization (CBS/Depot)",
                    False,
                    "No offers returned for Nashik CBS → Aurangabad Depot",
                    data
                )
                return False
            
            # Check that URLs contain nashik-to-aurangabad
            for offer in offers:
                booking_partners = offer.get("booking_partners", [])
                for partner in booking_partners:
                    url = partner.get("url", "")
                    partner_name = partner.get("name", "")
                    
                    if partner_name == "redBus":
                        expected_url = "https://www.redbus.in/bus-tickets/nashik-to-aurangabad"
                        if url != expected_url:
                            self.log_result(
                                "Suffix Normalization (CBS/Depot)",
                                False,
                                f"redBus URL shows suffixes not stripped. Expected: {expected_url}, Got: {url}",
                                {"partner": partner}
                            )
                            return False
                        break
            
            self.log_result(
                "Suffix Normalization (CBS/Depot)",
                True,
                "CBS and Depot suffixes correctly stripped from URLs"
            )
            return True
            
        except Exception as e:
            self.log_result("Suffix Normalization (CBS/Depot)", False, f"Exception: {str(e)}")
            return False
    
    async def test_tourist_destination_routes(self):
        """Test GET /api/search/buses?origin=Pune&destination=Mahabaleshwar - tourist destination should have valid slug URLs"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Pune",
                    "destination": "Mahabaleshwar",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Tourist Destination Routes", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "Tourist Destination Routes",
                    False,
                    "No offers returned for Pune → Mahabaleshwar",
                    data
                )
                return False
            
            # Validate all booking partner URLs
            all_valid, errors = self.validate_all_booking_partners(offers)
            
            if not all_valid:
                self.log_result(
                    "Tourist Destination Routes",
                    False,
                    f"URL validation failed: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}",
                    {"errors": errors}
                )
                return False
            
            # Check that URLs contain pune-to-mahabaleshwar
            for offer in offers:
                booking_partners = offer.get("booking_partners", [])
                for partner in booking_partners:
                    url = partner.get("url", "")
                    partner_name = partner.get("name", "")
                    
                    if partner_name != "MSRTC Official":  # MSRTC Official uses homepage
                        if "pune-to-mahabaleshwar" not in url.lower():
                            self.log_result(
                                "Tourist Destination Routes",
                                False,
                                f"{partner_name} URL doesn't contain expected route slug 'pune-to-mahabaleshwar': {url}",
                                {"partner": partner}
                            )
                            return False
            
            self.log_result(
                "Tourist Destination Routes",
                True,
                f"Tourist destination route has valid slug URLs in all {len(offers)} offers"
            )
            return True
            
        except Exception as e:
            self.log_result("Tourist Destination Routes", False, f"Exception: {str(e)}")
            return False
    
    async def test_msrtc_route_validation(self):
        """Test GET /api/search/buses?origin=Mumbai&destination=Pune - MSRTC offers should have proper booking URLs"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/search/buses",
                params={
                    "origin": "Mumbai",
                    "destination": "Pune",
                    "departure_date": "2025-12-30",
                    "passengers": 1
                }
            )
            
            if response.status_code != 200:
                self.log_result(
                    "MSRTC Route Validation", 
                    False, 
                    f"Expected 200, got {response.status_code}",
                    response.text
                )
                return False
            
            data = response.json()
            offers = data.get("offers", [])
            
            if not offers:
                self.log_result(
                    "MSRTC Route Validation",
                    False,
                    "No offers returned for Mumbai → Pune",
                    data
                )
                return False
            
            # Validate all booking partner URLs
            all_valid, errors = self.validate_all_booking_partners(offers)
            
            if not all_valid:
                self.log_result(
                    "MSRTC Route Validation",
                    False,
                    f"URL validation failed: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}",
                    {"errors": errors}
                )
                return False
            
            # Check for MSRTC Official homepage URL
            msrtc_found = False
            for offer in offers:
                booking_partners = offer.get("booking_partners", [])
                for partner in booking_partners:
                    if partner.get("name") == "MSRTC Official":
                        msrtc_found = True
                        expected_url = "https://public.msrtcors.com/ticket/"
                        actual_url = partner.get("url", "")
                        if actual_url != expected_url:
                            self.log_result(
                                "MSRTC Route Validation",
                                False,
                                f"MSRTC Official URL incorrect. Expected: {expected_url}, Got: {actual_url}",
                                {"partner": partner}
                            )
                            return False
                        break
            
            if not msrtc_found:
                self.log_result(
                    "MSRTC Route Validation",
                    False,
                    "MSRTC Official booking partner not found in offers",
                    {"offers_count": len(offers)}
                )
                return False
            
            self.log_result(
                "MSRTC Route Validation",
                True,
                f"MSRTC route has proper booking URLs including MSRTC Official homepage"
            )
            return True
            
        except Exception as e:
            self.log_result("MSRTC Route Validation", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all bus deep link tests"""
        print("🚀 Starting Bus Booking Deep Link Fix Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Run all tests in order
        tests = [
            self.test_basic_slug_url_validation,
            self.test_state_network_route_validation,
            self.test_city_alias_resolution,
            self.test_suffix_normalization_bus_stand,
            self.test_suffix_normalization_cbs_depot,
            self.test_tourist_destination_routes,
            self.test_msrtc_route_validation,
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
        print("📊 BUS DEEP LINK FIX TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All bus deep link tests passed!")
            print("📝 Slug-only URLs working correctly")
            print("📝 City alias resolution working")
            print("📝 Suffix normalization working")
            print("📝 No undefined/NaN values in URLs")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with BusDeepLinkTester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())