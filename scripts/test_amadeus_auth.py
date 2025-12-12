#!/usr/bin/env python3
"""
Test Amadeus Authentication

Tests Amadeus OAuth credentials and verifies API access.
Useful for debugging 401 errors.

Usage:
    python3 test_amadeus_auth.py
"""

import os
import sys
import httpx
import json
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / "apps" / "backend" / ".env"

if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

AMADEUS_API_KEY = os.environ.get("AMADEUS_API_KEY", "")
AMADEUS_API_SECRET = os.environ.get("AMADEUS_API_SECRET", "")
AMADEUS_BASE_URL = os.environ.get("AMADEUS_BASE_URL", "https://api.amadeus.com")

print("="*60)
print("Amadeus Authentication Test")
print("="*60)
print(f"Base URL: {AMADEUS_BASE_URL}")
print(f"API Key: {AMADEUS_API_KEY[:10]}...{AMADEUS_API_KEY[-4:]}" if AMADEUS_API_KEY else "API Key: NOT SET")
print(f"API Secret: {AMADEUS_API_SECRET[:10]}..." if AMADEUS_API_SECRET else "API Secret: NOT SET")
print()

if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
    print("❌ Error: Amadeus credentials not found in .env file")
    sys.exit(1)

def test_authentication():
    """Test OAuth token generation."""
    print("[1] Testing OAuth token generation...")
    
    token_url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
    
    try:
        response = httpx.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": AMADEUS_API_KEY,
                "client_secret": AMADEUS_API_SECRET
            },
            timeout=10.0
        )
        
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token", "")
            expires_in = data.get("expires_in", 0)
            
            print(f"    ✅ SUCCESS")
            print(f"    Token: {access_token[:20]}...")
            print(f"    Expires in: {expires_in}s ({expires_in//60} minutes)")
            print()
            return access_token
        else:
            print(f"    ❌ FAILED")
            print(f"    Response: {response.text}")
            print()
            return None
    
    except Exception as e:
        print(f"    ❌ EXCEPTION: {e}")
        print()
        return None

def test_flight_search(access_token):
    """Test a simple flight search."""
    print("[2] Testing flight search API...")
    
    search_url = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
    
    params = {
        "originLocationCode": "BOM",
        "destinationLocationCode": "DEL",
        "departureDate": "2025-12-25",
        "adults": 1,
        "currencyCode": "INR",
        "max": 5
    }
    
    try:
        response = httpx.get(
            search_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            },
            params=params,
            timeout=30.0
        )
        
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get("data", [])
            
            print(f"    ✅ SUCCESS")
            print(f"    Offers: {len(offers)}")
            
            if offers:
                first_offer = offers[0]
                price = first_offer.get("price", {}).get("total", "N/A")
                currency = first_offer.get("price", {}).get("currency", "N/A")
                print(f"    Sample price: {price} {currency}")
            
            print()
            return True
        else:
            print(f"    ❌ FAILED")
            print(f"    Response: {response.text}")
            print()
            return False
    
    except Exception as e:
        print(f"    ❌ EXCEPTION: {e}")
        print()
        return False

def main():
    # Test authentication
    access_token = test_authentication()
    
    if not access_token:
        print("="*60)
        print("❌ Authentication FAILED")
        print("="*60)
        print()
        print("Possible issues:")
        print("  1. Invalid API credentials")
        print("  2. Amadeus account suspended or deactivated")
        print("  3. Network connectivity issues")
        print("  4. Wrong environment (test vs production)")
        print()
        print("Next steps:")
        print("  1. Verify credentials in Amadeus dashboard")
        print("  2. Check account status and quota")
        print("  3. Contact Amadeus support if needed")
        print()
        sys.exit(1)
    
    # Test flight search
    search_ok = test_flight_search(access_token)
    
    if search_ok:
        print("="*60)
        print("✅ All tests PASSED")
        print("="*60)
        print()
        print("Amadeus integration is working correctly.")
        print()
        sys.exit(0)
    else:
        print("="*60)
        print("❌ Search test FAILED")
        print("="*60)
        print()
        print("Authentication succeeded but search failed.")
        print("Check API quota and rate limits.")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
