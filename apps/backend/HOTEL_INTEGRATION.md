# Hotel Provider Integrations Guide

## Overview

This document covers integration with hotel booking providers Trip.com and Booking.com/Agoda (via Kiwi aggregator).

---

## 1. Trip.com Integration

### API Registration
1. Go to https://www.trip.com/affiliate/
2. Sign up for affiliate program
3. Get Partner ID, API Key, API Secret

### Authentication
**Method**: HMAC-SHA256 Signature

**Signature Generation**:
```python
# 1. Sort parameters alphabetically
params = {"city": "Mumbai", "rooms": 1}
sorted_params = sorted(params.items())

# 2. Build signature string
sig_string = "city=Mumbai&rooms=1&timestamp=1234567890"

# 3. Generate HMAC-SHA256
signature = hmac.new(api_secret.encode(), sig_string.encode(), hashlib.sha256).hexdigest()
```

### Environment Variables
```bash
TRIP_API_KEY=your_api_key
TRIP_API_SECRET=your_secret
TRIP_PARTNER_ID=your_partner_id
```

### Sample Request
```bash
curl -X GET "https://api.trip.com/partner/v1/hotels/search?\
city=Mumbai&checkIn=2025-12-15&checkOut=2025-12-18&adults=2&rooms=1" \
  -H "X-Api-Key: your_api_key" \
  -H "X-Signature: generated_signature" \
  -H "X-Timestamp: 1234567890"
```

### Response Format
```json
{
  "hotels": [
    {
      "hotelId": "12345",
      "hotelName": "Grand Plaza Hotel",
      "address": "123 Main St",
      "starRating": 4.5,
      "userRating": 8.7,
      "rooms": [
        {
          "roomType": "Deluxe King",
          "price": {"total": 4500, "perNight": 4500, "currency": "INR"},
          "amenities": ["WiFi", "Breakfast"]
        }
      ]
    }
  ]
}
```

---

## 2. Booking.com / Agoda Integration (via Kiwi)

### API Registration
1. Go to https://tequila.kiwi.com/
2. Sign up and get API key
3. Access hotel aggregator endpoint

### Authentication
**Method**: API Key in header

### Environment Variables
```bash
KIWI_API_KEY=your_kiwi_api_key
```

### Sample Request
```bash
curl -X GET "https://api.tequila.kiwi.com/v2/search/hotels?\
city=Mumbai&checkin=2025-12-15&checkout=2025-12-18&adults=2" \
  -H "apikey: your_kiwi_api_key"
```

### Response Format
```json
{
  "data": [
    {
      "id": "67890",
      "provider": "booking.com",
      "name": "City View Inn",
      "address": "456 Park Ave",
      "stars": 3.5,
      "rating": 7.8,
      "price": {"total": 8400, "per_night": 2800},
      "amenities": ["WiFi", "Breakfast"],
      "deep_link": "https://booking.com/..."
    }
  ]
}
```

---

## Testing

### Run Unit Tests
```bash
cd /app/apps/backend
pytest tests/adapters/test_hotel_adapters.py -v
```

### Test with Real APIs
```python
# Set environment variables first
import asyncio
from app.services.adapters.trip_adapter import TripAdapter
from app.models.hotel import HotelSearchRequest

async def test():
    adapter = TripAdapter(mock_mode=False)
    request = HotelSearchRequest(
        city="Mumbai",
        check_in="2025-12-15",
        check_out="2025-12-18",
        adults=2,
        rooms=1
    )
    offers = await adapter.search_hotels(request)
    print(f"Found {len(offers)} hotels")

asyncio.run(test())
```

---

## Normalization

| Provider Field | Our Field | Notes |
|---------------|-----------|-------|
| hotelId/id | offer_id | Prefixed with provider |
| hotelName/name | hotel_name | Direct |
| starRating/stars | rating | 1-5 scale |
| userRating/rating | review_score | 0-10 scale |
| rooms[0].price.total | total_price | Float |
| rooms[0].amenities | amenities | List of strings |

---

**Status**: Phase 3B hotel adapters complete with tests
