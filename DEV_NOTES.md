# Development Notes - TravelSearch Metasearch Platform

**Date:** December 6, 2025  
**Issues Fixed:** Backend Connection + Pune Airport Autocomplete

---

## 🎯 Issues Resolved

### Issue #1: Backend Connection Refused ✅

**Problem:**  
Frontend was attempting to call `http://localhost:8001/api/search/flights` from the browser, resulting in `ERR_CONNECTION_REFUSED` because:
- The application runs in a cloud/preview environment
- Browser requests to `localhost:8001` fail in this context
- Frontend needed to use the external preview URL instead

**Solution:**  
Updated `/app/apps/frontend/.env.local`:
```bash
# Before
NEXT_PUBLIC_API_URL=http://localhost:8001

# After
NEXT_PUBLIC_API_URL=https://busway-planner.preview.emergentagent.com
```

**Technical Details:**
- Next.js environment variables prefixed with `NEXT_PUBLIC_` are embedded at build time
- The `AirportAutocomplete` and search results pages use this variable for API calls
- Backend is accessible via the preview URL with `/api` prefix (Kubernetes ingress routing)
- Rebuilt frontend to pick up the new environment variable

**Verification:**
- ✅ Flight search now successfully calls backend API
- ✅ No ERR_CONNECTION_REFUSED errors in browser console
- ✅ Results page loads with real Amadeus flight data

---

### Issue #2: Pune Airport (PNQ) Not Found in Autocomplete ✅

**Problem:**  
When typing "pune" or "pu" in the airport search field, autocomplete showed "No airports found" despite Pune (PNQ) existing in the dataset.

**Root Cause:**  
This was actually caused by Issue #1. The autocomplete component calls `/api/airports?query=pune`, but this was failing due to the connection issue. Once the backend connection was fixed, Pune started showing correctly.

**Verification:**
- Dataset already contained Pune: `{"iata": "PNQ", "name": "Pune Airport", "city": "Pune", "country": "India"}`
- Backend API correctly returns Pune: `curl "http://localhost:8001/api/airports?query=pune"` returns PNQ
- After fixing frontend API URL, autocomplete works perfectly

**How Autocomplete Works:**
1. User types "pu" (minimum 2 chars)
2. Frontend debounces and calls `${API_URL}/api/airports?query=pu`
3. Backend searches dataset for matches in IATA, city, or name (case-insensitive)
4. Frontend displays results as "City, Country - IATA"
5. When selected, IATA code (PNQ) is passed to search, not the display string

**Flow Example:**
```
User types "pu" → API call → Returns [{iata:"PNQ", city:"Pune", country:"India"}]
→ Shows "Pune, India - PNQ" in dropdown
→ User selects → Field displays "Pune, India" → Search uses "PNQ"
```

---

## 🚀 How to Run Backend & Frontend Together

### Prerequisites
```bash
# Verify services are running
sudo supervisorctl status

# Expected output:
# backend    RUNNING
# frontend   RUNNING
# mongodb    RUNNING
```

### Backend (FastAPI - Port 8001)

**Service managed by supervisor:**
```bash
# Check status
sudo supervisorctl status backend

# Restart if needed
sudo supervisorctl restart backend

# View logs
tail -f /var/log/supervisor/backend.err.log
```

**Manual run (for debugging):**
```bash
cd /app/apps/backend
source /root/.venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Test backend directly:**
```bash
# Health check
curl http://localhost:8001/api/health

# Airport autocomplete
curl "http://localhost:8001/api/airports?query=pune"

# Flight search (PNQ → BOM)
curl -X POST http://localhost:8001/api/search/flights \
  -H "Content-Type: application/json" \
  -d '{
    "trip_type": "oneway",
    "origin": "PNQ",
    "destination": "BOM",
    "departure_date": "2025-12-07",
    "adults": 1,
    "cabin_class": "economy"
  }'
```

---

### Frontend (Next.js - Port 3000)

**Service managed by supervisor:**
```bash
# Check status
sudo supervisorctl status frontend

# Restart
sudo supervisorctl restart frontend

# View logs
tail -f /var/log/supervisor/frontend.err.log
```

**Manual build & run:**
```bash
cd /app/apps/frontend

# Install dependencies (if needed)
yarn install

# Build (required after .env changes)
yarn build

# Start production server
yarn start

# Or for development with hot reload
yarn dev
```

**Important:** After changing `.env.local`, you **must** rebuild:
```bash
cd /app/apps/frontend
yarn build
sudo supervisorctl restart frontend
```

---

## 📍 Airport Dataset Location & Structure

**File:** `/app/apps/backend/data/airports.json`

**Schema:**
```json
{
  "iata": "PNQ",
  "name": "Pune Airport",
  "city": "Pune",
  "country": "India"
}
```

**Pune Entry:**
```json
{"iata": "PNQ", "name": "Pune Airport", "city": "Pune", "country": "India"}
```

**Backend Endpoint:** `GET /api/airports?query={searchTerm}`

**Search Logic (airports.py):**
```python
# Case-insensitive search on:
# - IATA code
# - City name
# - Airport name
query = query_param.lower()
filtered = [
    a for a in airports 
    if query in a["iata"].lower() 
    or query in a["city"].lower() 
    or query in a["name"].lower()
]
```

**Testing Airport Search:**
```bash
# Test Pune
curl "http://localhost:8001/api/airports?query=pune"
# Returns: [{"iata":"PNQ","name":"Pune Airport","city":"Pune","country":"India"}]

# Test by IATA code
curl "http://localhost:8001/api/airports?query=pnq"
# Returns: Same result

# Test partial
curl "http://localhost:8001/api/airports?query=pu"
# Returns: Pune + other matches like "Punta Arenas"

# Test invalid
curl "http://localhost:8001/api/airports?query=xyz"
# Returns: []
```

---

## 🔍 Example Working URLs

### 1. Airport Autocomplete API
```bash
curl "http://localhost:8001/api/airports?query=pune"

# Response:
[
  {
    "iata": "PNQ",
    "name": "Pune Airport",
    "city": "Pune",
    "country": "India"
  }
]
```

### 2. Flight Search API (PNQ → BOM)
```bash
curl -X POST "http://localhost:8001/api/search/flights" \
  -H "Content-Type: application/json" \
  -d '{
    "trip_type": "oneway",
    "origin": "PNQ",
    "destination": "BOM",
    "departure_date": "2025-12-07",
    "adults": 1,
    "cabin_class": "economy"
  }'

# Response: (Real Amadeus data)
{
  "offers": [
    {
      "offer_id": "AMADEUS-1",
      "provider": "amadeus",
      "price": 4500.0,
      "currency": "INR",
      "segments": [...],
      "stops": 0,
      ...
    }
  ],
  "search_id": "...",
  "cached": false
}
```

### 3. Flight Search from Browser (via preview URL)
```
https://busway-planner.preview.emergentagent.com/flights/results?origin=PNQ&destination=BOM&departure_date=2025-12-07&adults=1&cabin_class=economy
```

### 4. Backend API Documentation
```
http://localhost:8001/api/docs
# OR via preview URL:
https://busway-planner.preview.emergentagent.com/api/docs
```

---

## 🧪 Testing Checklist

### Backend Tests
```bash
cd /app/apps/backend
pytest tests/ -v

# Specific test for airport search
pytest tests/test_airports_api.py -v
```

### Frontend Tests  
```bash
cd /app/apps/frontend

# Unit tests
yarn test

# E2E tests (requires running services)
yarn test:e2e
```

### Manual Testing Flow

**1. Test Autocomplete:**
- Open: https://busway-planner.preview.emergentagent.com
- Type "pu" in "From" field
- ✅ Should see "Pune, India - PNQ" in dropdown
- Select it
- ✅ Field should show "Pune, India"

**2. Test Flight Search:**
- From: Pune (PNQ)
- To: Mumbai (BOM)
- Date: Tomorrow
- Click "Search Flights"
- ✅ URL should have `origin=PNQ` (not "pune")
- ✅ Should show real flight results from Amadeus
- ✅ Console should show no errors

**3. Test Backend Connection:**
- Open browser DevTools → Network tab
- Perform a search
- ✅ Should see successful calls to `/api/airports` and `/api/search/flights`
- ✅ Both should return 200 OK
- ✅ No ERR_CONNECTION_REFUSED errors

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Browser (User)                                         │
│  https://busway-planner.preview.emergentagent.com        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Kubernetes Ingress / Nginx Proxy                       │
│  Routes:                                                │
│  • /api/* → Backend (port 8001)                         │
│  • /* → Frontend (port 3000)                            │
└──────────────┬────────────────────┬─────────────────────┘
               │                    │
               │                    │
       ┌───────▼────────┐   ┌──────▼──────┐
       │  FastAPI       │   │  Next.js    │
       │  Backend       │   │  Frontend   │
       │  Port 8001     │   │  Port 3000  │
       └───────┬────────┘   └─────────────┘
               │
               │
       ┌───────▼────────┐
       │  MongoDB       │
       │  Port 27017    │
       └────────────────┘
               │
       ┌───────▼────────────────────┐
       │  External APIs             │
       │  • Amadeus (Flights/Hotels)│
       │  • Duffel (Optional)       │
       │  • Aviasales (Affiliate)   │
       └────────────────────────────┘
```

---

## 🔧 Configuration Files

### Backend Configuration

**1. Environment Variables:** `/app/apps/backend/.env`
```bash
# Amadeus (Sandbox)
AMADEUS_API_KEY=RtEE8e3AA2kTTvjKdrJJjaODhn6TvYbm
AMADEUS_API_SECRET=ARAiO3MdHM2BpBGn
AMADEUS_BASE_URL=https://test.api.amadeus.com
AMADEUS_ENVIRONMENT=test

# Provider Selection
FLIGHT_PROVIDER=amadeus
HOTEL_PROVIDER=amadeus
```

**2. Config Module:** `/app/apps/backend/app/config.py`
```python
class Settings(BaseSettings):
    amadeus_api_key: str = "REPLACE_ME"
    amadeus_api_secret: str = "REPLACE_ME"
    # ...
    
    class Config:
        env_file = ".env"
```

### Frontend Configuration

**1. Environment Variables:** `/app/apps/frontend/.env.local`
```bash
NEXT_PUBLIC_API_URL=https://busway-planner.preview.emergentagent.com
```

**2. Usage in Components:**
```typescript
// AirportAutocomplete.tsx
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
const response = await fetch(`${apiUrl}/api/airports?query=${searchQuery}`)
```

---

## 🐛 Troubleshooting

### Issue: Changes to .env.local not reflected

**Solution:**
```bash
cd /app/apps/frontend
yarn build  # Rebuild to embed new env vars
sudo supervisorctl restart frontend
```

### Issue: "No airports found" in autocomplete

**Check:**
1. Backend is running: `curl http://localhost:8001/api/health`
2. Airport endpoint works: `curl "http://localhost:8001/api/airports?query=pune"`
3. Frontend API URL is correct: Check `.env.local`
4. Browser console for API errors: DevTools → Console

### Issue: ERR_CONNECTION_REFUSED

**Check:**
1. Frontend is using correct API URL (not localhost in production)
2. Backend is accessible via the preview URL
3. CORS is configured correctly in backend
4. Supervisor services are running: `sudo supervisorctl status`

### Issue: Flight search returns no results

**Check:**
1. IATA codes are being passed (not city names): Check URL params
2. Date format is YYYY-MM-DD
3. Amadeus API credentials are valid
4. Backend logs: `tail -f /var/log/supervisor/backend.err.log`

---

## 📝 Key Files Modified

### Fixed Files

1. **`/app/apps/frontend/.env.local`**
   - Changed: `NEXT_PUBLIC_API_URL` from localhost to preview URL
   - Impact: Enables browser to reach backend API

2. **`/app/apps/frontend` (rebuilt)**
   - Action: `yarn build` to embed new environment variable
   - Impact: Next.js static site now has correct API URL

### Files That Worked Correctly (No Changes Needed)

1. **`/app/apps/backend/data/airports.json`**
   - Pune already present: `{"iata": "PNQ", ...}`
   
2. **`/app/apps/backend/app/routers/airports.py`**
   - Search logic already correct
   
3. **`/app/apps/frontend/components/search/AirportAutocomplete.tsx`**
   - Already using environment variable
   - Already passing IATA codes correctly
   
4. **`/app/apps/frontend/components/search/SearchBarV3.tsx`**
   - Already handling selected airports correctly

---

## 🎓 Lessons Learned

1. **Environment-Specific Configuration:**
   - Cloud/preview environments require external URLs, not localhost
   - Next.js `NEXT_PUBLIC_` variables must be set before build

2. **Cascading Issues:**
   - The Pune autocomplete issue was actually caused by the backend connection issue
   - Fixing the root cause (API URL) resolved both problems

3. **Testing in Production-Like Environments:**
   - Always test with the actual deployment URLs
   - Localhost testing can mask environment-specific issues

4. **Supervisor Management:**
   - Changes to .env require service restart
   - Next.js changes require rebuild + restart

---

## 📚 Additional Resources

- **Amadeus API Docs:** https://developers.amadeus.com/
- **Next.js Environment Variables:** https://nextjs.org/docs/basic-features/environment-variables
- **Airport IATA Codes:** https://www.iata.org/en/publications/directories/code-search/

---

## ✅ Verification Commands

```bash
# Quick health check (all should return 200 OK)
curl -I http://localhost:8001/api/health
curl -I http://localhost:3000

# Test Pune autocomplete
curl "http://localhost:8001/api/airports?query=pune" | jq '.[].city'
# Expected: "Pune"

# Test flight search with PNQ
curl -X POST http://localhost:8001/api/search/flights \
  -H "Content-Type: application/json" \
  -d '{"trip_type":"oneway","origin":"PNQ","destination":"BOM","departure_date":"2025-12-07","adults":1,"cabin_class":"economy"}' \
  | jq '.offers | length'
# Expected: Number > 0 (real Amadeus offers)

# Check services
sudo supervisorctl status | grep -E "backend|frontend"
# Expected: Both RUNNING
```

---

**Status:** ✅ Both issues resolved and thoroughly tested  
**Last Updated:** December 6, 2025
