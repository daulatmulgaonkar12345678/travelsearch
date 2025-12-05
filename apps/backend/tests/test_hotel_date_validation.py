"""
Test hotel search date validation
"""
from datetime import date, timedelta
import pytest
from httpx import AsyncClient
import asyncio


def get_client():
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


client = get_client()


def test_hotel_search_check_in_must_be_tomorrow_or_later():
    """Check-in date must be at least tomorrow"""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    
    # Try check-in = today (should fail)
    response = client.get(
        "/api/search/hotels",
        params={
            "city": "Mumbai",
            "check_in": today.isoformat(),
            "check_out": day_after.isoformat(),
        }
    )
    assert response.status_code == 400
    assert "tomorrow" in response.json()["detail"].lower()
    
    # Try check-in = tomorrow (should pass)
    response = client.get(
        "/api/search/hotels",
        params={
            "city": "Mumbai",
            "check_in": tomorrow.isoformat(),
            "check_out": day_after.isoformat(),
        }
    )
    assert response.status_code == 200


def test_hotel_search_check_out_must_be_after_check_in():
    """Check-out must be after check-in"""
    tomorrow = date.today() + timedelta(days=1)
    
    # Try check-out = check-in (should fail)
    response = client.get(
        "/api/search/hotels",
        params={
            "city": "Mumbai",
            "check_in": tomorrow.isoformat(),
            "check_out": tomorrow.isoformat(),
        }
    )
    assert response.status_code == 400
    assert "after" in response.json()["detail"].lower()
    
    # Try check-out < check-in (should fail)
    yesterday = tomorrow - timedelta(days=1)
    response = client.get(
        "/api/search/hotels",
        params={
            "city": "Mumbai",
            "check_in": tomorrow.isoformat(),
            "check_out": yesterday.isoformat(),
        }
    )
    assert response.status_code == 400
    
    # Try check-out > check-in (should pass)
    day_after = tomorrow + timedelta(days=1)
    response = client.get(
        "/api/search/hotels",
        params={
            "city": "Mumbai",
            "check_in": tomorrow.isoformat(),
            "check_out": day_after.isoformat(),
        }
    )
    assert response.status_code == 200


def test_hotel_search_valid_dates_returns_results():
    """Valid dates should return search results"""
    tomorrow = date.today() + timedelta(days=1)
    checkout = tomorrow + timedelta(days=2)
    
    response = client.get(
        "/api/search/hotels",
        params={
            "city": "Mumbai",
            "check_in": tomorrow.isoformat(),
            "check_out": checkout.isoformat(),
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "offers" in data
    assert isinstance(data["offers"], list)
