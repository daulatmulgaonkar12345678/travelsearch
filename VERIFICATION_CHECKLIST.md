# P0 Fix Verification Checklist

## ✅ Pre-Testing Verification (Completed)

- [x] `.env.local` updated with remote URL: `https://train-resolver.preview.emergentagent.com`
- [x] New `lib/api.ts` created with retry logic and timeout
- [x] All source files refactored to use `apiFetch()`
- [x] No `localhost:8001` references in source code (except fallback default)
- [x] Frontend rebuilt successfully
- [x] Frontend service restarted
- [x] Test suite created

## 🧪 Testing Checklist (To Be Done)

### 1. Basic Flight Search
- [ ] Search flights: JFK → LAX, tomorrow
- [ ] Verify results load
- [ ] Check browser console: URLs should show `metasearch-app.preview.emergentagent.com`
- [ ] No `ERR_CONNECTION_REFUSED` errors

### 2. Fallback Search (Critical Test)
- [ ] Search flights: ISK → RTC (should return 0 results)
- [ ] Verify fallback suggestions appear
- [ ] Check browser DevTools Network tab
- [ ] Confirm ALL API calls use `metasearch-app.preview.emergentagent.com`
- [ ] **NO** calls to `localhost:8001`

### 3. Airport Autocomplete
- [ ] Type "New" in origin field
- [ ] Verify suggestions appear
- [ ] Check network tab for `/api/airports` calls
- [ ] URL should be remote, not localhost

### 4. Date Range Pricing
- [ ] Search flights with valid route
- [ ] Verify date strip shows prices
- [ ] Check network tab for `/api/pricing/date-range` calls
- [ ] URL should be remote

### 5. Hotel Search (if applicable)
- [ ] Search hotels: New York, check-in tomorrow
- [ ] Verify results or appropriate message
- [ ] Check network tab for `/api/search/hotels` calls
- [ ] URL should be remote

### 6. Retry Behavior (Advanced)
- [ ] Check browser console logs
- [ ] Look for `[API] Retry` messages if any 5xx/429 errors occur
- [ ] Verify exponential backoff is working

## 🔍 What to Look For

### ✅ Success Indicators
- All API calls in Network tab show: `metasearch-app.preview.emergentagent.com`
- Console logs show: `[API] GET https://train-resolver.preview.emergentagent.com/api/...`
- Fallback searches work without connection errors
- Autocomplete suggestions load correctly

### ❌ Failure Indicators
- Any `localhost:8001` URLs in Network tab
- `ERR_CONNECTION_REFUSED` errors in console
- Fallback searches fail silently
- Console shows fetch errors to localhost

## 📝 Browser DevTools Tips

1. **Open DevTools:** F12 or Right-click → Inspect
2. **Network Tab:** 
   - Filter by "Fetch/XHR"
   - Look at Request URL column
   - All should start with `https://train-resolver.preview.emergentagent.com`
3. **Console Tab:**
   - Look for `[API]` log messages
   - Check for any red error messages
   - Verify retry messages if applicable

## 🚨 If Issues Found

### If still seeing `localhost:8001`:
1. Check if `.env.local` changes were applied
2. Verify frontend was rebuilt: `cd /app/apps/frontend && yarn build`
3. Verify frontend was restarted: `sudo supervisorctl restart frontend`
4. Clear browser cache and hard reload (Ctrl+Shift+R)

### If seeing connection refused errors:
1. Check backend is running: `sudo supervisorctl status backend`
2. Test backend directly: `curl https://train-resolver.preview.emergentagent.com/api/health`
3. Check backend logs: `tail -50 /var/log/supervisor/backend.*.log`

### If retry logic not working:
1. Check console for `[API] Retry` messages
2. Verify `api.ts` was properly created
3. Check imports in refactored files

## 📊 Expected Network Activity for Fallback Search

When searching ISK → RTC (should return 0 results):

```
1. POST /api/search/flights (ISK→RTC) → 0 results
2. GET /api/airports/ISK/nearby?radius_km=200
3. GET /api/airports/RTC/nearby?radius_km=200
4. POST /api/search/flights (alt date -3 days)
5. POST /api/search/flights (alt date -2 days)
6. POST /api/search/flights (alt date -1 day)
... (up to 4 total fallback attempts)
```

**ALL of these should use:** `https://train-resolver.preview.emergentagent.com`

## ✅ Sign-Off

Once all tests pass:
- [ ] Flight search works ✅
- [ ] Fallback search works ✅
- [ ] Airport autocomplete works ✅
- [ ] All URLs are remote ✅
- [ ] No localhost references ✅
- [ ] No connection errors ✅

**Ready to move to P1 tasks!**
