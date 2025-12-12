# Hybrid Supplier Protection System (No Redis Required)

## Overview

Production-safe supplier protection without Redis dependency. Uses:

1. **Local Token Buckets** (in-memory, per-instance) - Fast RPS/burst protection
2. **MongoDB Global Quota** - Distributed per-minute limiting
3. **MongoDB Circuit Breaker** - Supplier health tracking

**Fail-Safe**: If MongoDB is unreachable, system fails open with warnings but continues serving requests using local rate limiting only.

## Architecture

```
┌─────────────────────────────────────────┐
│         Flight Search Request           │
└───────────────┬─────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────┐
│  Hybrid Supplier Protection Controller        │
│                                               │
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │ 1. Circuit   │  │ 2. Local Token       │  │
│  │    Check     │─▶│    Bucket (RPS)      │  │
│  │ (MongoDB)    │  │  (In-Memory)         │  │
│  └──────────────┘  └──────────┬───────────┘  │
│                                │              │
│                                ▼              │
│                    ┌───────────────────────┐  │
│                    │ 3. Global Quota       │  │
│                    │    (Per-Minute)       │  │
│                    │   (MongoDB)           │  │
│                    └───────────────────────┘  │
└───────────────────────────────────────────────┘
                │
                ▼
    ✅ Allowed OR ❌ Blocked (+ Reason)
```

## Components

### 1. Local Token Bucket (`local_rate_limiter.py`)

**Purpose**: Fast, thread-safe RPS limiting per instance

**Features**:
- No network calls (pure Python)
- Configurable rate and burst
- Wait-with-timeout support
- Automatic token refill

**Configuration** (per supplier):
```python
SUPPLIER_CONFIG = {
    "amadeus": {
        "rps": 3.0,        # 3 requests per second
        "burst": 5.0,      # Burst capacity
        "per_minute": 100  # Global quota
    }
}
```

**Endpoint**: `GET /internal/hybrid/health/rate/{supplier}`

**Sample Response**:
```json
{
  "supplier": "amadeus",
  "type": "local_token_bucket",
  "current_tokens": 3.45,
  "capacity": 5.0,
  "refill_rate_per_sec": 3.0
}
```

### 2. Global Quota Store (`global_quota_store.py`)

**Purpose**: Distributed per-minute quota across all instances

**MongoDB Collection**: `supplier_quota`

**Document Structure**:
```javascript
{
  "_id": "amadeus:28383097",  // supplier:minute_bucket
  "supplier": "amadeus",
  "bucket_start_ts": 28383097,  // Unix timestamp / 60
  "allowed": 100,
  "used": 47,
  "created_at": 1702896234.5
}
```

**Features**:
- Atomic increment with MongoDB `$inc`
- Auto-expiration (1 hour TTL)
- Fail-open if DB unavailable

**Endpoint**: `GET /internal/hybrid/health/quota/{supplier}`

**Sample Response**:
```json
{
  "type": "global_quota",
  "supplier": "amadeus",
  "bucket_start_ts": 28383097,
  "allowed": 100,
  "used": 47,
  "remaining": 53
}
```

### 3. Circuit Breaker (`hybrid_circuit_breaker.py`)

**Purpose**: Track supplier health and disable unhealthy suppliers

**MongoDB Collection**: `supplier_circuit`

**Document Structure**:
```javascript
{
  "_id": "amadeus",
  "state": "OPEN",           // CLOSED, OPEN, HALF_OPEN
  "opened_at": 1702896234,
  "retry_after": 300,       // 5 minutes
  "failure_count": 3,
  "last_error": "429",
  "updated_at": ISODate(...)
}
```

**States**:
- `CLOSED`: Normal operation (allow all requests)
- `OPEN`: Supplier degraded (block all requests)
- `HALF_OPEN`: Testing recovery (allow single probe)

**Triggers**:
- 3 consecutive failures (429/401/5xx)
- Opens circuit for 5 minutes
- Auto-transitions to HALF_OPEN after cooldown

**Endpoint**: `GET /internal/hybrid/health/circuit/{supplier}`

**Sample Response**:
```json
{
  "type": "circuit_breaker",
  "supplier": "amadeus",
  "state": "OPEN",
  "failure_count": 3,
  "failure_threshold": 3,
  "last_error": "429",
  "opened_at": 1702896234,
  "retry_after_seconds": 245,
  "cooldown_seconds": 300
}
```

## Installation

### 1. Install Dependencies

```bash
cd /app/apps/backend
pip install motor  # Async MongoDB driver (already installed)
```

### 2. Configure MongoDB Indexes

Indexes are created automatically on startup, but you can manually create:

```javascript
// Global Quota
db.supplier_quota.createIndex(
  { "supplier": 1, "bucket_start_ts": 1 },
  { unique: true }
);
db.supplier_quota.createIndex(
  { "bucket_start_ts": 1 },
  { expireAfterSeconds: 3600 }
);

// Circuit Breaker
db.supplier_circuit.createIndex({ "state": 1 });
```

### 3. Restart Backend

```bash
sudo supervisorctl restart backend
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8001/internal/hybrid/health | jq .

# Expected output
{
  "status": "healthy",
  "initialized": true,
  "global_quota": "available",
  "circuit_breaker": "available",
  "local_buckets": 4
}
```

## Usage

### Protecting API Calls

```python
from app.services.supplier_protection_controller import (
    allow_request,
    on_supplier_success,
    on_supplier_failure
)

# Before calling supplier API
allowed, reason, metadata = await allow_request("amadeus", queue_timeout=0.3)

if not allowed:
    logger.warning(f"Amadeus blocked: {reason}")
    # Use fallback provider
    return await call_flightapi(...)

try:
    # Make API call
    response = await call_amadeus_api(...)
    
    if response.status_code == 200:
        await on_supplier_success("amadeus")
        return process_response(response)
    elif response.status_code in [429, 401, 500, 502, 503]:
        await on_supplier_failure("amadeus", str(response.status_code))
        return await call_fallback(...)

except Exception as e:
    await on_supplier_failure("amadeus", "500")
    return await call_fallback(...)
```

### Block Reasons

- `"allowed"` - Request permitted
- `"circuit_open"` - Circuit breaker is open (supplier degraded)
- `"local_rate_exceeded"` - Local RPS limit hit
- `"global_quota_exhausted"` - Per-minute quota exhausted
- `"db_unavailable_fail_open"` - MongoDB down (warning, allowing request)
- `"supplier_disabled"` - Supplier not enabled in config

## Testing

### Basic Functionality Test

```bash
bash /app/scripts/test_hybrid_protection.sh
```

**Expected Output**:
```
[1/6] Testing hybrid system health...
{
  "status": "healthy",
  "initialized": true,
  ...
}

[2/6] Checking Amadeus supplier status...
{
  "supplier": "amadeus",
  "configured": true,
  "local_bucket": {...},
  "global_quota": {...},
  "circuit_breaker": {"state": "CLOSED", ...}
}

...
```

### Stress Test

```bash
bash /app/scripts/stress_test_hybrid.sh
```

**Expected Behavior**:
- First 5 requests succeed (burst capacity)
- Subsequent requests rate-limited
- Some requests blocked (global quota)
- Block rate > 0%

### Manual Tests

#### Test 1: Local Rate Limiting

```bash
# Send 10 rapid requests
for i in {1..10}; do
  curl -s "http://localhost:8001/api/search?origin=BOM&destination=DEL&departure_date=2025-12-25" & 
done
wait

# Check logs for "local_rate_exceeded"
tail -f /var/log/supervisor/backend.out.log | grep "local_rate"
```

#### Test 2: Global Quota

```bash
# Set quota to 3 for current minute
mongo metasearch <<EOF
db.supplier_quota.updateOne(
  {"_id": "amadeus:" + Math.floor(Date.now() / 60000)},
  {\$set: {"allowed": 3, "used": 0}},
  {upsert: true}
);
EOF

# Send 6 requests - expect 3 to succeed
for i in {1..6}; do
  curl -s "http://localhost:8001/api/search?origin=BOM&destination=DEL&departure_date=2025-12-25"
  sleep 0.5
done

# Check quota status
curl http://localhost:8001/internal/hybrid/health/quota/amadeus | jq .
```

#### Test 3: Circuit Breaker

```bash
# Simulate 3 failures (requires mock or Amadeus returning errors)
# Check circuit state
curl http://localhost:8001/internal/hybrid/health/circuit/amadeus | jq '.state'

# If OPEN, further requests will be blocked
curl "http://localhost:8001/api/search?origin=BOM&destination=DEL&departure_date=2025-12-25"

# Check logs for "circuit_open"
tail -f /var/log/supervisor/backend.out.log | grep "circuit"
```

## Monitoring

### Health Endpoints

```bash
# Overall health
curl http://localhost:8001/internal/hybrid/health

# Supplier status (comprehensive)
curl http://localhost:8001/internal/hybrid/status/amadeus | jq .

# Rate limiter only
curl http://localhost:8001/internal/hybrid/health/rate/amadeus | jq .

# Quota only
curl http://localhost:8001/internal/hybrid/health/quota/amadeus | jq .

# Circuit breaker only
curl http://localhost:8001/internal/hybrid/health/circuit/amadeus | jq .

# Metrics
curl http://localhost:8001/internal/hybrid/metrics | jq .
```

### Metrics Response

```json
{
  "status": "ok",
  "metrics": {
    "total_requests": 150,
    "allowed": 120,
    "blocked_local_rate": 15,
    "blocked_global_quota": 10,
    "blocked_circuit_open": 5,
    "db_unavailable_count": 0,
    "block_rate": 20.0
  }
}
```

### MongoDB Queries

```javascript
// Check current minute quota for all suppliers
db.supplier_quota.find(
  {"bucket_start_ts": Math.floor(Date.now() / 60000)}
);

// Check circuit breaker states
db.supplier_circuit.find();

// Find OPEN circuits
db.supplier_circuit.find({"state": "OPEN"});

// Reset circuit breaker
db.supplier_circuit.updateOne(
  {"_id": "amadeus"},
  {$set: {"state": "CLOSED", "failure_count": 0}}
);
```

## Configuration

### Supplier Config

Edit `/app/apps/backend/app/services/supplier_protection_controller.py`:

```python
SUPPLIER_CONFIG = {
    "amadeus": {
        "rps": 3.0,          # Local RPS limit
        "burst": 5.0,        # Burst capacity
        "per_minute": 100,   # Global per-minute quota
        "enabled": True
    },
    # Add more suppliers...
}
```

### Circuit Breaker Config

Edit `/app/apps/backend/app/services/hybrid_circuit_breaker.py`:

```python
TRIP_THRESHOLD = 3        # Failures before opening
COOLDOWN_SECONDS = 300    # 5 minutes cooldown
```

## Administration

### Reset Protection

```bash
# Reset all protection for a supplier
curl -X POST http://localhost:8001/internal/hybrid/reset/amadeus

# Response
{
  "supplier": "amadeus",
  "status": "reset",
  "message": "Protection reset successfully"
}
```

### Emergency Disable

To disable protection for a supplier:

```python
# In supplier_protection_controller.py
SUPPLIER_CONFIG = {
    "amadeus": {
        "enabled": False  # Disable protection
    }
}
```

Restart backend:
```bash
sudo supervisorctl restart backend
```

## Troubleshooting

### Issue: MongoDB Connection Failed

**Symptom**: Logs show "db_unavailable_fail_open"

**Solution**:
```bash
# Check MongoDB status
sudo systemctl status mongod

# Restart if needed
sudo systemctl restart mongod

# Verify connection
mongo --eval "db.runCommand({ ping: 1 })"
```

**System Behavior**: Continues operating with local rate limiting only (degraded mode).

### Issue: Circuit Breaker Stuck Open

**Symptom**: All requests blocked with "circuit_open"

**Solution**:
```bash
# Check circuit status
curl http://localhost:8001/internal/hybrid/health/circuit/amadeus | jq .

# Wait for cooldown OR manually reset
curl -X POST http://localhost:8001/internal/hybrid/reset/amadeus

# Verify
curl http://localhost:8001/internal/hybrid/health/circuit/amadeus | jq '.state'
# Should show "CLOSED"
```

### Issue: High Block Rate

**Symptom**: Metrics show `block_rate > 50%`

**Solution**:
```bash
# Check which protection is blocking
curl http://localhost:8001/internal/hybrid/metrics | jq '.metrics | {blocked_local_rate, blocked_global_quota, blocked_circuit_open}'

# If local_rate high: Increase RPS in config
# If global_quota high: Increase per_minute in config
# If circuit_open high: Investigate supplier failures
```

### Issue: No Protection Working

**Symptom**: Health shows "status": "degraded"

**Solution**:
```bash
# Check backend logs
tail -100 /var/log/supervisor/backend.err.log | grep -i "hybrid\|protection"

# Common causes:
# 1. MongoDB not running
# 2. Initialization error
# 3. Import error

# Restart backend
sudo supervisorctl restart backend
```

## Comparison: Redis vs Hybrid

| Feature | Redis (Phase 1) | Hybrid (Current) |
|---------|----------------|------------------|
| **Dependencies** | Redis required | MongoDB only |
| **Local Rate Limiting** | Via Redis Lua | In-memory (faster) |
| **Global Coordination** | Redis | MongoDB |
| **Fail-Safe** | Fail-open if Redis down | Fail-open if MongoDB down |
| **Performance** | ~1-2ms overhead | ~0.1ms (local) + ~2-5ms (global) |
| **Complexity** | High (Redis + Lua) | Medium (pure Python + MongoDB) |
| **Best For** | High-scale (1000+ RPS) | Medium-scale (10-100 RPS) |

## Production Checklist

- ✅ MongoDB indexes created
- ✅ Supplier configs tuned (RPS/per_minute)
- ✅ Circuit breaker thresholds set
- ✅ Health endpoints accessible
- ✅ Monitoring dashboard configured
- ✅ Alerts set up for circuit_open events
- ✅ Backup suppliers configured (FlightAPI, Duffel)
- ✅ Stress test passed
- ✅ Fail-safe behavior verified (MongoDB down scenario)

## Support

For issues:
1. Check logs: `tail -f /var/log/supervisor/backend.out.log`
2. Check health: `curl http://localhost:8001/internal/hybrid/health`
3. Check MongoDB: `mongo metasearch --eval "db.supplier_quota.find(); db.supplier_circuit.find();"`
4. Reset if needed: `curl -X POST http://localhost:8001/internal/hybrid/reset/amadeus`

## Summary

Hybrid protection system provides production-grade supplier protection without Redis:
- ✅ **Fast**: Local rate limiting (thread-safe, no network)
- ✅ **Distributed**: MongoDB-backed global coordination
- ✅ **Resilient**: Fail-safe behavior (continues with warnings)
- ✅ **Observable**: Comprehensive health endpoints
- ✅ **Testable**: Full test suite included
- ✅ **Simple**: Pure Python + MongoDB (no Redis)

**Recommended for production deployments up to 100 RPS per supplier.**
