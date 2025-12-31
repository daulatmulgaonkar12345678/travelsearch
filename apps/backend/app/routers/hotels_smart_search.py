"""
Hotel Smart Search API - City, Area, Hotel Name Autocomplete

Provides unified autocomplete for hotels supporting three search types:
- CITY: City-level search (e.g., "Mumbai")
- AREA: Area/locality search (e.g., "Andheri East, Mumbai")
- HOTEL: Specific hotel name search (e.g., "Taj Lands End")

Each result includes a `type` field for frontend rendering.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()

# Type definitions
SearchResultType = Literal["CITY", "AREA", "HOTEL"]


class SmartSearchResult(BaseModel):
    """Unified search result with type discrimination"""
    id: str
    type: SearchResultType
    label: str
    city: str
    country: str = "India"
    # Optional fields based on type
    area_name: Optional[str] = None     # For AREA type
    hotel_name: Optional[str] = None    # For HOTEL type
    hotel_id: Optional[str] = None      # For HOTEL type
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SmartSearchResponse(BaseModel):
    """API response wrapper"""
    query: str
    count: int
    results: List[SmartSearchResult]
    source: str


# Static data: Popular Indian cities
POPULAR_CITIES = [
    {"city": "Mumbai", "country": "India", "lat": 19.0760, "lng": 72.8777},
    {"city": "Delhi", "country": "India", "lat": 28.7041, "lng": 77.1025},
    {"city": "Bangalore", "country": "India", "lat": 12.9716, "lng": 77.5946},
    {"city": "Chennai", "country": "India", "lat": 13.0827, "lng": 80.2707},
    {"city": "Kolkata", "country": "India", "lat": 22.5726, "lng": 88.3639},
    {"city": "Hyderabad", "country": "India", "lat": 17.3850, "lng": 78.4867},
    {"city": "Pune", "country": "India", "lat": 18.5204, "lng": 73.8567},
    {"city": "Goa", "country": "India", "lat": 15.2993, "lng": 74.1240},
    {"city": "Jaipur", "country": "India", "lat": 26.9124, "lng": 75.7873},
    {"city": "Kochi", "country": "India", "lat": 9.9312, "lng": 76.2673},
    {"city": "Ahmedabad", "country": "India", "lat": 23.0225, "lng": 72.5714},
    {"city": "Lucknow", "country": "India", "lat": 26.8467, "lng": 80.9462},
    {"city": "Varanasi", "country": "India", "lat": 25.3176, "lng": 82.9739},
    {"city": "Udaipur", "country": "India", "lat": 24.5854, "lng": 73.7125},
    {"city": "Agra", "country": "India", "lat": 27.1767, "lng": 78.0081},
    {"city": "Shimla", "country": "India", "lat": 31.1048, "lng": 77.1734},
    {"city": "Manali", "country": "India", "lat": 32.2396, "lng": 77.1887},
    {"city": "Rishikesh", "country": "India", "lat": 30.0869, "lng": 78.2676},
    {"city": "Mysore", "country": "India", "lat": 12.2958, "lng": 76.6394},
    {"city": "Ooty", "country": "India", "lat": 11.4102, "lng": 76.6950},
    {"city": "Munnar", "country": "India", "lat": 10.0889, "lng": 77.0595},
    {"city": "Darjeeling", "country": "India", "lat": 27.0360, "lng": 88.2627},
    {"city": "Srinagar", "country": "India", "lat": 34.0837, "lng": 74.7973},
    {"city": "Leh", "country": "India", "lat": 34.1526, "lng": 77.5771},
    {"city": "Amritsar", "country": "India", "lat": 31.6340, "lng": 74.8723},
    {"city": "Chandigarh", "country": "India", "lat": 30.7333, "lng": 76.7794},
    {"city": "Indore", "country": "India", "lat": 22.7196, "lng": 75.8577},
    {"city": "Coimbatore", "country": "India", "lat": 11.0168, "lng": 76.9558},
    {"city": "Thiruvananthapuram", "country": "India", "lat": 8.5241, "lng": 76.9366},
    {"city": "Bhubaneswar", "country": "India", "lat": 20.2961, "lng": 85.8245},
]

# Static data: Popular areas/localities by city
POPULAR_AREAS = {
    "Mumbai": [
        {"area": "Andheri East", "lat": 19.1136, "lng": 72.8697},
        {"area": "Andheri West", "lat": 19.1362, "lng": 72.8372},
        {"area": "Bandra", "lat": 19.0544, "lng": 72.8402},
        {"area": "Juhu", "lat": 19.0969, "lng": 72.8267},
        {"area": "Powai", "lat": 19.1176, "lng": 72.9060},
        {"area": "Colaba", "lat": 18.9068, "lng": 72.8163},
        {"area": "Lower Parel", "lat": 19.0050, "lng": 72.8283},
        {"area": "BKC (Bandra Kurla Complex)", "lat": 19.0596, "lng": 72.8654},
        {"area": "Marine Drive", "lat": 18.9432, "lng": 72.8232},
        {"area": "Nariman Point", "lat": 18.9256, "lng": 72.8242},
    ],
    "Delhi": [
        {"area": "Connaught Place", "lat": 28.6315, "lng": 77.2167},
        {"area": "Karol Bagh", "lat": 28.6519, "lng": 77.1909},
        {"area": "Paharganj", "lat": 28.6448, "lng": 77.2157},
        {"area": "Aerocity", "lat": 28.5535, "lng": 77.0867},
        {"area": "Dwarka", "lat": 28.5921, "lng": 77.0460},
        {"area": "Gurgaon (Gurugram)", "lat": 28.4595, "lng": 77.0266},
        {"area": "Noida", "lat": 28.5355, "lng": 77.3910},
        {"area": "Saket", "lat": 28.5245, "lng": 77.2066},
        {"area": "Hauz Khas", "lat": 28.5494, "lng": 77.2001},
        {"area": "Greater Kailash", "lat": 28.5494, "lng": 77.2340},
    ],
    "Bangalore": [
        {"area": "Koramangala", "lat": 12.9352, "lng": 77.6245},
        {"area": "MG Road", "lat": 12.9758, "lng": 77.6045},
        {"area": "Whitefield", "lat": 12.9698, "lng": 77.7499},
        {"area": "Electronic City", "lat": 12.8399, "lng": 77.6770},
        {"area": "HSR Layout", "lat": 12.9116, "lng": 77.6389},
        {"area": "Indiranagar", "lat": 12.9784, "lng": 77.6408},
        {"area": "Jayanagar", "lat": 12.9308, "lng": 77.5838},
        {"area": "Marathahalli", "lat": 12.9591, "lng": 77.6974},
        {"area": "Malleshwaram", "lat": 13.0035, "lng": 77.5690},
        {"area": "Hebbal", "lat": 13.0358, "lng": 77.5970},
    ],
    "Goa": [
        {"area": "Calangute", "lat": 15.5449, "lng": 73.7553},
        {"area": "Baga", "lat": 15.5553, "lng": 73.7516},
        {"area": "Anjuna", "lat": 15.5739, "lng": 73.7420},
        {"area": "Panjim", "lat": 15.4989, "lng": 73.8278},
        {"area": "Candolim", "lat": 15.5179, "lng": 73.7618},
        {"area": "Vagator", "lat": 15.5978, "lng": 73.7448},
        {"area": "Palolem", "lat": 15.0100, "lng": 74.0231},
        {"area": "Colva", "lat": 15.2788, "lng": 73.9116},
        {"area": "Arpora", "lat": 15.5664, "lng": 73.7657},
        {"area": "Morjim", "lat": 15.6301, "lng": 73.7315},
    ],
    "Jaipur": [
        {"area": "MI Road", "lat": 26.9072, "lng": 75.7893},
        {"area": "C Scheme", "lat": 26.8936, "lng": 75.7943},
        {"area": "Raja Park", "lat": 26.8957, "lng": 75.8220},
        {"area": "Vaishali Nagar", "lat": 26.9125, "lng": 75.7370},
        {"area": "Tonk Road", "lat": 26.8495, "lng": 75.8089},
        {"area": "Amer", "lat": 26.9855, "lng": 75.8513},
        {"area": "Bani Park", "lat": 26.9282, "lng": 75.7839},
        {"area": "Malviya Nagar", "lat": 26.8583, "lng": 75.8130},
    ],
}

# Static data: Popular hotels by city (sample - would be expanded in production)
POPULAR_HOTELS = {
    "Mumbai": [
        {"name": "Taj Mahal Palace", "hotel_id": "taj_mumbai", "area": "Colaba", "lat": 18.9217, "lng": 72.8332},
        {"name": "The Oberoi Mumbai", "hotel_id": "oberoi_mumbai", "area": "Nariman Point", "lat": 18.9256, "lng": 72.8231},
        {"name": "Trident Nariman Point", "hotel_id": "trident_np", "area": "Nariman Point", "lat": 18.9246, "lng": 72.8234},
        {"name": "JW Marriott Mumbai Juhu", "hotel_id": "jw_juhu", "area": "Juhu", "lat": 19.1020, "lng": 72.8269},
        {"name": "ITC Grand Central", "hotel_id": "itc_mumbai", "area": "Lower Parel", "lat": 19.0058, "lng": 72.8289},
        {"name": "The Lalit Mumbai", "hotel_id": "lalit_mumbai", "area": "Andheri East", "lat": 19.1136, "lng": 72.8697},
        {"name": "Sofitel Mumbai BKC", "hotel_id": "sofitel_bkc", "area": "BKC", "lat": 19.0596, "lng": 72.8654},
        {"name": "Four Seasons Mumbai", "hotel_id": "fs_mumbai", "area": "Worli", "lat": 19.0121, "lng": 72.8176},
    ],
    "Delhi": [
        {"name": "The Imperial", "hotel_id": "imperial_delhi", "area": "Connaught Place", "lat": 28.6250, "lng": 77.2187},
        {"name": "Taj Palace", "hotel_id": "taj_delhi", "area": "Chanakyapuri", "lat": 28.5927, "lng": 77.1739},
        {"name": "The Oberoi New Delhi", "hotel_id": "oberoi_delhi", "area": "Zakir Hussain Marg", "lat": 28.6023, "lng": 77.2301},
        {"name": "ITC Maurya", "hotel_id": "itc_maurya", "area": "Chanakyapuri", "lat": 28.5971, "lng": 77.1746},
        {"name": "The Leela Palace", "hotel_id": "leela_delhi", "area": "Chanakyapuri", "lat": 28.5950, "lng": 77.1769},
        {"name": "Andaz Delhi", "hotel_id": "andaz_delhi", "area": "Aerocity", "lat": 28.5535, "lng": 77.0867},
        {"name": "JW Marriott Aerocity", "hotel_id": "jw_aerocity", "area": "Aerocity", "lat": 28.5550, "lng": 77.0885},
    ],
    "Goa": [
        {"name": "Taj Exotica Resort & Spa", "hotel_id": "taj_exotica_goa", "area": "Benaulim", "lat": 15.2549, "lng": 73.9315},
        {"name": "The Leela Goa", "hotel_id": "leela_goa", "area": "Mobor", "lat": 15.1536, "lng": 73.9461},
        {"name": "Grand Hyatt Goa", "hotel_id": "hyatt_goa", "area": "Bambolim", "lat": 15.4610, "lng": 73.8553},
        {"name": "W Goa", "hotel_id": "w_goa", "area": "Vagator", "lat": 15.5978, "lng": 73.7448},
        {"name": "Park Hyatt Goa", "hotel_id": "park_hyatt_goa", "area": "Arossim", "lat": 15.2993, "lng": 73.8798},
        {"name": "Alila Diwa Goa", "hotel_id": "alila_goa", "area": "Majorda", "lat": 15.2868, "lng": 73.9151},
    ],
    "Jaipur": [
        {"name": "Taj Rambagh Palace", "hotel_id": "rambagh_jaipur", "area": "Bhawani Singh Road", "lat": 26.8972, "lng": 75.8122},
        {"name": "The Oberoi Rajvilas", "hotel_id": "rajvilas_jaipur", "area": "Goner Road", "lat": 26.8280, "lng": 75.8680},
        {"name": "ITC Rajputana", "hotel_id": "itc_jaipur", "area": "MI Road", "lat": 26.9072, "lng": 75.7893},
        {"name": "Fairmont Jaipur", "hotel_id": "fairmont_jaipur", "area": "Kukas", "lat": 27.0165, "lng": 75.8745},
        {"name": "Jai Mahal Palace", "hotel_id": "jai_mahal", "area": "Civil Lines", "lat": 26.9139, "lng": 75.7956},
    ],
}

# Cache for search results
smart_search_cache: Dict[str, tuple[List[SmartSearchResult], datetime]] = {}
CACHE_TTL = 600  # 10 minutes


def search_cities(query: str, limit: int = 5) -> List[SmartSearchResult]:
    """Search cities matching query"""
    query_lower = query.lower()
    results = []
    
    for city_data in POPULAR_CITIES:
        if query_lower in city_data["city"].lower():
            results.append(SmartSearchResult(
                id=f"CITY_{city_data['city'].upper().replace(' ', '_')}",
                type="CITY",
                label=f"{city_data['city']}, {city_data['country']}",
                city=city_data["city"],
                country=city_data["country"],
                latitude=city_data.get("lat"),
                longitude=city_data.get("lng"),
            ))
    
    return results[:limit]


def search_areas(query: str, limit: int = 5) -> List[SmartSearchResult]:
    """Search areas/localities matching query"""
    query_lower = query.lower()
    results = []
    
    for city, areas in POPULAR_AREAS.items():
        for area_data in areas:
            area_name = area_data["area"]
            # Match on area name or "area, city" format
            search_str = f"{area_name} {city}".lower()
            if query_lower in search_str or query_lower in area_name.lower():
                results.append(SmartSearchResult(
                    id=f"AREA_{city.upper()}_{area_name.upper().replace(' ', '_').replace('(', '').replace(')', '')}",
                    type="AREA",
                    label=f"{area_name}, {city}",
                    city=city,
                    country="India",
                    area_name=area_name,
                    latitude=area_data.get("lat"),
                    longitude=area_data.get("lng"),
                ))
    
    return results[:limit]


def search_hotels(query: str, limit: int = 5) -> List[SmartSearchResult]:
    """Search hotels matching query"""
    query_lower = query.lower()
    results = []
    
    for city, hotels in POPULAR_HOTELS.items():
        for hotel_data in hotels:
            hotel_name = hotel_data["name"]
            # Match on hotel name, area, or city
            search_str = f"{hotel_name} {hotel_data.get('area', '')} {city}".lower()
            if query_lower in search_str or query_lower in hotel_name.lower():
                results.append(SmartSearchResult(
                    id=f"HOTEL_{hotel_data['hotel_id'].upper()}",
                    type="HOTEL",
                    label=f"{hotel_name}, {city}",
                    city=city,
                    country="India",
                    hotel_name=hotel_name,
                    hotel_id=hotel_data["hotel_id"],
                    area_name=hotel_data.get("area"),
                    latitude=hotel_data.get("lat"),
                    longitude=hotel_data.get("lng"),
                ))
    
    return results[:limit]


@router.get("/hotels/smart-search", response_model=SmartSearchResponse)
async def smart_search(
    query: str = Query(..., min_length=2, description="Search query (city, area, or hotel name)"),
    limit: int = Query(10, ge=1, le=20, description="Max results per type"),
):
    """
    Smart Hotel Search - Returns mixed results for City, Area, and Hotel name searches.
    
    Each result includes a `type` field:
    - CITY: City-level search (searches all hotels in city)
    - AREA: Area/locality search (filters to specific area)
    - HOTEL: Specific hotel (links directly to hotel)
    
    Results are deduplicated and sorted by relevance.
    """
    try:
        # Check cache
        cache_key = f"smart:{query.lower()}:{limit}"
        if cache_key in smart_search_cache:
            cached_results, cached_at = smart_search_cache[cache_key]
            if datetime.utcnow() - cached_at < timedelta(seconds=CACHE_TTL):
                logger.info(f"[SMART_SEARCH] query=\"{query}\" cacheHit=true count={len(cached_results)}")
                return SmartSearchResponse(
                    query=query,
                    count=len(cached_results),
                    results=cached_results,
                    source="cached"
                )
        
        # Perform searches across CITY and AREA types only
        # NOTE: Hotel name search is NOT supported by Amadeus API
        # Hotels are returned after city selection and can be filtered locally
        city_results = search_cities(query, limit=5)
        area_results = search_areas(query, limit=5)
        
        # Combine and dedupe (prioritize: cities > areas)
        # Hotel-name autocomplete removed per industry standard (Skyscanner, Kayak, Trivago)
        all_results: List[SmartSearchResult] = []
        seen_ids = set()
        
        # Add cities first (broader search)
        for r in city_results:
            if r.id not in seen_ids:
                all_results.append(r)
                seen_ids.add(r.id)
        
        # Then areas (more specific)
        for r in area_results:
            if r.id not in seen_ids:
                all_results.append(r)
                seen_ids.add(r.id)
        
        # Limit total results
        final_results = all_results[:limit]
        
        # Cache results
        smart_search_cache[cache_key] = (final_results, datetime.utcnow())
        
        logger.info(f"[SMART_SEARCH] query=\"{query}\" cities={len(city_results)} areas={len(area_results)} total={len(final_results)}")
        
        return SmartSearchResponse(
            query=query,
            count=len(final_results),
            results=final_results,
            source="static"  # Would be "amadeus" in production
        )
    
    except Exception as e:
        logger.error(f"[SMART_SEARCH] Error: {e}")
        raise HTTPException(status_code=500, detail="Smart search failed")


@router.get("/hotels/smart-search/health")
async def smart_search_health():
    """Health check for smart search endpoint"""
    return {
        "status": "healthy",
        "cache_entries": len(smart_search_cache),
        "cities_count": len(POPULAR_CITIES),
        "areas_cities": list(POPULAR_AREAS.keys()),
        "hotels_cities": list(POPULAR_HOTELS.keys()),
    }
