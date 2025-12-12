#!/bin/bash
#
# Supplier Protection System - Quick Setup Script
#
# This script sets up and verifies the Phase 1 MVP implementation.
#

set -e

echo "=========================================="
echo "Supplier Protection System - Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Redis
echo "[1/6] Checking Redis..."
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✓${NC} Redis is installed"
    
    # Check if Redis is running
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓${NC} Redis is running"
    else
        echo -e "${YELLOW}⚠${NC} Redis is not running. Starting..."
        if command -v docker-compose &> /dev/null; then
            cd /app && docker-compose up -d redis
            echo -e "${GREEN}✓${NC} Redis started via Docker Compose"
        else
            sudo service redis-server start 2>/dev/null || echo -e "${RED}✗${NC} Failed to start Redis"
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC} Redis not found"
    echo "   Install options:"
    echo "   1. Docker: cd /app && docker-compose up -d redis"
    echo "   2. Local: sudo apt-get install redis-server"
    echo ""
    echo "   System will work in degraded mode (fail-open) without Redis."
fi

echo ""

# Step 2: Check Python dependencies
echo "[2/6] Checking Python dependencies..."
if python3 -c "import redis" &> /dev/null; then
    echo -e "${GREEN}✓${NC} redis Python module installed"
else
    echo -e "${YELLOW}⚠${NC} Installing redis module..."
    cd /app/apps/backend && pip install redis[hiredis] &> /dev/null
    echo -e "${GREEN}✓${NC} redis installed"
fi

echo ""

# Step 3: Verify configuration
echo "[3/6] Verifying configuration..."
if grep -q "SUPPLIER_PROTECTION=true" /app/apps/backend/.env; then
    echo -e "${GREEN}✓${NC} SUPPLIER_PROTECTION enabled"
else
    echo -e "${YELLOW}⚠${NC} SUPPLIER_PROTECTION not enabled"
fi

if grep -q "FLIGHTAPI_ENABLED=true" /app/apps/backend/.env; then
    echo -e "${GREEN}✓${NC} FlightAPI fallback enabled"
else
    echo -e "${YELLOW}⚠${NC} FlightAPI fallback disabled"
fi

echo ""

# Step 4: Test Amadeus authentication
echo "[4/6] Testing Amadeus authentication..."
python3 /app/scripts/test_amadeus_auth.py &> /tmp/amadeus_test.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Amadeus authentication and search working"
else
    if grep -q "✅ SUCCESS" /tmp/amadeus_test.txt; then
        echo -e "${GREEN}✓${NC} Amadeus authentication working"
        if grep -q "429" /tmp/amadeus_test.txt; then
            echo -e "${YELLOW}⚠${NC} Amadeus quota exceeded (429) - Protection system will handle this"
        else
            echo -e "${YELLOW}⚠${NC} Amadeus search failed - Check /tmp/amadeus_test.txt"
        fi
    else
        echo -e "${RED}✗${NC} Amadeus authentication failed"
        echo "   View details: cat /tmp/amadeus_test.txt"
    fi
fi

echo ""

# Step 5: Check backend status
echo "[5/6] Checking backend service..."
if curl -s http://localhost:8001/api/health &> /dev/null; then
    echo -e "${GREEN}✓${NC} Backend is running"
    
    # Check if protected orchestrator is initialized
    if curl -s http://localhost:8001/internal/health 2>&1 | grep -q "healthy\|degraded"; then
        echo -e "${GREEN}✓${NC} Protected orchestrator accessible"
    else
        echo -e "${YELLOW}⚠${NC} Protected orchestrator may not be initialized"
    fi
else
    echo -e "${RED}✗${NC} Backend is not running"
    echo "   Start it: sudo supervisorctl restart backend"
fi

echo ""

# Step 6: Summary
echo "[6/6] System Status Summary"
echo "────────────────────────────────────────"

# Check each component
redis_status="❌"
if redis-cli ping &> /dev/null; then
    redis_status="✅"
fi

backend_status="❌"
if curl -s http://localhost:8001/api/health &> /dev/null; then
    backend_status="✅"
fi

amadeus_status="❌"
if grep -q "✅ SUCCESS" /tmp/amadeus_test.txt 2>/dev/null; then
    amadeus_status="✅"
fi

flightapi_status="⚠️ "
if grep -q "FLIGHTAPI_ENABLED=true" /app/apps/backend/.env; then
    flightapi_status="✅"
fi

echo "  Redis:           $redis_status"
echo "  Backend:         $backend_status"
echo "  Amadeus Auth:    $amadeus_status"
echo "  FlightAPI:       $flightapi_status"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. If Redis is not running, start it (see step 1 above)"
echo "  2. Restart backend: sudo supervisorctl restart backend"
echo "  3. Test the system: bash /app/scripts/test_protected_system.sh"
echo "  4. View metrics: curl http://localhost:8001/internal/metrics | jq ."
echo ""
echo "Documentation:"
echo "  - Main README: /app/SUPPLIER_PROTECTION_README.md"
echo "  - Implementation: /app/PHASE1_MVP_COMPLETE.md"
echo ""
