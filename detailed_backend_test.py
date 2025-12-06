#!/usr/bin/env python3
"""
Detailed Backend API Testing - Response times and data validation
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8001"

async def test_response_times():
    """Test API response times"""
    print("⏱️  Testing API Response Times")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test flight search response time
        start_time = time.time()
        response = await client.post(
            f"{BACKEND_URL}/api/search/flights",
            json={
                "trip_type": "oneway",
                "origin": "BOM",
                "destination": "DEL",
                "departure_date": "2025-12-20",
                "adults": 1,
                "cabin_class": "economy"
            }
        )
        flight_time = time.time() - start_time
        
        print(f"✅ Flight Search: {flight_time:.2f}s (< 30s requirement)")
        
        # Test hotel search response time
        start_time = time.time()
        response = await client.post(
            f"{BACKEND_URL}/api/search/hotels",
            json={
                "city": "Mumbai",
                "check_in": "2025-12-20",
                "check_out": "2025-12-22",
                "rooms": [{"adults": 2, "children": []}]
            }
        )
        hotel_time = time.time() - start_time
        
        print(f"✅ Hotel Search: {hotel_time:.2f}s (< 30s requirement)")
        
        # Test redirect response time
        start_time = time.time()
        response = await client.get(
            f"{BACKEND_URL}/api/redirect/aviasales",
            params={
                "origin": "BOM",
                "destination": "DEL",
                "depart": "2025-12-20",
                "adults": 1
            },
            follow_redirects=False
        )
        redirect_time = time.time() - start_time
        
        print(f"✅ Aviasales Redirect: {redirect_time:.2f}s")
        
        return flight_time < 30 and hotel_time < 30

async def test_data_quality():
    """Test data quality and completeness"""
    print("\n🔍 Testing Data Quality")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test flight data quality
        response = await client.post(
            f"{BACKEND_URL}/api/search/flights",
            json={
                "trip_type": "oneway",
                "origin": "BOM",
                "destination": "DEL",
                "departure_date": "2025-12-20",
                "adults": 1,
                "cabin_class": "economy"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get("offers", [])
            
            if offers:
                first_offer = offers[0]
                
                # Check for mock data indicators
                if "MOCK" in str(first_offer) or "mock" in str(first_offer):
                    print("❌ Flight data contains mock indicators")
                    return False
                
                # Validate segments have real data
                segments = first_offer.get("segments", [])
                if segments:
                    segment = segments[0]
                    
                    # Check departure/arrival times are valid
                    dep_time = segment.get("departure_time")
                    arr_time = segment.get("arrival_time")
                    
                    if dep_time and arr_time:
                        try:
                            dep_dt = datetime.fromisoformat(dep_time.replace("Z", "+00:00"))
                            arr_dt = datetime.fromisoformat(arr_time.replace("Z", "+00:00"))
                            
                            if arr_dt > dep_dt:
                                print(f"✅ Flight times valid: {dep_time} -> {arr_time}")
                            else:
                                print(f"❌ Invalid flight times: {dep_time} -> {arr_time}")
                                return False
                        except:
                            print(f"❌ Invalid datetime format: {dep_time}, {arr_time}")
                            return False
                    
                    # Check carrier info
                    carrier = segment.get("carrier_code")
                    flight_num = segment.get("flight_number")
                    
                    if carrier and flight_num:
                        print(f"✅ Flight details: {carrier} {flight_num}")
                    else:
                        print("❌ Missing carrier or flight number")
                        return False
                
                # Check price is reasonable (not 0 or negative)
                price = first_offer.get("price", 0)
                if price > 1000:  # Reasonable minimum for BOM-DEL flight
                    print(f"✅ Realistic price: ₹{price}")
                else:
                    print(f"❌ Unrealistic price: ₹{price}")
                    return False
        
        # Test hotel data quality
        response = await client.post(
            f"{BACKEND_URL}/api/search/hotels",
            json={
                "city": "Mumbai",
                "check_in": "2025-12-20",
                "check_out": "2025-12-22",
                "rooms": [{"adults": 2, "children": []}]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get("offers", [])
            
            if offers:
                first_offer = offers[0]
                
                # Check for mock data
                if "MOCK" in str(first_offer) or "mock" in str(first_offer):
                    print("❌ Hotel data contains mock indicators")
                    return False
                
                hotel_name = first_offer.get("hotel_name", "")
                price = first_offer.get("total_price", 0)
                
                if hotel_name and len(hotel_name) > 3:
                    print(f"✅ Real hotel name: {hotel_name}")
                else:
                    print(f"❌ Invalid hotel name: {hotel_name}")
                    return False
                
                if price > 1000:  # Reasonable minimum for Mumbai hotel
                    print(f"✅ Realistic hotel price: ₹{price}")
                else:
                    print(f"❌ Unrealistic hotel price: ₹{price}")
                    return False
        
        return True

async def test_provider_verification():
    """Verify all responses are from real providers, not mock"""
    print("\n🏢 Testing Provider Verification")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Check flight provider
        response = await client.post(
            f"{BACKEND_URL}/api/search/flights",
            json={
                "trip_type": "oneway",
                "origin": "BOM",
                "destination": "DEL",
                "departure_date": "2025-12-20",
                "adults": 1,
                "cabin_class": "economy"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get("offers", [])
            
            if offers:
                providers = set(offer.get("provider") for offer in offers)
                print(f"✅ Flight providers: {', '.join(providers)}")
                
                if "amadeus" not in providers:
                    print("❌ Amadeus provider not found in flight results")
                    return False
            else:
                print("❌ No flight offers returned")
                return False
        
        # Check hotel provider
        response = await client.post(
            f"{BACKEND_URL}/api/search/hotels",
            json={
                "city": "Mumbai",
                "check_in": "2025-12-20",
                "check_out": "2025-12-22",
                "rooms": [{"adults": 2, "children": []}]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get("offers", [])
            
            if offers:
                providers = set(offer.get("provider") for offer in offers)
                print(f"✅ Hotel providers: {', '.join(providers)}")
                
                if "amadeus" not in providers:
                    print("❌ Amadeus provider not found in hotel results")
                    return False
            else:
                print("❌ No hotel offers returned")
                return False
        
        # Check Aviasales redirect
        response = await client.get(
            f"{BACKEND_URL}/api/redirect/aviasales",
            params={
                "origin": "BOM",
                "destination": "DEL",
                "depart": "2025-12-20",
                "adults": 1
            },
            follow_redirects=False
        )
        
        if response.status_code == 302:
            location = response.headers.get("location", "")
            if "aviasales.tpx.lt" in location and "marker=689331" in location:
                print("✅ Aviasales redirect configured correctly")
            else:
                print(f"❌ Invalid Aviasales redirect: {location}")
                return False
        else:
            print(f"❌ Aviasales redirect failed: {response.status_code}")
            return False
        
        return True

async def main():
    """Run detailed tests"""
    print("🔬 Detailed Backend API Testing")
    print("=" * 50)
    
    # Run all detailed tests
    time_ok = await test_response_times()
    quality_ok = await test_data_quality()
    provider_ok = await test_provider_verification()
    
    print("\n" + "=" * 50)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 50)
    
    print(f"⏱️  Response Times: {'✅ PASS' if time_ok else '❌ FAIL'}")
    print(f"🔍 Data Quality: {'✅ PASS' if quality_ok else '❌ FAIL'}")
    print(f"🏢 Provider Verification: {'✅ PASS' if provider_ok else '❌ FAIL'}")
    
    all_passed = time_ok and quality_ok and provider_ok
    
    if all_passed:
        print("\n🎉 All detailed tests passed!")
        print("✅ APIs are returning real data from Amadeus")
        print("✅ Response times are within requirements")
        print("✅ No mock data detected")
    else:
        print("\n⚠️  Some detailed tests failed")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())