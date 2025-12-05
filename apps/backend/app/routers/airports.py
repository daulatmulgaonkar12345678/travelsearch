from fastapi import APIRouter, Query
from typing import List, Optional
import json
from pathlib import Path
from functools import lru_cache

router = APIRouter()

@lru_cache(maxsize=1)
def load_airports():
    """Load airports data from JSON file with caching"""
    data_path = Path(__file__).parent.parent.parent / "data" / "airports.json"
    with open(data_path, 'r') as f:
        return json.load(f)


@router.get("/airports")
async def search_airports(
    query: str = Query(..., min_length=1, description="Search query (city, airport name, or IATA code)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return")
):
    """
    Search airports by city, name, or IATA code
    Returns empty list if query < 2 characters
    """
    # Return empty for very short queries
    if len(query) < 2:
        return []
    
    airports = load_airports()
    query_lower = query.lower()
    results = []
    
    for airport in airports:
        # Check IATA code (exact match, case-insensitive)
        if airport['iata'].lower() == query_lower:
            results.append(airport)
            continue
        
        # Check if query matches city (prefix or contains)
        if airport['city'].lower().startswith(query_lower) or query_lower in airport['city'].lower():
            results.append(airport)
            continue
        
        # Check if query matches airport name
        if query_lower in airport['name'].lower():
            results.append(airport)
            continue
        
        # Check country
        if query_lower in airport['country'].lower():
            results.append(airport)
    
    # Sort by relevance: exact IATA match, then city prefix, then others
    def sort_key(a):
        if a['iata'].lower() == query_lower:
            return (0, a['city'])
        elif a['city'].lower().startswith(query_lower):
            return (1, a['city'])
        else:
            return (2, a['city'])
    
    results.sort(key=sort_key)
    
    return results[:limit]


@router.get("/cities")
async def search_cities(
    query: str = Query(..., min_length=1, description="Search query for cities"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return")
):
    """
    Search cities only (for hotel search)
    Returns city names without IATA codes
    """
    if len(query) < 2:
        return []
    
    airports = load_airports()
    query_lower = query.lower()
    cities = set()
    results = []
    
    for airport in airports:
        # Avoid duplicates (same city might have multiple airports)
        city_key = f"{airport['city']}, {airport['country']}"
        if city_key in cities:
            continue
        
        # Check if query matches city
        if airport['city'].lower().startswith(query_lower) or query_lower in airport['city'].lower():
            cities.add(city_key)
            results.append({
                "city": airport['city'],
                "country": airport['country'],
                "display": city_key
            })
    
    # Sort by city name
    results.sort(key=lambda x: x['city'])
    
    return results[:limit]
