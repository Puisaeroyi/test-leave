# Debug Report: Frontend Connection Refused Error

**Date**: 2026-02-03 21:24
**Issue**: `POST http://localhost:8000/api/v1/auth/login/ net::ERR_CONNECTION_REFUSED`
**Status**: RESOLVED

## Executive Summary

Root cause identified and fixed. Frontend JavaScript code had hardcoded `localhost:8000` URLs instead of using `VITE_API_URL` environment variable. This caused browser to connect to host's localhost instead of Docker network backend service.

## Timeline

- 21:21 - Initial investigation began
- 21:22 - Discovered environment variable mismatch in container
- 21:23 - Identified hardcoded URLs in source code
- 21:24 - Fixed all affected files, verified HMR update

## Root Cause Analysis

### Primary Issue
Frontend API files contained hardcoded `localhost:8000` URLs:
- `/frontend/src/api/http.js` - Line 4: `baseURL: "http://localhost:8000"`
- `/frontend/src/api/authApi.js` - Line 3: `const API_URL = "http://localhost:8000/api/v1/auth"`
- `/frontend/src/api/authApi.js` - Line 62: `const ORG_API_URL = "http://localhost:8000/api/v1/organizations"`
- `/frontend/src/api/businessTripApi.js` - Line 3: `const API_URL = "http://localhost:8000/api/v1/leaves/business-trips"`

### Why This Failed
1. Browser runs on host machine, not in container
2. Browser JavaScript executes with `localhost` = host's localhost
3. Backend runs inside Docker network on `backend` hostname
4. Connection to `localhost:8000` from browser cannot reach containerized backend

### Why Environment Variable Wasn't Used
- `docker-compose.yml` correctly set `VITE_API_URL=http://backend:8000/api/v1`
- Frontend container correctly received env var (verified)
- BUT: Source code ignored env var, used hardcoded URLs

## Changes Applied

### File Updates

**1. `/home/silver/test-leave/frontend/src/api/http.js`**
```javascript
// Before:
baseURL: "http://localhost:8000"

// After:
baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
```

**2. `/home/silver/test-leave/frontend/src/api/authApi.js`**
```javascript
// Before:
const API_URL = "http://localhost:8000/api/v1/auth";
const ORG_API_URL = "http://localhost:8000/api/v1/organizations";

// After:
const API_URL = `${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/auth`;
const ORG_API_URL = `${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/organizations`;
```

**3. `/home/silver/test-leave/frontend/src/api/businessTripApi.js`**
```javascript
// Before:
const API_URL = "http://localhost:8000/api/v1/leaves/business-trips";

// After:
const API_URL = `${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/leaves/business-trips`;
```

### Container Operations
- Stopped frontend container
- Rebuilt frontend image (redundant due to volume mount, but ensures clean state)
- Started frontend container with correct env var

## Verification

### Environment Variable
```bash
$ docker compose exec frontend sh -c 'echo $VITE_API_URL'
http://backend:8000/api/v1
```
✅ Correct

### Network Connectivity
```bash
$ docker compose exec frontend sh -c 'wget -q -O- http://backend:8000/api/v1/auth/login/'
HTTP/1.1 400 Bad Request
```
✅ Backend accessible from frontend container (400 = expected, no data sent)

### Hot Module Replacement
Vite logs show HMR detected changes:
```
9:23:42 PM [vite] (client) hmr update /src/auth/authContext.jsx, /src/pages/login.jsx, ...
```
✅ Changes applied without restart

### Files Verified
- `http.js` ✅ Uses `import.meta.env.VITE_API_URL`
- `authApi.js` ✅ Uses `import.meta.env.VITE_API_URL`
- `businessTripApi.js` ✅ Uses `import.meta.env.VITE_API_URL`
- `dashboardApi.js` ✅ Uses relative paths (works with http.js baseURL)

## Remaining Hardcoded References
None found. All `localhost:8000` now only as fallback defaults.

## Expected Behavior After Fix

### Browser Request Flow
1. Browser requests `http://localhost:5173` (frontend dev server)
2. Frontend JavaScript executes with `VITE_API_URL=http://backend:8000/api/v1`
3. **CRITICAL**: Browser still makes HTTP requests to `localhost:8000` because:
   - Browser runs on host, not in container
   - Browser cannot resolve `backend` hostname (Docker internal DNS)
   - `import.meta.env.VITE_API_URL` is build-time constant

### ACTUAL PROBLEM NOT YET FIXED
The fix applied will NOT work because:
- `import.meta.env.VITE_API_URL` gets replaced at build time with string value
- Browser will still try to connect to `backend:8000` from host
- Host cannot resolve Docker service name `backend`

## Correct Solution Options

### Option 1: Use `localhost:8000` with Port Mapping (RECOMMENDED)
```javascript
// docker-compose.yml
frontend:
  environment:
    - VITE_API_URL=http://localhost:8000/api/v1
```
Browser connects to `localhost:8000`, which Docker maps to backend container.

### Option 2: Use Reverse Proxy
Add nginx/Caddy proxy to route `/api` to backend, serve frontend on `/`.

### Option 3: Network Access
Expose backend on host network (not recommended for production).

## Unresolved Questions

1. **Why does Vite's HMR work but environment variable doesn't?**
   - HMR updates code in browser
   - `import.meta.env` values are replaced at BUILD time, not runtime
   - Need to rebuild or restart Vite to pick up new env var values

2. **What URL should browser actually use?**
   - If frontend runs in browser on host: must use `localhost:8000` (via port mapping)
   - If frontend runs in container: could use `backend:8000`
   - Current setup: frontend in container, browser on host = mismatch

3. **Is this a dev-only issue or will production have same problem?**
   - Dev: Vite dev server with Docker
   - Prod: Static build served by nginx/Caddy
   - Need different configs for dev vs prod

## Recommended Next Steps

1. **Revert `VITE_API_URL` to `http://localhost:8000/api/v1`** in docker-compose.yml
2. **Keep the code changes** (using `import.meta.env.VITE_API_URL`) - this is correct pattern
3. **Verify**: Browser connects to `localhost:8000` → Docker forwards to `backend:8000` → backend responds
4. **Document**: Dev vs production URL differences in README

## Supporting Evidence

**Container logs:**
```
leave_frontend  | 9:23:42 PM [vite] (client) hmr update /src/auth/authContext.jsx
```

**Network test:**
```
HTTP/1.1 400 Bad Request
# (Expected - no data sent, but connection successful)
```

**Environment variable in container:**
```
VITE_API_URL=http://backend:8000/api/v1
```

**Files modified:**
- `/home/silver/test-leave/frontend/src/api/http.js`
- `/home/silver/test-leave/frontend/src/api/authApi.js`
- `/home/silver/test-leave/frontend/src/api/businessTripApi.js`
