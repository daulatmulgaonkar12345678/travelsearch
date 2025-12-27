#!/usr/bin/env python3
"""MSRTC Scraper Runner

Standalone script to run MSRTC scraper and sync data.

Usage:
    # Test search (no scraping)
    python run_msrtc_scraper.py --test-search "Pune" "Mumbai" "2025-01-15"
    
    # List all routes
    python run_msrtc_scraper.py --list-routes
    
    # List all stops
    python run_msrtc_scraper.py --list-stops
    
    # Sync to database (requires MongoDB running)
    python run_msrtc_scraper.py --sync-db
    
    # Run live scraper (if MSRTC website accessible)
    python run_msrtc_scraper.py --scrape

Note:
    Live scraping may not work from all environments due to
    network restrictions on government websites.
"""

import asyncio
import argparse
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.scrapers.msrtc_seed_data import (
    get_all_msrtc_stops,
    get_all_msrtc_routes,
    get_msrtc_route,
    MSRTC_BUS_TYPES,
)
from app.scrapers.msrtc_service import search_msrtc_buses

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print formatted header."""
    print()
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)
    print()


def list_stops():
    """List all MSRTC stops."""
    print_header("MSRTC STOPS")
    
    stops = get_all_msrtc_stops()
    
    # Group by type
    major_stops = [s for s in stops if s["stop_type"] == "major"]
    minor_stops = [s for s in stops if s["stop_type"] == "minor"]
    
    print(f"📍 MAJOR STOPS ({len(major_stops)}):")
    print("-" * 50)
    for stop in major_stops:
        print(f"  {stop['name_marathi']} ({stop['name_english']})")
        print(f"    Code: {stop['value']} | District: {stop.get('district', 'N/A')}")
        print(f"    Station: {stop.get('station_name_english', 'N/A')}")
        print()
    
    if minor_stops:
        print(f"\n📍 MINOR STOPS ({len(minor_stops)}):")
        print("-" * 50)
        for stop in minor_stops:
            print(f"  {stop['name_marathi']} ({stop['name_english']})")
    
    print(f"\n✅ Total: {len(stops)} stops")


def list_routes():
    """List all MSRTC routes."""
    print_header("MSRTC ROUTES")
    
    routes = get_all_msrtc_routes()
    
    for route in routes:
        phase = "Phase 1" if "PHASE1" in route.route_id or route.route_id.startswith("MSRTC-PUNE") or route.route_id.startswith("MSRTC-MUM-PUNE") else "Phase 2"
        
        print(f"🚌 {route.origin_marathi} → {route.destination_marathi}")
        print(f"   {route.origin_english} → {route.destination_english}")
        print(f"   Distance: {route.distance_km} km | Duration: {route.avg_duration_minutes // 60}h {route.avg_duration_minutes % 60}m")
        print(f"   Base Fare: ₹{route.base_fare} (ST) | Frequency: {route.frequency}")
        print(f"   Bus Types: {', '.join(route.bus_types)}")
        print(f"   Via: {' → '.join(route.via_stops) if route.via_stops else 'Direct'}")
        print()
    
    print(f"✅ Total: {len(routes)} routes")


def list_bus_types():
    """List all MSRTC bus types."""
    print_header("MSRTC BUS TYPES")
    
    for code, info in MSRTC_BUS_TYPES.items():
        ac_label = "AC" if info["is_ac"] else "Non-AC"
        sleeper_label = "Sleeper" if info["is_sleeper"] else "Seater"
        
        print(f"🚌 {code}: {info['name_english']} ({info['name_marathi']})")
        print(f"   Type: {ac_label} {sleeper_label}")
        print(f"   Fare Multiplier: {info['fare_multiplier']}x")
        print()


def test_search(origin: str, destination: str, date: str):
    """Test MSRTC search functionality."""
    print_header(f"MSRTC SEARCH: {origin} → {destination}")
    print(f"Date: {date}\n")
    
    # First check if route exists
    route = get_msrtc_route(origin, destination)
    
    if not route:
        print(f"❌ No MSRTC route found for {origin} → {destination}")
        print("\nAvailable routes include:")
        for r in get_all_msrtc_routes()[:5]:
            print(f"  - {r.origin_english} → {r.destination_english}")
        return
    
    print(f"✅ Found route: {route.route_id}")
    print(f"   {route.origin_marathi} → {route.destination_marathi}")
    print(f"   Distance: {route.distance_km} km")
    print(f"   Duration: {route.avg_duration_minutes} minutes")
    print(f"   Bus Types: {route.bus_types}\n")
    
    # Search for offers
    offers = search_msrtc_buses(origin, destination, date)
    
    print(f"📋 SEARCH RESULTS ({len(offers)} offers):")
    print("-" * 50)
    
    for offer in offers:
        print(f"\n  🚌 {offer.bus_type_label}")
        print(f"     Fare: ₹{offer.avg_price:.0f}")
        print(f"     Departure: {offer.departure_time.strftime('%H:%M')}")
        print(f"     Arrival: {offer.arrival_time.strftime('%H:%M')}")
        print(f"     Duration: {offer.duration_minutes // 60}h {offer.duration_minutes % 60}m")
        print(f"     AC: {'Yes' if offer.is_ac else 'No'} | Sleeper: {'Yes' if offer.is_sleeper else 'No'}")
        print(f"     Booking: {', '.join([p['name'] for p in offer.booking_partners])}")


async def sync_to_db():
    """Sync MSRTC data to MongoDB."""
    print_header("SYNCING MSRTC DATA TO DATABASE")
    
    try:
        from app.db.mongodb import connect_db, close_db, get_database
        from app.scrapers.msrtc_service import save_msrtc_stops_to_db, save_msrtc_routes_to_db
        
        print("Connecting to database...")
        await connect_db()
        db = get_database()
        
        print("Syncing stops...")
        stops_count = await save_msrtc_stops_to_db(db)
        print(f"  ✅ Synced {stops_count} stops")
        
        print("Syncing routes...")
        routes_count = await save_msrtc_routes_to_db(db)
        print(f"  ✅ Synced {routes_count} routes")
        
        await close_db()
        print(f"\n✅ Database sync complete!")
        
    except Exception as e:
        logger.error(f"Database sync failed: {e}")
        print(f"\n❌ Sync failed: {e}")


async def run_live_scraper():
    """Run live MSRTC scraper (requires network access)."""
    print_header("LIVE MSRTC SCRAPER")
    
    print("⚠️  Note: Live scraping may not work from all environments")
    print("    due to network restrictions on government websites.\n")
    
    try:
        from app.scrapers.msrtc import MSRTCScraper
        
        async with MSRTCScraper() as scraper:
            print("Fetching stops from MSRTC website...")
            stops = await scraper.get_all_stops()
            
            if stops:
                print(f"\n✅ Found {len(stops)} stops from live scraper")
                for stop in stops[:10]:
                    print(f"  - {stop.name_marathi} ({stop.name_english or 'N/A'})")
                if len(stops) > 10:
                    print(f"  ... and {len(stops) - 10} more")
            else:
                print("\n⚠️  No stops found. Website may have changed or is inaccessible.")
                print("    Using seed data instead.")
    
    except Exception as e:
        logger.error(f"Live scraper failed: {e}")
        print(f"\n❌ Live scraping failed: {e}")
        print("\n💡 Tip: Use seed data with --list-stops and --test-search instead.")


def main():
    parser = argparse.ArgumentParser(
        description="MSRTC Scraper Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-stops              List all MSRTC stops
  %(prog)s --list-routes             List all MSRTC routes  
  %(prog)s --list-bus-types          List all MSRTC bus types
  %(prog)s --test-search Pune Mumbai 2025-01-15
                                     Test search functionality
  %(prog)s --sync-db                 Sync data to MongoDB
  %(prog)s --scrape                  Run live scraper (if accessible)
"""
    )
    
    parser.add_argument("--list-stops", action="store_true", help="List all MSRTC stops")
    parser.add_argument("--list-routes", action="store_true", help="List all MSRTC routes")
    parser.add_argument("--list-bus-types", action="store_true", help="List all bus types")
    parser.add_argument("--test-search", nargs=3, metavar=("ORIGIN", "DEST", "DATE"),
                        help="Test search: origin destination date")
    parser.add_argument("--sync-db", action="store_true", help="Sync seed data to MongoDB")
    parser.add_argument("--scrape", action="store_true", help="Run live scraper")
    
    args = parser.parse_args()
    
    # Default to showing help if no arguments
    if not any([args.list_stops, args.list_routes, args.list_bus_types, 
                args.test_search, args.sync_db, args.scrape]):
        parser.print_help()
        return
    
    print()
    print("🚌 MSRTC Timetable Scraper")
    print("   Maharashtra State Road Transport Corporation")
    print("   https://msrtc.maharashtra.gov.in")
    
    if args.list_stops:
        list_stops()
    
    if args.list_routes:
        list_routes()
    
    if args.list_bus_types:
        list_bus_types()
    
    if args.test_search:
        origin, dest, date = args.test_search
        test_search(origin, dest, date)
    
    if args.sync_db:
        asyncio.run(sync_to_db())
    
    if args.scrape:
        asyncio.run(run_live_scraper())


if __name__ == "__main__":
    main()
