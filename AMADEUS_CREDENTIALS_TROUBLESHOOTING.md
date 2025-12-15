# Amadeus Credentials Troubleshooting Guide

## 🔴 CURRENT SITUATION

**Date:** December 15, 2025

Your Amadeus API credentials were recently renewed, and both the old and new credentials are currently showing as "invalid_client" when tested.

---

## 📊 CREDENTIAL STATUS

### Old Credentials (Now Invalid)
```
API Key: T6nGT3oh8k2kYsDJiGVjv4kSxDh2Q3ve
API Secret: v8mF0xbVNpZkKLwp
Status: ❌ INVALID (Deactivated after renewal)
```

### New Credentials (From Renewal)
```
API Key: 9ZgpDiUxU8d2TuAkiluFcMUrzOvwtwHA
API Secret: ugCJOblPa3oPi6LJ
Status: ⚠️ INVALID (Possible reasons below)
```

---

## 🔍 POSSIBLE REASONS FOR INVALID CREDENTIALS

### 1. **Activation Delay**
- Some API providers require 5-30 minutes for new credentials to activate
- **Action:** Wait 30 minutes and test again

### 2. **Wrong Environment**
- Credentials might be for Production instead of Test
- **Action:** Try changing to production URL or verify in Amadeus dashboard

### 3. **Copy/Paste Error**
- Special characters or spaces might have been included
- **Action:** Re-copy credentials carefully

### 4. **Account Issue**
- The Amadeus account might have billing/activation issues
- **Action:** Check Amadeus dashboard for account status

### 5. **API Key Format Changed**
- Amadeus might have changed their authentication method
- **Action:** Check Amadeus documentation for updates

---

## ✅ TESTING COMMANDS

### Test Current Configuration
```bash
curl http://localhost:8001/api/health/amadeus | python3 -m json.tool
```

### Test Credentials Directly (Test Environment)
```bash
curl -X POST "https://test.api.amadeus.com/v1/security/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=9ZgpDiUxU8d2TuAkiluFcMUrzOvwtwHA&client_secret=ugCJOblPa3oPi6LJ"
```

### Test Credentials Directly (Production Environment)
```bash
curl -X POST "https://api.amadeus.com/v1/security/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=9ZgpDiUxU8d2TuAkiluFcMUrzOvwtwHA&client_secret=ugCJOblPa3oPi6LJ"
```

**Expected Success Response:**
```json
{
  "type": "amadeusOAuth2Token",
  "username": "...",
  "application_name": "...",
  "client_id": "...",
  "token_type": "Bearer",
  "access_token": "...",
  "expires_in": 1799,
  "state": "approved"
}
```

**Current Error Response:**
```json
{
  "error": "invalid_client",
  "error_description": "Client credentials are invalid",
  "code": 38187,
  "title": "Invalid parameters"
}
```

---

## 🔧 IMMEDIATE ACTIONS TO TRY

### Option 1: Wait for Activation
```bash
# Wait 30 minutes, then test:
curl http://localhost:8001/api/health/amadeus | python3 -m json.tool
```

### Option 2: Try Production Environment
Edit `/app/apps/backend/.env`:
```env
AMADEUS_BASE_URL=https://api.amadeus.com
AMADEUS_ENVIRONMENT=production
```

Then restart:
```bash
cd /app/apps/backend
find . -type d -name __pycache__ -exec rm -rf {} +
sudo supervisorctl restart backend
sleep 5
curl http://localhost:8001/api/health/amadeus | python3 -m json.tool
```

### Option 3: Verify Credentials in Amadeus Dashboard
1. Log into: https://developers.amadeus.com
2. Go to "My Self-Service Workspace"
3. Check the API keys shown there
4. Verify they match what you have
5. Check if there are any activation requirements

### Option 4: Generate New Credentials
If the current ones still don't work:
1. Go to Amadeus dashboard
2. Generate a fresh set of credentials
3. Copy them carefully (no extra spaces)
4. Update the .env file
5. Follow the 3-step update process

---

## 📝 WHEN CREDENTIALS ARE WORKING

Once you get working credentials, update them with these simple steps:

### Step 1: Update .env
```bash
nano /app/apps/backend/.env
```

Update these lines with working credentials:
```env
AMADEUS_API_KEY=your_working_key
AMADEUS_API_SECRET=your_working_secret
AMADEUS_BASE_URL=https://test.api.amadeus.com  # or https://api.amadeus.com for production
```

### Step 2: Clear Cache & Restart
```bash
cd /app/apps/backend
find . -type d -name __pycache__ -exec rm -rf {} +
sudo supervisorctl restart backend
```

### Step 3: Verify
```bash
sleep 5
curl http://localhost:8001/api/health/amadeus | python3 -m json.tool
```

You should see:
```json
{
  "status": "success",
  "token_obtained": true,
  "message": "Amadeus authentication successful"
}
```

---

## 🆘 IF NOTHING WORKS

### Contact Amadeus Support
- **Email:** developers@amadeus.com
- **Dashboard:** https://developers.amadeus.com/support
- **Mention:**
  - Your client ID
  - That credentials show as "invalid_client"
  - That you recently renewed credentials
  - Request activation confirmation

### Temporary Workaround
Until Amadeus credentials work, the system will:
- Automatically fall back to FlightAPI (already configured)
- Log detailed errors for debugging
- Continue to serve requests

---

## 📋 CURRENT CONFIGURATION STATUS

✅ **Centralized Config:** Implemented and working  
✅ **Health Check Endpoint:** `/api/health/amadeus` available  
✅ **Debug Logging:** Full credential loading logs active  
✅ **Cache Clearing:** Completed  
✅ **Backend:** Running and ready  
⚠️ **Amadeus Auth:** Waiting for valid credentials  

**Current .env settings:**
- API Key: 9ZgpDiUxU8d2TuAkiluFcMUrzOvwtwHA (last 4: twHA)
- API Secret: ugCJOblPa3oPi6LJ (last 4: i6LJ)
- Base URL: https://test.api.amadeus.com
- Environment: test

---

## 📞 NEXT STEPS FOR USER

1. **Wait 30 minutes** for potential activation delay
2. **Test again** using health check endpoint
3. **Check Amadeus dashboard** to verify credentials and account status
4. **Try production environment** if test doesn't work
5. **Contact Amadeus support** if credentials still invalid after 30+ minutes

Once working credentials are obtained, the system is ready to use them immediately with the 3-step process above.

---

**System Status:** ✅ Ready for credentials  
**Last Updated:** December 15, 2025  
**Configuration:** Centralized and optimized
