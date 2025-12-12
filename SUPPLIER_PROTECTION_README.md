# Supplier Protection System (Pattern 1 - Safe/Cost-Conscious)

## Overview

The Supplier Protection System implements comprehensive safeguards to prevent 401/429 errors and maintain service availability. It uses Redis-based distributed components to coordinate protection across all backend instances.

## Architecture

```
┌─────────────────┐
│  Flight Search   │
│    Request      │
└───────┬────────┘
        │
        ↓
┌───────┴───────────────────────────┐
│  Same-Day Policy Validator      │
│  (Before 12:00 IST → Tomorrow)  │
└────────────┬────────────────────┘
             │
             ↓
┌────────────┴──────────────────────────┐
│  Protected Orchestrator                 │
└────────────┬──────────────────────────┘
             │
      ┌──────┼──────┐
      │             │
      ↓             ↓
┌─────┴─────┐   ┌────┴─────┐
│  PRIMARY  │   │ FALLBACK │
│ (Amadeus)│   │(FlightAPI)│
└─────┬─────┘   └────┬─────┘
      │             │
      │   Circuit   │
      │   Breaker   │
      │      +      │
      │    Rate     │
      │   Limiter   │
      │             │
      │ (Redis)     │
      └─────┬───────┘
            │
            ↓
      ┌─────┴─────┐
      │   FINAL   │
      │ FALLBACK  │
      │   (Hub)   │
      └───────────┘
```

## Components

### 1. Redis Token-Bucket Rate Limiter

**Purpose:** Prevent 429 (Too Many Requests) errors by enforcing RPS/RPM limits globally.

**Configuration:**
```bash
AMADEUS_RPS=3                    # Requests per second
AMADEUS_RPM=100                  # Requests per minute
AMADEUS_BURST=5                  # Burst capacity
RATE_LIMIT_QUEUE_WAIT_MS=2000    # Max queue time
```

**Features:**
- Atomic token consumption via Lua script
- Gradual token refill (1 token/sec per RPS)
- Request queuing with 200ms poll intervals
- Automatic timeout after 2 seconds

**Health Check:**
```bash
curl http://localhost:8001/internal/health/rate/amadeus | jq .
```

### 2. Redis Circuit Breaker

**Purpose:** Prevent cascading failures by temporarily disabling unhealthy suppliers.

**Configuration:**
```bash
AMADEUS_CIRCUIT_FAILURES=3              # Failure threshold
AMADEUS_CIRCUIT_COOLDOWN_SECONDS=300    # 5-minute cooldown
```

**States:**
- `CLOSED`: Normal operation (all requests allowed)
- `OPEN`: Supplier degraded (requests blocked)
- `HALF_OPEN`: Testing recovery (single probe)

**Triggers:**
- 429 (rate limit)
- 401 (auth failure)
- 5xx (server errors)
- Timeouts

**Health Check:**
```bash
curl http://localhost:8001/internal/health/circuit/amadeus | jq .
```

### 3. Same-Day Policy Validator

**Purpose:** Enforce business rule for same-day flight searches.

**Rule:**
- Searches for flights departing **TODAY** are only allowed **AFTER 12:00 IST**
- Before 12:00 IST, the system auto-shifts to tomorrow and adds metadata

**Timezone:** Asia/Kolkata (IST = UTC+5:30)

### 4. Protected Orchestrator

**Flow:**
1. Validate same-day policy
2. Check Amadeus circuit breaker
3. Try Amadeus (with rate limiter)
4. If Amadeus fails/empty → FlightAPI (synchronous)
5. If FlightAPI fails/empty → Hub composition
6. Return results or no_results

**Background Enrichment:**
- When Amadeus succeeds, FlightAPI runs in background (non-blocking)
- Results merged if returned within 800ms

## Environment Variables

Add to `/app/apps/backend/.env`:

```bash
# Amadeus Configuration
AMADEUS_API_KEY=your_api_key
AMADEUS_API_SECRET=your_secret
AMADEUS_BASE_URL=https://api.amadeus.com
AMADEUS_RPS=3
AMADEUS_RPM=100
AMADEUS_BURST=5
AMADEUS_CIRCUIT_FAILURES=3
AMADEUS_CIRCUIT_COOLDOWN_SECONDS=300
AMADEUS_TIMEOUT_MS=2500

# FlightAPI Configuration
FLIGHT_ENABLED=true
FLIGHTPAPI_KEY=your_flightapi_key
FLIGHTAPI_BASE=https://api.flightapi.io
FLIGHTAPI_TIMEOUT_MS=3000

# Duffel & Kiwi (Optional)
DUFFEL_ENABLED=false
KIWI_ENABLED=false

# Redis
REDIS_URL=redis://redis:6379/0

# Feature Flag
SUPPLIER_PROTECTION=true

# Alerting (Optional)
MOCK_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
MOCK_PAGERDUTY_WEBHOOK=https://api.pagerduty.com/YOUR/WEBHOOK
```

## Installation

### 1. Install Redis Client

```bash
cd /app/apps/backend
pip install redis[hiredis]
pip freeze > requirements.txt
```

### 2. Start Redis

```bash
cd /app
docker-compose up -d redis
```

### 3. Verify Redis Connection

```bash
curl http://localhost:8001/internal/health/redis | jq .
```

### 4. Update Backend Startup

The protected orchestrator will initialize automatically when the backend starts.

## Testing

### 1. Test Amadeus Authentication

```bash
python3 /app/scripts/test_amadeus_auth.py
```

**Expected Output:**
```
[1] Testing OAuth token generation...
    Status: 200
    ✅ SUCCESS
    Token: eyJ0eXAiOiJKV1QiLCJh...
    Expires in: 1799s (29 minutes)

[2] Testing flight search API...
    Status: 200
    ✅ SUCCESS
    Offers: 15
    Sample price: 5500.00 INR

✅ All tests PASSED
```

### 2. Stress Test Rate Limiter

```bash
bash /app/scripts/stress_rate_limit.sh
```

**Expected Behavior:**
- First 3-5 requests succeed (within rate limit)
- Subsequent requests queued (200ms intervals)
- Requests beyond 2s timeout get blocked
- Fallback provider (FlightAPI) used for blocked requests

### 3. Test Circuit Breaker

Simulate repeated failures:

```bash
# Trigger 3+ failures to open circuit
for i in {1..5}; do
  curl -s "http://localhost:8001/api/search?origin=XXX&destination=YYY&departure_date=2025-12-25" > /dev/null
  echo "Request $i sent"
  sleep 1
done

# Check circuit state
curl http://localhost:8001/internal/health/circuit/amadeus | jq .
```

### 4. Test Same-Day Policy

**Before 12:00 IST:**
```bash
curl -X GET "http://localhost:8001/api/search?origin=BOM&destination=DEL&departure_date=$(date +%Y-%m-%d)&adults=1" | jq '.same_day_metadata'
```

**Expected Response:**
```json
{
  "same_day_check": true,
  "same_day_allowed": false,
  "same_day_shifted": true,
  "current_ist_time": "10:30",
  "requested_date": "2025-12-15",
  "suggested_date": "2025-12-16",
  "reason": "Same-day searches available after 12:00 IST"
}
```

## Health Endpoints

### Rate Limiter Status
```bash
GET /internal/health/rate/{supplier}
```

Response:
```json
{
  "supplier": "amadeus",
  "status": "ok",
  "capacity": 5,
  "current_tokens": 3.2,
  "refill_per_sec": 3,
  "last_refill_ago_ms": 150.5,
  "queue_timeout_ms": 2000
}
```

### Circuit Breaker Status
```bash
GET /internal/health/circuit/{supplier}
```

Response:
```json
{
  "supplier": "amadeus",
  "status": "ok",
  "state": "OPEN",
  "failures": 3,
  "failure_threshold": 3,
  "last_error": "429",
  "opened_at": 1702896234.5,
  "retry_after_seconds": 245.3
}
```

### Metrics
```bash
GET /internal/metrics
```

Response:
```json
{
  "status": "ok",
  "metrics": {
    "total_searches": 150,
    "amadeus_success": 120,
    "amadeus_fallback": 25,
    "flightapi_used": 20,
    "hub_composition_used": 5,
    "same_day_shifted": 10,
    "rate_limiter": {
      "allowed_total": 140,
      "blocked_total": 5,
      "queued_total": 25,
      "avg_queue_time_ms": 380.5
    },
    "circuit_breaker": {
      "failures_total": 30,
      "circuit_open_count": 3,
      "probes_total": 3,
      "probes_success": 2
    }
  }
}
```

## Troubleshooting

### Redis Connection Failed

**Symptom:** `Redis unavailable - allowing request (degraded mode)`

**Solution:**
```bash
# Check if Redis is running
docker-compose ps redis

# Start Redis
docker-compose up -d redis

# Test connection
redis-cli -h redis ping
```

### Amadeus 401 Errors

**Symptom:** Circuit breaker opens with `last_error: 401`

**Solution:**
```bash
# Test credentials
python3 /app/scripts/test_amadeus_auth.py

# If failed:
# 1. Verify credentials in Amadeus dashboard
# 2. Check account status and quota
# 3. Contact Amadeus support
```

### Amadeus 429 Errors

**Symptom:** Circuit breaker opens with `last_error: 429`

**Solution:**
```bash
# Check rate limiter configuration
curl http://localhost:8001/internal/health/rate/amadeus | jq .

# Reduce RPS/RPM in .env if needed
# AMADEUS_RPS=2
# AMADEUS_RPM=50

# Restart backend
sudo supervisorctl restart backend
```

### FlightAPI Not Working

**Symptom:** Fallback never triggers

**Solution:**
```bash
# Check if FlightAPI is enabled
grep FLIGHTAPI_ENABLED /app/apps/backend/.env

# Verify API key
grep FLIGHTAPI_KEY /app/apps/backend/.env

# Test FlightAPI directly
curl "https://api.flightapi.io/oneway/YOUR_KEY/BOM/DEL/2025-12-25/1"
```

## Support Templates

### Amadeus 401 Support Email

**Subject:** Amadeus API Authentication Failure - Account: [YOUR_ACCOUNT]

**Body:**
```
Hello Amadeus Support,

We are experiencing 401 Unauthorized errors with our Amadeus API integration.

Account Details:
- Client ID: [AMADEUS_API_KEY]
- Environment: Production
- Base URL: https://api.amadeus.com

Error Details:
- Error Code: 401 Unauthorized
- Endpoint: /v1/security/oauth2/token
- Timestamp: [TIMESTAMP]
- Request ID: [REQUEST_ID]

We have verified:
1. Credentials are correct
2. No recent changes to API keys
3. Previous keys also failing

Please check:
1. Account status (active/suspended)
2. API quota and limits
3. Any recent policy changes

Request Logs:
[ATTACH: test_amadeus_auth.py output]

Thank you,
[YOUR_NAME]
```

### Amadeus 429 Support Email

**Subject:** Amadeus API Rate Limit Increase Request - Account: [YOUR_ACCOUNT]

**Body:**
```
Hello Amadeus Support,

We are experiencing 429 Too Many Requests errors and would like to request a quota increase.

Current Limits (as configured):
- RPS: 3
- RPM: 100

Usage Patterns:
- Peak traffic: [TIME_RANGE]
- Avg requests/min: [NUMBER]
- Users: [NUMBER]

We have implemented:
1. Redis-based rate limiter
2. Circuit breaker (opens after 3 failures)
3. Fallback provider (FlightAPI)
4. Request queuing (2s timeout)

Requested Limits:
- RPS: 10
- RPM: 500

Metrics:
[ATTACH: curl http://localhost:8001/internal/metrics output]

Thank you,
[YOUR_NAME]
```

## Next Steps

### Phase 2: Additional Suppliers

- Enable Duffel adapter
- Enable Kiwi adapter
- Configure rate limiters for each

### Phase 3: Monitoring

- Set up Prometheus scraping
- Create Grafana dashboard
- Configure PagerDuty/Slack alerts

### Phase 4: Advanced Features

- Credential auto-rotation
- Dynamic rate limit adjustment
- Machine learning for failure prediction
- A/B testing for supplier selection
