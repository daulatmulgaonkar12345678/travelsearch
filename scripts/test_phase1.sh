#!/bin/bash
# Phase 1 Testing Script

echo "================================================"
echo "  Phase 1 - Architecture & Scaffold Tests"
echo "================================================"
echo ""

# Test 1: Backend imports
echo "✓ Test 1: Backend imports..."
cd /app/apps/backend
python -c "from app.main import app; print('  ✅ FastAPI app imports successfully')" || exit 1

# Test 2: Check provider adapters
echo "✓ Test 2: Provider adapters..."
python -c "from app.services.adapters import AmadeusAdapter, LCCAdapter, HotelAdapter; print('  ✅ All adapters imported')" || exit 1

# Test 3: Check models
echo "✓ Test 3: Pydantic models..."
python -c "from app.models import FlightOffer, HotelOffer, User, ClickLog; print('  ✅ All models imported')" || exit 1

# Test 4: Frontend files exist
echo "✓ Test 4: Frontend structure..."
[ -f "/app/apps/frontend/package.json" ] && echo "  ✅ package.json exists" || exit 1
[ -f "/app/apps/frontend/app/page.tsx" ] && echo "  ✅ page.tsx exists" || exit 1
[ -f "/app/apps/frontend/components/search/SearchBar.tsx" ] && echo "  ✅ SearchBar.tsx exists" || exit 1

# Test 5: Documentation
echo "✓ Test 5: Documentation..."
[ -f "/app/ARCHITECTURE.md" ] && echo "  ✅ ARCHITECTURE.md exists" || exit 1
[ -f "/app/README.md" ] && echo "  ✅ README.md exists" || exit 1
[ -f "/app/.env.example" ] && echo "  ✅ .env.example exists" || exit 1

echo ""
echo "================================================"
echo "  ✅ All Phase 1 Tests Passed!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. cd /app/apps/backend && uvicorn app.main:app --reload --port 8001"
echo "  2. cd /app/apps/frontend && yarn dev"
echo "  3. Visit http://localhost:3000"
echo ""
