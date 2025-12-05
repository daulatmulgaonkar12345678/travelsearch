from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from app.config import settings, is_mock_mode

router = APIRouter()

class ProviderStatus(BaseModel):
    name: str
    enabled: bool
    mock_mode: bool
    type: str  # flight, hotel, both

@router.get("/providers", response_model=List[ProviderStatus])
async def get_providers():
    """Get list of available providers and their status"""
    providers = [
        ProviderStatus(
            name="amadeus",
            enabled=True,
            mock_mode=is_mock_mode("amadeus"),
            type="flight"
        ),
        ProviderStatus(
            name="lcc",
            enabled=True,
            mock_mode=is_mock_mode("lcc"),
            type="flight"
        ),
        ProviderStatus(
            name="trip.com",
            enabled=True,
            mock_mode=is_mock_mode("trip"),
            type="hotel"
        ),
        ProviderStatus(
            name="agoda",
            enabled=True,
            mock_mode=is_mock_mode("agoda"),
            type="hotel"
        ),
        ProviderStatus(
            name="kiwi",
            enabled=True,
            mock_mode=is_mock_mode("kiwi"),
            type="both"
        ),
    ]
    return providers

@router.get("/providers/{provider_name}")
async def get_provider_info(provider_name: str):
    """Get detailed info about a specific provider"""
    provider_map = {
        "amadeus": {
            "name": "Amadeus",
            "description": "Primary flight search provider with global coverage",
            "mock_mode": is_mock_mode("amadeus"),
            "api_docs": "https://developers.amadeus.com/",
            "required_keys": ["AMADEUS_API_KEY", "AMADEUS_API_SECRET"]
        },
        "lcc": {
            "name": "Low-Cost Carriers",
            "description": "Aggregated LCC flight data",
            "mock_mode": is_mock_mode("lcc"),
            "required_keys": ["LCC_API_KEY"]
        },
        "trip": {
            "name": "Trip.com",
            "description": "Hotel booking provider",
            "mock_mode": is_mock_mode("trip"),
            "api_docs": "https://www.trip.com/affiliate/",
            "required_keys": ["TRIP_API_KEY"]
        },
        "agoda": {
            "name": "Agoda",
            "description": "Hotel booking provider",
            "mock_mode": is_mock_mode("agoda"),
            "api_docs": "https://partners.agoda.com/",
            "required_keys": ["AGODA_API_KEY"]
        },
    }
    
    if provider_name not in provider_map:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return provider_map[provider_name]
