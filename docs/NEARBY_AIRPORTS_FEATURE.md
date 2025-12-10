# Nearby Airports Feature - Implementation Guide

## Overview
The "Add nearby airports" feature allows users to include airports within 200-250km of their selected origin/destination to discover cheaper fares and better options, similar to Skyscanner.

---

## ✅ Backend Implementation (COMPLETE)

### 1. Existing API Endpoint
```
GET /api/airports/{IATA}/nearby?radius_km=250&limit=10
```

**Already Implemented:**
- ✅ Haversine distance calculation
- ✅ Filters commercial passenger airports only
- ✅ Excludes military/cargo/closed airports
- ✅ Returns sorted by distance
- ✅ Includes IATA codes, coordinates, airport details

**Example Response:**
```json
{
  "center_iata": "PNQ",
  "radius_km": 250.0,
  "count": 3,
  "results": [
    {
      "airport": {
        "iata": "BOM",
        "name": "Chhatrapati Shivaji International",
        "city": "Mumbai",
        "country": "IN",
        "lat": 19.0887,
        "lon": 72.8678
      },
      "distance_km": 120.5
    },
    {
      "airport": {
        "iata": "NMI",
        "name": "Nashik Airport",
        "city": "Nashik",
        "country": "IN",
        "lat": 20.1191,
        "lon": 73.9129
      },
      "distance_km": 100.3
    }
  ]
}
```

### 2. Flight Search with Multiple Airports

**Updated Model Support:**
```python
# In FlightSearchRequest
origin: Optional[str] = None              # Single IATA
destination: Optional[str] = None         # Single IATA

# NEW: Multi-airport support
origin_airports: Optional[List[str]] = None      # ["PNQ", "BOM", "NMI"]
destination_airports: Optional[List[str]] = None # ["DEL", "DXB"]

# Nearby airports flags
include_nearby_origin: bool = False
include_nearby_destination: bool = False
nearby_radius_km: float = 250.0
```

**Search Logic:**
1. If `include_nearby_origin=True`:
   - Call `/api/airports/{origin}/nearby?radius_km=250`
   - Build `origin_airports = [origin] + nearby_airports`
2. If `include_nearby_destination=True`:
   - Call `/api/airports/{destination}/nearby?radius_km=250`
   - Build `destination_airports = [destination] + nearby_airports`
3. Perform searches for all combinations
4. Deduplicate identical routes
5. Tag results with `source_airport` and `nearby` flag
6. Merge and rank results

### 3. Caching Strategy
- Nearby airport lookups: **10 minutes TTL** (already implemented)
- Flight search results: **20 seconds TTL** (already implemented)
- Cache key includes nearby airports flag

---

## 🎨 Frontend Implementation (TO DO)

### 1. UI Layout

**Placement:**
```tsx
<div className="space-y-4">
  {/* From Field */}
  <div>
    <label>From</label>
    <AirportAutocomplete
      value={origin}
      onChange={setOrigin}
      placeholder="Origin airport"
    />
    
    {/* Nearby Airports Toggle */}
    <div className="mt-2 flex items-center gap-2">
      <input
        type="checkbox"
        id="nearby-origin"
        checked={includeNearbyOrigin}
        onChange={(e) => setIncludeNearbyOrigin(e.target.checked)}
        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
      />
      <label htmlFor="nearby-origin" className="text-sm text-gray-700">
        Add nearby airports
        <Tooltip content="Include airports within 250 km for better prices">
          <InfoIcon className="inline ml-1 h-3 w-3" />
        </Tooltip>
      </label>
    </div>
  </div>
  
  {/* To Field */}
  <div>
    <label>To</label>
    <AirportAutocomplete
      value={destination}
      onChange={setDestination}
      placeholder="Destination airport"
    />
    
    {/* Nearby Airports Toggle */}
    <div className="mt-2 flex items-center gap-2">
      <input
        type="checkbox"
        id="nearby-destination"
        checked={includeNearbyDestination}
        onChange={(e) => setIncludeNearbyDestination(e.target.checked)}
        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
      />
      <label htmlFor="nearby-destination" className="text-sm text-gray-700">
        Add nearby airports
      </label>
    </div>
  </div>
</div>
```

### 2. State Management
```tsx
const [origin, setOrigin] = useState<Airport | null>(null)
const [destination, setDestination] = useState<Airport | null>(null)
const [includeNearbyOrigin, setIncludeNearbyOrigin] = useState(false)
const [includeNearbyDestination, setIncludeNearbyDestination] = useState(false)

interface Airport {
  iata: string
  name: string
  city: string
  country: string
}
```

### 3. Search Request Building
```tsx
const handleSearch = async () => {
  const searchParams = {
    origin: origin.iata,
    destination: destination.iata,
    departure_date: departureDate,
    return_date: returnDate,
    adults: adults,
    cabin_class: cabinClass,
    
    // NEW: Nearby airports flags
    include_nearby_origin: includeNearbyOrigin,
    include_nearby_destination: includeNearbyDestination,
    nearby_radius_km: 250
  }
  
  const response = await fetch('/api/search/flights', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(searchParams)
  })
  
  const results = await response.json()
  setFlightResults(results.offers)
}
```

### 4. Results Display - Nearby Airport Tags

**Flight Card Updates:**
```tsx
interface FlightOffer {
  // ... existing fields
  source_airport?: string     // Actual departure airport
  nearby_origin?: boolean     // True if not from selected origin
  nearby_destination?: boolean // True if not to selected destination
  original_origin?: string    // User's selected origin
  original_destination?: string // User's selected destination
}

// In FlightCard component
{offer.nearby_origin && (
  <div className="flex items-center gap-2 mt-2">
    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
      <MapPin className="h-3 w-3 mr-1" />
      Nearby airport
    </span>
    <span className="text-sm text-gray-600">
      Departs from {offer.source_airport} ({offer.source_airport_city})
    </span>
  </div>
)}

{/* Savings Hint */}
{offer.nearby_origin && offer.savings_amount > 0 && (
  <div className="flex items-center gap-1 text-green-600 text-sm">
    <TrendingDown className="h-4 w-4" />
    <span>Save ₹{offer.savings_amount} by flying from {offer.source_airport_city}</span>
  </div>
)}
```

### 5. Accessibility

**Requirements:**
- ✅ Keyboard accessible (Tab, Space, Enter)
- ✅ Screen reader labels
- ✅ Focus states
- ✅ ARIA attributes

```tsx
<div className="mt-2">
  <label className="flex items-center gap-2 cursor-pointer">
    <input
      type="checkbox"
      id="nearby-origin"
      checked={includeNearbyOrigin}
      onChange={handleToggle}
      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
      aria-describedby="nearby-origin-description"
    />
    <span className="text-sm text-gray-700 select-none">
      Add nearby airports
    </span>
    <Tooltip 
      id="nearby-origin-description"
      content="Include airports within 250 km for better prices"
      aria-label="Information about nearby airports"
    >
      <InfoIcon className="h-3 w-3 text-gray-400" aria-hidden="true" />
    </Tooltip>
  </label>
</div>
```

---

## 🔧 Backend Search Flow

### Scenario 1: Origin Nearby Enabled
```
User selects: PNQ (Pune)
User enables: "Add nearby airports" (origin)

Backend flow:
1. Call /api/airports/PNQ/nearby?radius_km=250
   → Returns: [BOM (120km), NMI (100km)]

2. Build origin_airports = ["PNQ", "BOM", "NMI"]

3. Search flights:
   - PNQ → DEL
   - BOM → DEL  ✅ Tag: nearby_origin=true
   - NMI → DEL  ✅ Tag: nearby_origin=true

4. Deduplicate and merge results

5. Add metadata:
   - source_airport: "BOM"
   - nearby_origin: true
   - original_origin: "PNQ"
   - savings_amount: calculateSavings(offer.price, cheapestFromPNQ.price)

6. Sort by best value (price + duration + nearby penalty)
```

### Scenario 2: Both Enabled
```
Origin: PNQ → [PNQ, BOM, NMI]
Destination: DEL → [DEL, GGN, DED]

Search matrix:
PNQ → DEL
PNQ → GGN ✅
PNQ → DED ✅
BOM → DEL ✅
BOM → GGN ✅
BOM → DED ✅
NMI → DEL ✅
NMI → GGN ✅
NMI → DED ✅

Total: 9 searches (parallelized)
Deduplicate identical routes
Tag all with appropriate flags
Merge and rank
```

### Performance Optimization
```python
# Parallel searches
async def search_nearby_flights(request):
    tasks = []
    
    for origin in origin_airports:
        for destination in destination_airports:
            task = search_flight_route(origin, destination, request)
            tasks.append(task)
    
    # Run all searches in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out errors and deduplicate
    valid_results = [r for r in results if not isinstance(r, Exception)]
    deduplicated = deduplicate_routes(valid_results)
    
    # Tag with nearby flags
    tagged_results = tag_nearby_airports(deduplicated, original_origin, original_destination)
    
    return tagged_results
```

---

## 💡 Savings Calculation

```python
def calculate_savings(offer, base_price):
    """
    Calculate savings compared to direct airport option
    
    Args:
        offer: Flight offer from nearby airport
        base_price: Price from original selected airport
    
    Returns:
        Savings amount (positive if cheaper)
    """
    if base_price is None:
        return 0
    
    savings = base_price - offer.price
    return max(0, savings)  # Only show positive savings
```

**Display Logic:**
```tsx
{offer.savings_amount > 0 && (
  <div className="text-green-600 text-sm font-medium">
    💡 Save ₹{offer.savings_amount.toLocaleString()} 
    flying from {offer.source_airport_city}
  </div>
)}
```

---

## 🎯 Sorting & Ranking

**Priority Rules:**
1. **Best/Cheapest Sort:**
   - Prioritize exact airport matches
   - Nearby airports ranked lower (penalty: +10% score)
   - Show savings hint if nearby is significantly cheaper

2. **Fastest Sort:**
   - Duration is king
   - Nearby airport penalty minimal

3. **Default Sort (Best):**
   - Balanced score = (price/1000) + (duration/60) + (nearby_penalty * 0.1)

**Example:**
```python
def calculate_rank_score(offer, is_nearby):
    base_score = (offer.price / 1000) + (offer.total_duration_minutes / 60)
    nearby_penalty = 0.5 if is_nearby else 0
    return base_score + nearby_penalty
```

---

## 🔍 Deduplication Logic

```python
def deduplicate_routes(offers):
    """
    Remove identical routes (same airports, times, airline)
    Keep the cheapest option per route
    """
    seen_routes = {}
    
    for offer in offers:
        # Build route key
        route_key = (
            offer.segments[0].departure_airport,
            offer.segments[-1].arrival_airport,
            offer.segments[0].departure_time.date(),
            offer.segments[0].carrier_code,
            offer.total_duration_minutes
        )
        
        # Keep cheapest
        if route_key not in seen_routes or offer.price < seen_routes[route_key].price:
            seen_routes[route_key] = offer
    
    return list(seen_routes.values())
```

---

## ❌ Error Handling

### Nearby Lookup Fails
```python
try:
    nearby_airports = await get_nearby_airports(origin, radius_km=250)
except Exception as e:
    logger.warning(f"Nearby airports lookup failed: {e}")
    # Fallback: Use only original airport
    nearby_airports = []

origin_airports = [origin] + nearby_airports
```

### Amadeus Rate Limit
```python
# Continue with successful searches
results = await asyncio.gather(*tasks, return_exceptions=True)
successful = [r for r in results if not isinstance(r, Exception)]

if len(successful) == 0:
    raise HTTPException(status_code=503, detail="Flight search temporarily unavailable")
```

### No Results from Nearby
```python
if not any(offer.nearby_origin for offer in results):
    # All results are from original airport
    # No special handling needed
    pass
```

---

## 📊 Analytics & Logging

**Track Usage:**
```python
logger.info(f"[NEARBY] query origin={origin} nearby_enabled={include_nearby_origin} nearby_count={len(nearby_airports)}")
logger.info(f"[NEARBY] results total={len(results)} nearby={sum(1 for r in results if r.nearby_origin)} savings_avg={avg_savings}")
```

**Metrics to Monitor:**
- % of searches with nearby enabled
- Average savings with nearby airports
- Most common nearby airport pairs
- Conversion rate (nearby vs direct)

---

## ✅ Success Criteria

**Functional:**
- [x] Backend `/api/airports/{IATA}/nearby` endpoint working
- [ ] Frontend toggles render correctly
- [ ] Multi-airport search works
- [ ] Results tagged correctly
- [ ] Deduplication working
- [ ] Savings hints display

**Performance:**
- [ ] Search completes in < 10 seconds (even with 9 routes)
- [ ] Caching reduces duplicate API calls
- [ ] No duplicate routes shown

**UX:**
- [ ] Default OFF (user must opt-in)
- [ ] Clear labeling of nearby results
- [ ] Savings hints when applicable
- [ ] Keyboard accessible
- [ ] Screen reader friendly

**Edge Cases:**
- [ ] No nearby airports found → silent fallback
- [ ] Rate limit hit → search still completes with available results
- [ ] Identical routes → deduplicated correctly

---

## 🚀 Implementation Checklist

### Backend (Partially Complete)
- [x] `/api/airports/{IATA}/nearby` endpoint
- [x] Haversine distance calculation
- [x] Commercial airport filtering
- [x] Caching (10 min TTL)
- [ ] Update `FlightSearchRequest` model with new fields
- [ ] Implement multi-airport search logic
- [ ] Add tagging for nearby results
- [ ] Implement deduplication
- [ ] Add savings calculation

### Frontend (To Do)
- [ ] Add "Add nearby airports" checkbox (origin)
- [ ] Add "Add nearby airports" checkbox (destination)
- [ ] Update search request building
- [ ] Add nearby airport tags to results
- [ ] Show savings hints
- [ ] Add tooltips with info
- [ ] Implement accessibility features
- [ ] Test keyboard navigation
- [ ] Add loading states

### Testing (To Do)
- [ ] Unit tests for nearby lookup
- [ ] Unit tests for deduplication
- [ ] Integration tests for multi-airport search
- [ ] UI tests for toggle behavior
- [ ] Performance tests (9 parallel searches)
- [ ] Accessibility tests

---

## 📚 Future Enhancements

**Short Term:**
- [ ] Remember user preference (local storage)
- [ ] Show nearby airport count in toggle label
- [ ] Animated map showing nearby airports

**Medium Term:**
- [ ] Price comparison chart (nearby vs direct)
- [ ] "Smart nearby" (auto-enable if saves > ₹1000)
- [ ] Filter by nearby airport in results

**Long Term:**
- [ ] Train ML model to predict best nearby combos
- [ ] Historical price analysis for nearby routes
- [ ] "Flexible origin" mode (any nearby)

---

**Status:** Backend infrastructure ready, frontend implementation pending
**Priority:** High - Major competitive feature
**Complexity:** Medium - Requires careful UX and performance optimization
