#!/bin/bash
#
# Test Hybrid Supplier Protection System
#
# Tests all components:
# 1. Local rate limiting (token bucket)
# 2. Global quota (MongoDB)
# 3. Circuit breaker (MongoDB)
# 4. End-to-end flow
#

set -e

BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"

echo "=========================================="
echo "Hybrid Protection System - Test Suite"
echo "=========================================="
echo "Backend: $BACKEND_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health check
echo "[1/6] Testing hybrid system health..."
curl -s "$BACKEND_URL/internal/hybrid/health" | jq .

echo ""

# Test 2: Check amadeus status
echo "[2/6] Checking Amadeus supplier status..."
curl -s "$BACKEND_URL/internal/hybrid/status/amadeus" | jq .

echo ""

# Test 3: Local rate limiter
echo "[3/6] Testing local rate limiter..."
echo "  Sending 10 rapid requests..."

for i in $(seq 1 10); do
    STATUS=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/search?origin=BOM&destination=DEL&departure_date=2025-12-25&adults=1" 2>&1 | tail -n 1)
    echo "  Request $i: HTTP $STATUS"
    sleep 0.1
done

echo ""
echo "  Rate limiter status after burst:"
curl -s "$BACKEND_URL/internal/hybrid/health/rate/amadeus" | jq .

echo ""

# Test 4: Global quota
echo "[4/6] Testing global quota..."
curl -s "$BACKEND_URL/internal/hybrid/health/quota/amadeus" | jq .

echo ""

# Test 5: Circuit breaker
echo "[5/6] Testing circuit breaker..."
curl -s "$BACKEND_URL/internal/hybrid/health/circuit/amadeus" | jq .

echo ""

# Test 6: Metrics
echo "[6/6] Testing metrics endpoint..."
METRICS=$(curl -s "$BACKEND_URL/internal/hybrid/metrics")

if echo "$METRICS" | jq -e '.metrics' &>/dev/null; then
    echo "  Total requests:"
    echo "$METRICS" | jq -r '.metrics.total_requests' | sed 's/^/    /'
    
    echo "  Allowed:"
    echo "$METRICS" | jq -r '.metrics.allowed' | sed 's/^/    /'
    
    echo "  Blocked (local rate):"
    echo "$METRICS" | jq -r '.metrics.blocked_local_rate' | sed 's/^/    /'
    
    echo "  Blocked (global quota):"
    echo "$METRICS" | jq -r '.metrics.blocked_global_quota' | sed 's/^/    /'
    
    echo "  Blocked (circuit open):"
    echo "$METRICS" | jq -r '.metrics.blocked_circuit_open' | sed 's/^/    /'
    
    echo "  Block rate:"
    echo "$METRICS" | jq -r '.metrics.block_rate' | sed 's/^/    /' | xargs printf "%.2f%%\n"
else
    echo "  Metrics not available"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "System Status:"

HEALTH=$(curl -s "$BACKEND_URL/internal/hybrid/health")

if echo "$HEALTH" | jq -e '.status == "healthy"' &>/dev/null; then
    echo -e "  ${GREEN}✅ Fully operational${NC}"
else
    echo -e "  ${YELLOW}⚠️  Degraded mode${NC}"
fi

echo ""
echo "Documentation:"
echo "  - README: /app/HYBRID_PROTECTION_README.md"
echo "  - Admin reset: curl -X POST $BACKEND_URL/internal/hybrid/reset/amadeus"
echo ""
