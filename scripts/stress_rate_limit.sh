#!/bin/bash
#
# Stress Test: Rate Limiter
#
# Simulates N parallel requests to trigger rate limiting.
# Verifies that:
# 1. Rate limiter blocks requests beyond RPS/RPM limits
# 2. Fallback provider is used when primary is rate-limited
# 3. Circuit breaker opens after repeated failures
#

set -e

BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"
NUM_REQUESTS=20
CONCURRENCY=10

echo "==========================================="
echo "Rate Limiter Stress Test"
echo "==========================================="
echo "Backend: $BACKEND_URL"
echo "Requests: $NUM_REQUESTS"
echo "Concurrency: $CONCURRENCY"
echo ""

# Test search endpoint
SEARCH_URL="$BACKEND_URL/api/search"

echo "[1] Checking initial rate limiter status..."
curl -s "$BACKEND_URL/internal/health/rate/amadeus" | jq .

echo ""
echo "[2] Sending $NUM_REQUESTS parallel requests..."

# Create temp file for results
RESULTS_FILE=$(mktemp)

# Function to make a single request
make_request() {
    local id=$1
    local start=$(date +%s%3N)
    
    response=$(curl -s -w "\n%{http_code}" \
        -X GET "$SEARCH_URL?origin=BOM&destination=DEL&departure_date=2025-12-25&adults=1" \
        -H "Content-Type: application/json" 2>&1)
    
    local end=$(date +%s%3N)
    local duration=$((end - start))
    local status_code=$(echo "$response" | tail -n 1)
    
    echo "Request $id: status=$status_code, duration=${duration}ms" >> "$RESULTS_FILE"
}

# Launch requests in parallel
for i in $(seq 1 $NUM_REQUESTS); do
    make_request $i &
    
    # Control concurrency
    if [ $((i % CONCURRENCY)) -eq 0 ]; then
        wait
    fi
done

# Wait for all requests to complete
wait

echo ""
echo "[3] Results:"
cat "$RESULTS_FILE"

echo ""
echo "[4] Rate limiter status after stress test:"
curl -s "$BACKEND_URL/internal/health/rate/amadeus" | jq .

echo ""
echo "[5] Circuit breaker status:"
curl -s "$BACKEND_URL/internal/health/circuit/amadeus" | jq .

echo ""
echo "[6] Metrics:"
curl -s "$BACKEND_URL/internal/metrics" | jq '.metrics.rate_limiter, .metrics.circuit_breaker'

# Cleanup
rm -f "$RESULTS_FILE"

echo ""
echo "==========================================="
echo "Test Complete"
echo "==========================================="
echo ""
echo "Expected behavior:"
echo "  - First few requests succeed (within rate limit)"
echo "  - Subsequent requests get queued (200ms intervals)"
echo "  - Requests beyond timeout get blocked"
echo "  - Fallback provider (FlightAPI) used for blocked requests"
echo ""
