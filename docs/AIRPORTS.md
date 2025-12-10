# Airport Dataset Documentation

## Overview

The application uses a comprehensive, production-ready airport dataset with 9,015+ airports worldwide, providing fast autocomplete with fuzzy matching and Amadeus API fallback.

---

## Dataset Information

### Current Dataset
- **File:** `/app/data/airports-full.json`
- **Airports:** 9,015 worldwide
- **Size:** 2.14 MB (minified JSON)
- **Last Updated:** December 2025

### Data Sources
1. **OurAirports** (Primary)
   - URL: https://ourairports.com/data/
   - More comprehensive metadata
   - Reliable scheduled service flags

2. **OpenFlights** (Secondary)
   - URL: https://github.com/jpatokal/openflights
   - Fills gaps in IATA coverage
   - Additional timezone data

### Data Fields
```json
{
  "iata": "PNQ",              // IATA code (3 letters)
  "icao": "VAPO",             // ICAO code (4 letters, optional)
  "name": "Pune Airport",     // Full airport name
  "city": "Pune",             // City name
  "country": "IN",            // ISO country code
  "iso_country": "IN",        // ISO country (redundant, for compatibility)
  "lat": 18.5821,             // Latitude
  "lon": 73.9197,             // Longitude
  "timezone": "Asia/Kolkata", // IANA timezone (optional)
  "type": "medium_airport",   // Airport type
  "aliases": [                // Search aliases (lowercase)
    "pune",
    "pune airport",
    "pnq",
    "vapo"
  ]
}
```

---

## Updating the Dataset

### When to Update
- **Weekly** (recommended): Catch new airports and changes
- **Monthly** (minimum): Keep data reasonably current
- **On-demand**: When users report missing airports

### How to Update

#### Method 1: Manual (Quick)
```bash
# SSH into production server
cd /app

# Run build script
python3 scripts/build_airports.py

# Restart backend to reload dataset
sudo supervisorctl restart backend

# Verify dataset loaded
curl "http://localhost:8001/api/airports?query=pune&limit=1"
```

#### Method 2: CI/CD (Automated)
Add to your CI pipeline:
```yaml
# .github/workflows/update-airports.yml
name: Update Airport Dataset

on:
  schedule:
    # Run every Monday at 2 AM UTC
    - cron: '0 2 * * 1'
  workflow_dispatch: # Allow manual trigger

jobs:
  update-airports:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Build airport dataset
        run: python3 scripts/build_airports.py
      
      - name: Commit changes
        run: |
          git config user.name "Airport Bot"
          git config user.email "bot@yourdomain.com"
          git add data/airports-full.json
          git commit -m "chore: update airport dataset [skip ci]" || exit 0
          git push
```

---

## API Endpoints

### 1. Search Airports
```http
GET /api/airports?query={query}&limit={limit}
```

**Parameters:**
- `query` (required): Search term (min 2 characters)
- `limit` (optional): Max results (1-50, default: 10)
- `nearby` (optional): Include nearby airports (boolean)
- `nearby_iata` (optional): IATA code for nearby search
- `radius_km` (optional): Search radius in km (50-500, default: 250)

**Response:**
```json
{
  "query": "pune",
  "count": 1,
  "source": "local",
  "results": [
    {
      "iata": "PNQ",
      "name": "Pune Airport",
      "city": "Pune",
      "country": "IN",
      "lat": 18.5821,
      "lon": 73.9197,
      "...": "..."
    }
  ]
}
```

**Examples:**
```bash
# Basic search
curl "http://localhost:8001/api/airports?query=shirdi&limit=5"

# With nearby airports
curl "http://localhost:8001/api/airports?query=pune&nearby=true&nearby_iata=PNQ&radius_km=250"
```

### 2. Get Nearby Airports
```http
GET /api/airports/{iata}/nearby?radius_km={radius}&limit={limit}
```

**Parameters:**
- `iata` (path): Center airport IATA code
- `radius_km` (optional): Search radius (50-500, default: 250)
- `limit` (optional): Max results (1-50, default: 10)

**Response:**
```json
{
  "center_iata": "PNQ",
  "radius_km": 250.0,
  "count": 5,
  "results": [
    {
      "airport": { /* airport object */ },
      "distance_km": 120.5
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8001/api/airports/PNQ/nearby?radius_km=250&limit=10"
```

---

## Search Behavior

### Fuzzy Matching
The search uses weighted fuzzy matching:

| Field     | Weight | Match Type                    |
|-----------|--------|-------------------------------|
| IATA      | 0.9    | Exact, starts-with, contains  |
| City      | 0.8    | Starts-with, contains         |
| Name      | 0.7    | Starts-with, contains         |
| Aliases   | 0.6    | Starts-with, contains         |

**Minimum Score:** 0.3 (configurable)

### Match Examples
- **Exact:** "PNQ" → Pune (score: 1.0)
- **Starts with:** "Pun" → Pune (score: 0.9)
- **Contains:** "une" → Pune (score: 0.7)
- **Alias:** "shirdi" → SAG (score: 0.9)

### Amadeus Fallback
If local search returns zero results:
1. Query Amadeus Locations API
2. Parse and unify response format
3. Cache for 10 minutes
4. Return to user

**Security:** Amadeus API keys never exposed to frontend.

---

## Performance

### Benchmarks
- **Dataset Load:** ~100ms (on backend startup)
- **Search Query:** < 25ms (target: 50ms)
- **Cache Hit:** 0ms (instant)
- **Amadeus Fallback:** ~500ms (network call)

### Optimization
- All searches use in-memory dataset (no DB)
- Simple O(n) scan with early termination
- Pre-computed aliases for fuzzy matching
- Amadeus results cached (10 min TTL)

### Scalability
- Current: 9,015 airports → ~25ms search
- 20,000 airports → ~50ms search (estimated)
- 50,000 airports → ~100ms search (consider indexing)

**Recommendation:** Current approach works well up to ~20k airports. For larger datasets, consider:
- Trie-based prefix index
- Elasticsearch/Algolia
- Dedicated search service

---

## Verification & Testing

### Required Airports (Must Pass)
```bash
# Test required Indian airports
echo "=== Testing Required Airports ==="

curl -s "http://localhost:8001/api/airports?query=shirdi&limit=1" | jq -r '.results[0].iata'
# Expected: SAG

curl -s "http://localhost:8001/api/airports?query=kolhapur&limit=1" | jq -r '.results[0].iata'
# Expected: KLH

curl -s "http://localhost:8001/api/airports?query=ratnagiri&limit=1" | jq -r '.results[0].iata'
# Expected: RTC

curl -s "http://localhost:8001/api/airports?query=chandigarh&limit=1" | jq -r '.results[0].iata'
# Expected: IXC

curl -s "http://localhost:8001/api/airports?query=pune&limit=1" | jq -r '.results[0].iata'
# Expected: PNQ
```

### Fuzzy Matching Tests
```bash
# Partial queries
curl "http://localhost:8001/api/airports?query=mum&limit=1"     # → BOM (Mumbai)
curl "http://localhost:8001/api/airports?query=del&limit=1"     # → DEL (Delhi)
curl "http://localhost:8001/api/airports?query=bang&limit=1"    # → BLR (Bangalore)
curl "http://localhost:8001/api/airports?query=chen&limit=1"    # → MAA (Chennai)
```

### Nearby Airports Test
```bash
# Find airports near Pune (within 250km)
curl "http://localhost:8001/api/airports/PNQ/nearby?radius_km=250&limit=5"

# Expected: BOM (Mumbai), NMI (Nashik), etc.
```

---

## Known Issues & Limitations

### Data Quality
1. **City Names:** Some airports have incorrect/outdated city names
   - Example: Shirdi Airport lists "Kakadi" as city
   - Aliases include "shirdi" to compensate

2. **Duplicates:** Some airports have multiple IATA codes
   - We keep the first occurrence only
   - Consider merging aliases in future

3. **Closed Airports:** Some closed airports may slip through filters
   - Run periodic cleanup
   - Add user reporting mechanism

### Search Limitations
1. **No Real-time Updates:** Dataset is static snapshot
   - New airports need manual update
   - Consider API-based solution for real-time

2. **Simple Fuzzy Matching:** Not as sophisticated as Fuse.js
   - Typo tolerance limited
   - Consider upgrading to Levenshtein distance

3. **Single Language:** Only English names/aliases
   - Consider adding localized names
   - Add transliteration for non-English queries

---

## Monitoring

### Health Checks
```bash
# Check dataset loaded
curl "http://localhost:8001/api/airports?query=test&limit=1"

# Should return 200 OK with results or empty array
```

### Logs to Watch
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log | grep -i airport

# Look for:
# - "✅ Loaded {N} airports from dataset" (on startup)
# - "Amadeus fallback returned {N} results" (fallback usage)
# - Any errors loading dataset
```

### Metrics to Track
- Search query latency (p50, p95, p99)
- Cache hit rate (local vs Amadeus)
- Most queried airports (analytics)
- Failed searches (zero results)

---

## Troubleshooting

### No Results for Known Airport
1. **Check dataset:** `grep "IATA_CODE" /app/data/airports-full.json`
2. **Check aliases:** Ensure city/name in aliases array
3. **Rebuild dataset:** Run `build_airports.py` to refresh
4. **Check logs:** Look for loading errors

### Slow Search Performance
1. **Check dataset size:** `wc -l /app/data/airports-full.json`
2. **Profile search:** Add timing logs to search function
3. **Consider indexing:** For >20k airports, use Trie or Elasticsearch

### Amadeus Fallback Not Working
1. **Check credentials:** Ensure production keys are set
2. **Check logs:** Look for "Amadeus fallback error"
3. **Test manually:** `curl` Amadeus API directly
4. **Check cache:** May be serving stale cached errors

---

## Future Enhancements

### Short Term (1-3 months)
- [ ] Add Fuse.js for better fuzzy matching
- [ ] Implement frontend caching (localStorage)
- [ ] Add user feedback for missing airports
- [ ] Track search analytics

### Medium Term (3-6 months)
- [ ] Multi-language support (localized names)
- [ ] Real-time updates from IATA database
- [ ] Search suggestions based on user history
- [ ] Popular airports quick access

### Long Term (6-12 months)
- [ ] Elasticsearch integration for scale
- [ ] AI-powered search (handle typos, context)
- [ ] Airport metadata (terminals, facilities)
- [ ] User-contributed corrections

---

## Support

### Questions?
- **Code:** Check `/app/scripts/build_airports.py` and `/app/apps/backend/app/routers/airports.py`
- **Data:** See OurAirports and OpenFlights documentation
- **API:** Test with `curl` examples above

### Reporting Issues
When reporting missing or incorrect airports:
1. Provide IATA code and correct details
2. Include search query that failed
3. Check if airport exists in source datasets
4. Suggest alias to add for fuzzy matching

---

**Last Updated:** December 2025
**Maintainer:** Development Team
**Dataset Version:** 1.0
