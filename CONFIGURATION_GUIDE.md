# Centralized Configuration System - Complete Guide

## 🎯 OVERVIEW

This system provides a **SINGLE SOURCE OF TRUTH** for all API credentials and configuration.

**Key Principle:** Update credentials in ONE place (`.env` file), and the entire backend automatically uses them.

---

## 📁 FILE STRUCTURE

```
/app/apps/backend/
├── .env                          # ← ONLY place to update credentials
├── app/
│   ├── core/
│   │   └── config.py             # ← CENTRALIZED CONFIG (imports .env)
│   ├── services/
│   │   └── adapters/
│   │       └── amadeus_flights_v2.py  # ← NEW adapter with debug logging
│   └── routers/
│       └── health_amadeus.py     # ← Health check endpoint
```

---

## 🔧 HOW TO UPDATE CREDENTIALS

### Step 1: Edit .env File
```bash
nano /app/apps/backend/.env
```

Update these lines:
```env
AMADEUS_API_KEY=your_new_key_here
AMADEUS_API_SECRET=your_new_secret_here
AMADEUS_BASE_URL=https://test.api.amadeus.com
AMADEUS_ENVIRONMENT=test
```

### Step 2: Clear Python Cache
```bash
cd /app/apps/backend
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
```

### Step 3: Restart Backend
```bash
sudo supervisorctl restart backend
```

### Step 4: Verify Configuration
```bash
curl -s "http://localhost:8001/api/health/amadeus" | python3 -m json.tool
```

Expected response:
```json
{
  "status": "success",
  "credentials": {
    "api_key_preview": "T6nGT3oh...Q3ve",
    "api_secret_preview": "v8mF...KLwp",
    "base_url": "https://test.api.amadeus.com",
    "environment": "test"
  },
  "token_obtained": true,
  "message": "Amadeus authentication successful"
}
```

---

## 🏗️ ARCHITECTURE

### Old System (BEFORE):
- ❌ Multiple files loading .env
- ❌ Hardcoded fallbacks
- ❌ Credential caching issues
- ❌ Silent failures (returned empty arrays)
- ❌ No debug logging

### New System (AFTER):
- ✅ Single centralized config file
- ✅ No fallbacks - credentials must be set
- ✅ No caching issues - always loads from .env
- ✅ Exceptions raised on failures
- ✅ Comprehensive debug logging at every step

---

## 🔍 KEY FILES EXPLAINED

### 1. `/app/apps/backend/app/core/config.py`
**The Single Source of Truth**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    amadeus_api_key: str
    amadeus_api_secret: str
    amadeus_base_url: str = "https://test.api.amadeus.com"
    # ... more settings
    
    model_config = SettingsConfigDict(
        env_file="/app/apps/backend/.env",
        env_file_encoding="utf-8"
    )

# Singleton instance
settings = Settings()
```

**How to use in your code:**
```python
from app.core.config import settings

api_key = settings.amadeus_api_key
```

### 2. `/app/apps/backend/app/services/adapters/amadeus_flights_v2.py`
**New Adapter with Full Debug Logging**

Key features:
- Logs credentials on initialization (masked)
- Logs every step of token request
- Logs full error responses
- Raises exceptions instead of returning empty arrays
- Validates credentials are not default values

### 3. `/app/apps/backend/app/routers/health_amadeus.py`
**Health Check Endpoint**

Test authentication without making search requests:
```bash
GET /api/health/amadeus
```

Returns:
- Current credentials being used (masked)
- Whether token fetch succeeded
- Full error details if failed

---

## 🚀 TESTING

### 1. Health Check
```bash
curl http://localhost:8001/api/health/amadeus
```

### 2. Test Flight Search
```bash
curl "http://localhost:8001/api/search/flights?origin=BOM&destination=DEL&departure_date=2025-12-20&trip_type=oneway&adults=1&cabin_class=economy"
```

### 3. Check Backend Logs
```bash
# Startup logs (shows config loading)
tail -100 /var/log/supervisor/backend.out.log

# Error logs
tail -100 /var/log/supervisor/backend.err.log
```

---

## 🔐 CURRENT CREDENTIALS (As of Last Update)

```env
# Amadeus Production Test Environment
AMADEUS_API_KEY=T6nGT3oh8k2kYsDJiGVjv4kSxDh2Q3ve
AMADEUS_API_SECRET=v8mF0xbVNpZkKLwp
AMADEUS_BASE_URL=https://test.api.amadeus.com
AMADEUS_ENVIRONMENT=test
```

✅ **Status:** Verified working - authentication successful as of Dec 15, 2025

---

## 🛠️ TROUBLESHOOTING

### Issue: "401 Unauthorized" errors

**Solution:**
1. Verify credentials in `.env` are correct
2. Clear Python cache
3. Restart backend
4. Test with health check endpoint

```bash
cd /app/apps/backend
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
sudo supervisorctl restart backend
sleep 5
curl http://localhost:8001/api/health/amadeus | python3 -m json.tool
```

### Issue: "No results" from searches

**Possible causes:**
1. ✅ Credentials working - Check via health endpoint
2. ⚠️ Amadeus test API has limited data
3. ⚠️ Route not available in test environment
4. ⚠️ Date too far in future
5. ⚠️ No flights available for that route/date

**How to diagnose:**
```bash
# Check if auth is working
curl http://localhost:8001/api/health/amadeus

# Try a major route with near-term date
curl "http://localhost:8001/api/search/flights?origin=BOM&destination=DEL&departure_date=2025-12-20&adults=1&cabin_class=economy"

# Check logs for detailed error messages
tail -50 /var/log/supervisor/backend.err.log
```

### Issue: Backend won't start

**Solution:**
```bash
# Check syntax errors
tail -100 /var/log/supervisor/backend.err.log

# Force rebuild
cd /app/apps/backend
find . -type d -name __pycache__ -exec rm -rf {} +
sudo supervisorctl stop backend
sleep 2
sudo supervisorctl start backend
sudo supervisorctl status backend
```

---

## 📊 LOGGING

The system now provides comprehensive logging:

### On Startup:
```
================================================
CONFIGURATION STATUS
================================================
✅ Amadeus API Key: T6nGT3oh...Q3ve
✅ Amadeus Base URL: https://test.api.amadeus.com
✅ Amadeus Environment: test
================================================
```

### On Authentication:
```
================================================
REQUESTING NEW AMADEUS ACCESS TOKEN
================================================
Token URL: https://test.api.amadeus.com/v1/security/oauth2/token
Client ID: T6nGT3oh...Q3ve
Client Secret: v8mF...KLwp
================================================
Token response status: 200
✅ AMADEUS TOKEN OBTAINED SUCCESSFULLY
================================================
```

### On Search:
```
Starting Amadeus flight search: BOM → DEL
✅ Token obtained, building search parameters...
Calling Amadeus API: https://test.api.amadeus.com/v2/shopping/flight-offers
Amadeus search response status: 200
✅ Amadeus returned 10 raw offers
✅ Amadeus search completed: 10 offers normalized
```

---

## ✅ VERIFICATION CHECKLIST

After updating credentials:

- [ ] Edit `/app/apps/backend/.env` with new credentials
- [ ] Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
- [ ] Restart backend: `sudo supervisorctl restart backend`
- [ ] Check health endpoint: `curl http://localhost:8001/api/health/amadeus`
- [ ] Verify "status": "success" and "token_obtained": true
- [ ] Test flight search with major route
- [ ] Check logs for any errors

---

## 🎓 BEST PRACTICES

1. **Never hardcode credentials** - Always use `settings` object
2. **Always import from centralized config** - `from app.core.config import settings`
3. **Test after changes** - Use health endpoint to verify
4. **Check logs** - They now provide full debug information
5. **Clear cache after .env changes** - Ensures fresh config loading

---

## 📞 SUPPORT

If you encounter issues:

1. Run health check: `curl http://localhost:8001/api/health/amadeus`
2. Check error logs: `tail -100 /var/log/supervisor/backend.err.log`
3. Verify .env file has correct credentials
4. Ensure no Python cache issues (clear and restart)

---

**Last Updated:** December 15, 2025  
**Status:** ✅ System operational with centralized config
