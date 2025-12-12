#!/bin/bash
#
# Test Protected System
#
# Tests the supplier protection system end-to-end
#

set -e

echo "=========================================="
echo "Protected System - End-to-End Test"
echo "=========================================="
echo ""

API_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"

# Test 1: Health check
echo "[1/5] Testing health endpoints..."
echo "  - Overall health:"
curl -s "$API_URL/internal/health" | jq -r '.status, .redis' | sed 's/^/    /'

echo ""
echo "  - Redis health:"
curl -s "$API_URL/internal/health/redis" | jq -r '.status' | sed 's/^/    /'

echo ""

# Test 2: Rate limiter status
echo "[2/5] Testing rate limiter..."
curl -s "$API_URL/internal/health/rate/amadeus" | jq . 2>/dev/null || echo "    Rate limiter not configured (Redis unavailable)"

echo ""

# Test 3: Circuit breaker status  
echo "[3/5] Testing circuit breaker..."
curl -s "$API_URL/internal/health/circuit/amadeus" | jq . 2>/dev/null || echo "    Circuit breaker not configured (Redis unavailable)"

echo ""

# Test 4: Flight search with same-day policy
echo "[4/5] Testing flight search..."
TODAY=$(date +%Y-%m-%d)
RESPONSE=$(curl -s "$API_URL/api/search?origin=BOM&destination=DEL&departure_date=$TODAY&adults=1")

echo "  - Request status:"
echo "$RESPONSE" | jq -r '.status, .outcome' 2>/dev/null | sed 's/^/    /'

echo ""
echo "  - Same-day metadata:"
echo "$RESPONSE" | jq '.same_day_metadata' 2>/dev/null | sed 's/^/    /' || echo "    N/A"

echo ""

# Test 5: Metrics
echo "[5/5] Testing metrics endpoint..."
METRICS=$(curl -s "$API_URL/internal/metrics" 2>/dev/null)

if echo "$METRICS" | jq -e '.metrics' &>/dev/null; then
    echo "  - Total searches:"
    echo "$METRICS" | jq -r '.metrics.total_searches // "N/A"' | sed 's/^/    /'
    
    echo "  - Amadeus success:"
    echo "$METRICS" | jq -r '.metrics.amadeus_success // "N/A"' | sed 's/^/    /'
    
    echo "  - FlightAPI used:"
    echo "$METRICS" | jq -r '.metrics.flightapi_used // "N/A"' | sed 's/^/    /'
else
    echo "    Metrics not available (protected orchestrator not initialized)"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "System Status:"
if curl -s "$API_URL/internal/health" | jq -e '.redis == "connected"' &>/dev/null; then
    echo "  ✅ Fully operational (Redis connected)"
elif curl -s "$API_URL/api/health" | jq -e '.status == "healthy"' &>/dev/null; then
    echo "  ⚠️  Degraded mode (Redis unavailable)"
    echo "      - Backend is functional"
    echo "      - Rate limiting disabled (fail-open)"
    echo "      - Circuit breaker disabled (fail-open)"
    echo "      - To enable full protection: Start Redis"
else
    echo "  ❌ Backend not responding"
fi

echo ""
echo "For full protection, install and start Redis:"
echo "  Option 1 (Docker): cd /app && docker-compose up -d redis"
echo "  Option 2 (Local):  sudo apt-get install redis-server && sudo service redis-server start"
echo ""
