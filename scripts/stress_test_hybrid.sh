#!/bin/bash
#
# Stress Test: Hybrid Protection System
#
# Simulates heavy load to verify:
# 1. Local rate limiting kicks in
# 2. Global quota enforcement
# 3. Circuit breaker trips after failures
#

set -e

BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"
NUM_REQUESTS=30
CONCURRENCY=10

echo "=========================================="
echo "Hybrid Protection - Stress Test"
echo "=========================================="
echo "Backend: $BACKEND_URL"
echo "Requests: $NUM_REQUESTS"
echo "Concurrency: $CONCURRENCY"
echo ""

# Reset protection first
echo "[0] Resetting protection state..."
curl -s -X POST "$BACKEND_URL/internal/hybrid/reset/amadeus" | jq -r '.message'

echo ""
echo "[1] Initial state:"
curl -s "$BACKEND_URL/internal/hybrid/status/amadeus" | jq '{local_bucket, global_quota, circuit_breaker: .circuit_breaker.state}'

echo ""
echo "[2] Sending $NUM_REQUESTS parallel requests (concurrency=$CONCURRENCY)..."

START_TIME=$(date +%s)
SUCCESS=0
FAILED=0

for i in $(seq 1 $NUM_REQUESTS); do
    (
        STATUS=$(curl -s -w "\n%{http_code}" \
            "$BACKEND_URL/api/search?origin=BOM&destination=DEL&departure_date=2025-12-25&adults=1" \
            2>&1 | tail -n 1)
        
        if [ "$STATUS" == "200" ]; then
            echo "✓ Request $i: SUCCESS"
        else
            echo "✗ Request $i: FAILED (HTTP $STATUS)"
        fi
    ) &
    
    # Control concurrency
    if [ $((i % CONCURRENCY)) -eq 0 ]; then
        wait
    fi
done

wait

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "[3] Test completed in ${ELAPSED}s"

echo ""
echo "[4] Final state:"
curl -s "$BACKEND_URL/internal/hybrid/status/amadeus" | jq '{local_bucket, global_quota, circuit_breaker: {state: .circuit_breaker.state, failures: .circuit_breaker.failure_count}}'

echo ""
echo "[5] Metrics:"
curl -s "$BACKEND_URL/internal/hybrid/metrics" | jq '.metrics | {total_requests, allowed, blocked_local_rate, blocked_global_quota, blocked_circuit_open, block_rate}'

echo ""
echo "=========================================="
echo "Stress Test Complete"
echo "=========================================="
echo ""
echo "Expected behavior:"
echo "  1. First ~5 requests succeed (local burst)"
echo "  2. Subsequent requests queued/rate-limited"
echo "  3. Global quota blocks after per-minute limit"
echo "  4. If many failures occur, circuit breaker opens"
echo ""
echo "Verify:"
echo "  - block_rate > 0% (some requests blocked)"
echo "  - Check MongoDB: db.supplier_quota.find() and db.supplier_circuit.find()"
echo ""
