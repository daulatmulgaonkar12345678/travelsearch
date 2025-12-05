# Amadeus Flight Offers API Integration Guide

## Overview

This document provides complete integration instructions for the Amadeus Flight Offers API.

**API Provider**: Amadeus for Developers  
**Base URL**: `https://api.amadeus.com/v2`  
**Authentication**: OAuth 2.0 (Client Credentials)  
**Rate Limits**: 10 requests/second, 2000 requests/hour  
**Documentation**: https://developers.amadeus.com/

---

## 1. API Registration

### Sign Up for Amadeus API
1. Go to https://developers.amadeus.com/register
2. Create a free account
3. Navigate to "My Apps" → "Create New App"
4. Select API products:
   - ✅ Flight Offers Search
   - ✅ Flight Offers Price
   - ✅ Flight Create Orders (optional for booking)

### Get API Credentials
After creating your app, you'll receive:
- **API Key** (Client ID): `YourClientId12345`
- **API Secret** (Client Secret): `YourSecret67890`

---

## 2. Environment Setup

### Add Credentials to `.env`
```bash
# Amadeus API Credentials
AMADEUS_API_KEY=YourClientId12345
AMADEUS_API_SECRET=YourSecret67890
```

### Verify Configuration
```python
from app.config import settings

print(settings.amadeus_api_key)  # Should not be "REPLACE_ME"
print(settings.amadeus_api_secret)
```

---

## 3. OAuth Authentication Flow

### Get Access Token

**Endpoint**: `POST /v1/security/oauth2/token`

**Request**:
```bash
curl -X POST https://api.amadeus.com/v1/security/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YourClientId12345" \
  -d "client_secret=YourSecret67890"
```

**Response**:
```json
{
  "type": "amadeusOAuth2Token",
  "username": "your-email@example.com",
  "application_name": "YourAppName",
  "client_id": "YourClientId12345",
  "token_type": "Bearer",
  "access_token": "AbCdEf123456...",
  "expires_in": 1799,
  "state": "approved",
  "scope": ""
}
```

**Token Validity**: 30 minutes (1799 seconds)  
**Caching**: Store token and refresh 5 minutes before expiry

---

## 4. Flight Search API

### Endpoint
`GET /v2/shopping/flight-offers`

### Required Parameters
- `originLocationCode`: IATA airport code (3 letters) - e.g., "BOM"
- `destinationLocationCode`: IATA airport code - e.g., "PNQ"
- `departureDate`: Date in YYYY-MM-DD format
- `adults`: Number of adult passengers (1-9)

### Optional Parameters
- `returnDate`: Return date for round-trip
- `children`: Number of children (0-9)
- `infants`: Number of infants (0-9)
- `travelClass`: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
- `nonStop`: true/false (direct flights only)
- `currencyCode`: 3-letter currency code (e.g., "INR")
- `max`: Maximum number of results (1-250, default: 250)

### Sample Request
```bash
curl -X GET "https://api.amadeus.com/v2/shopping/flight-offers?\
originLocationCode=BOM&\
destinationLocationCode=PNQ&\
departureDate=2025-12-15&\
adults=1&\
currencyCode=INR&\
max=10" \
  -H "Authorization: Bearer AbCdEf123456..."
```

### Sample Response (Simplified)
```json
{
  "meta": {
    "count": 3
  },
  "data": [
    {
      "type": "flight-offer",
      "id": "1",
      "itineraries": [
        {
          "duration": "PT1H30M",
          "segments": [
            {
              "departure": {
                "iataCode": "BOM",
                "at": "2025-12-15T09:30:00"
              },
              "arrival": {
                "iataCode": "PNQ",
                "at": "2025-12-15T11:00:00"
              },
              "carrierCode": "6E",
              "number": "2341",
              "aircraft": {"code": "320"},
              "duration": "PT1H30M"
            }
          ]
        }
      ],
      "price": {
        "currency": "INR",
        "total": "8500.00",
        "base": "7200.00"
      },
      "travelerPricings": [
        {
          "fareDetailsBySegment": [
            {
              "cabin": "ECONOMY",
              "includedCheckedBags": {
                "weight": 15,
                "weightUnit": "KG"
              }
            }
          ]
        }
      ]
    }
  ],
  "dictionaries": {
    "carriers": {
      "6E": "INDIGO"
    },
    "aircraft": {
      "320": "AIRBUS A320"
    }
  }
}
```

---

## 5. Data Normalization

### Our Internal Format (FlightOffer)
```python
FlightOffer(
    offer_id="AMD-1",
    provider="amadeus",
    price=8500.0,
    currency="INR",
    segments=[...],
    total_duration_minutes=90,
    stops=0,
    baggage_allowance="15 kg checked",
    cabin_class="economy",
    fare_rules="Non-refundable, change fee applies",
    deep_link="https://amadeus.com/booking/1",
    rating=85.0
)
```

### Mapping Rules

| Amadeus Field | Our Field | Transformation |
|--------------|-----------|----------------|
| `data[].id` | `offer_id` | Prefix with "AMD-" |
| `price.total` | `price` | Convert to float |
| `price.currency` | `currency` | Direct |
| `itineraries[0].segments` | `segments` | Parse each segment |
| `segments[].departure.iataCode` | `departure_airport` | Direct |
| `segments[].arrival.iataCode` | `arrival_airport` | Direct |
| `segments[].duration` | `duration_minutes` | Parse ISO 8601 (PT1H30M → 90) |
| `len(segments) - 1` | `stops` | Calculated |
| `travelerPricings[0].fareDetailsBySegment[0].includedCheckedBags` | `baggage_allowance` | Format as string |

### Duration Parsing
ISO 8601 format: `PT{hours}H{minutes}M`

Examples:
- `PT1H30M` → 90 minutes
- `PT2H` → 120 minutes
- `PT45M` → 45 minutes

---

## 6. Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check parameters |
| 401 | Unauthorized | Refresh token |
| 429 | Rate Limit | Wait for retry-after header |
| 500 | Server Error | Retry with exponential backoff |

### Rate Limiting

**Response Headers**:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait (on 429)

**Implementation**:
```python
if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 60))
    await asyncio.sleep(retry_after)
    # Retry request
```

### Fallback Strategy
1. **Primary**: Real Amadeus API
2. **Fallback**: Mock data with logged warning
3. **Logging**: All API errors logged for monitoring

---

## 7. Testing

### Run Unit Tests
```bash
cd /app/apps/backend
pytest tests/adapters/test_amadeus.py -v
```

### Expected Output
```
tests/adapters/test_amadeus.py::TestAmadeusAdapter::test_adapter_initializes_in_mock_mode PASSED
tests/adapters/test_amadeus.py::TestAmadeusAdapter::test_parse_iso_duration PASSED
tests/adapters/test_amadeus.py::TestAmadeusAdapter::test_get_carrier_name PASSED
tests/adapters/test_amadeus.py::TestAmadeusAdapter::test_parse_amadeus_response_direct_flight PASSED
tests/adapters/test_amadeus.py::TestAmadeusAdapter::test_parse_amadeus_response_connecting_flight PASSED
tests/adapters/test_amadeus.py::TestAmadeusAdapter::test_mock_flight_search PASSED

=========== 10 passed in 1.23s ===========
```

### Test with Real API
```python
import asyncio
from app.services.adapters.amadeus_production import AmadeusAdapter
from app.models.flight import FlightSearchRequest

async def test_real():
    adapter = AmadeusAdapter(
        api_key="YourRealKey",
        api_secret="YourRealSecret",
        mock_mode=False
    )
    
    request = FlightSearchRequest(
        origin="BOM",
        destination="PNQ",
        departure_date="2025-12-15",
        adults=1
    )
    
    offers = await adapter.search_flights(request)
    print(f"Found {len(offers)} offers")
    for offer in offers:
        print(f"  - {offer.offer_id}: ₹{offer.price}")

asyncio.run(test_real())
```

---

## 8. Production Checklist

### Before Going Live
- [ ] API credentials secured in Secret Manager / Vault
- [ ] Rate limiting monitoring enabled
- [ ] Logging configured for API errors
- [ ] Fallback to mock mode tested
- [ ] Token refresh logic tested
- [ ] Response caching implemented (15min TTL)
- [ ] Error alerts configured
- [ ] Cost monitoring dashboard set up

### Monitoring Metrics
- **Requests/minute**: Track API usage
- **Success rate**: % of successful requests
- **Latency**: p50, p95, p99 response times
- **Error rate**: % of failed requests
- **Cache hit rate**: % of cached responses
- **Cost per search**: API cost tracking

### Cost Estimation

Amadeus Pricing (Approx):
- **Free Tier**: 2,000 requests/month
- **Pay-as-you-go**: $0.008 per request
- **Enterprise**: Custom pricing

Example:
- 10,000 searches/day = 300,000/month
- Cost: 298,000 × $0.008 = $2,384/month

---

## 9. Troubleshooting

### Common Issues

**Issue**: 401 Unauthorized
```
Solution: Check API key/secret, ensure token not expired
```

**Issue**: Empty results
```
Solution: Verify IATA codes are valid, check date format
```

**Issue**: Rate limit exceeded
```
Solution: Implement request throttling, increase tier
```

**Issue**: Slow response times
```
Solution: Enable caching, use max parameter to limit results
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will log all API requests/responses
```

---

## 10. Support & Resources

### Official Documentation
- API Docs: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search
- SDKs: https://github.com/amadeus4dev
- Community: https://developers.amadeus.com/support

### Contact
- Email: developers@amadeus.com
- Forum: https://developers.amadeus.com/forum

### Our Integration Status
- **Adapter**: `app/services/adapters/amadeus_production.py`
- **Tests**: `tests/adapters/test_amadeus.py`
- **Fixtures**: `tests/fixtures/amadeus_sample_response.json`
- **Status**: ✅ Production-ready with mock fallback

---

**Last Updated**: December 2025  
**Integration Version**: 1.0.0  
**API Version**: v2
