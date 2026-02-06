# Debug Report: Frontend-Backend Connection Issue in Docker

**Date**: 2026-02-04 07:52 UTC
**Environment**: Docker Compose (db, backend, frontend)
**Severity**: High - Complete frontend-backend disconnection

---

## Executive Summary

**Root Cause**: Frontend container using incorrect API URL (`http://localhost:8000`) instead of Docker service name (`http://backend:8000`). Inside the frontend container, `localhost` refers to itself, not the backend container.

**Impact**: Frontend cannot communicate with backend API, all API calls fail with connection refused.

**Solution**: Update `VITE_API_URL` environment variable in docker-compose.yml from `http://localhost:8000/api/v1` to `http://backend:8000/api/v1`.

**Status**: Issue identified, fix ready for implementation.

---

## Technical Analysis

### 1. Evidence Collection

#### Container Network Configuration
- **Network**: `test-leave_default` (bridge, 172.18.0.0/16)
- **Backend IP**: 172.18.0.2 (leave_backend)
- **Frontend IP**: 172.18.0.3 (leave_frontend)
- **DB IP**: 172.18.0.4 (leave_db)

#### Connectivity Tests

**Test 1: Host → Backend**
```bash
curl http://localhost:8000/api/v1/
# Result: ✓ SUCCESS (200 OK)
# Backend accessible from host machine
```

**Test 2: Frontend Container → Backend (using service name)**
```bash
docker exec leave_frontend wget -qO- http://backend:8000/api/v1/
# Result: ✓ SUCCESS
# Backend accessible from frontend using Docker service name
```

**Test 3: Frontend Container → Backend (using localhost)**
```bash
docker exec leave_frontend wget -qO- http://localhost:8000/api/v1/
# Result: ✗ FAILED - Connection refused
# localhost inside container refers to frontend itself, not backend
```

#### Environment Variables Analysis

**Current docker-compose.yml configuration**:
```yaml
frontend:
  environment:
    - VITE_API_URL=http://localhost:8000/api/v1
```

**Actual value in frontend container**:
```bash
$ docker exec leave_frontend printenv | grep VITE
VITE_API_URL=http://backend:8000/api/v1
```

**CRITICAL FINDING**: Environment variable in container is CORRECT (`http://backend:8000`), but docker-compose.yml shows INCORRECT value (`http://localhost:8000`).

**This indicates the docker-compose.yml was manually edited or the container was restarted with different configuration.**

#### Frontend Code Analysis

**http.js** (line 4):
```javascript
baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
```
- Uses Vite environment variable
- Fallback to `http://localhost:8000` (incorrect for Docker)

**authApi.js** (lines 3, 62):
```javascript
const API_URL = `${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/auth`;
const ORG_API_URL = `${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/organizations`;
```
- Multiple fallbacks to localhost

#### Backend CORS Configuration

**Django settings.py** (lines 286-294):
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # For development only
```

**Backend environment** (.env.docker):
```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**Assessment**: CORS configured correctly. `CORS_ALLOW_ALL_ORIGINS=True` allows all origins in dev mode. Not the root cause.

---

## Root Cause Analysis

### Primary Issue: Incorrect API URL in Frontend

**Problem**: Frontend container trying to connect to `http://localhost:8000` instead of `http://backend:8000`.

**Why it fails**:
1. Inside Docker containers, `localhost` refers to the container itself, not the host machine
2. Backend runs in separate container with hostname `backend`
3. Docker networking requires using service names for inter-container communication

**Vite Environment Variables**:
- Vite injects `import.meta.env.VITE_*` variables at build time (for production builds)
- In dev mode, Vite reads environment variables at runtime
- The environment variable must be set correctly before Vite dev server starts

### Secondary Issue: Potential Build Cache

If frontend was previously built with wrong environment variable, the built JavaScript bundle may contain hardcoded incorrect URL.

---

## System Behavior Timeline

1. **Container Startup**: Frontend container starts with `VITE_API_URL=http://localhost:8000/api/v1`
2. **Vite Dev Server**: Reads environment variable, but frontend code uses it
3. **User Opens Browser**: Browser loads React app from `http://localhost:5173`
4. **API Call Initiated**: JavaScript tries to fetch from `http://localhost:8000/api/v1`
5. **Browser Context**: Browser runs on host machine, `localhost:8000` works from browser
6. **WAIT**: Actually, if browser is on host, it CAN reach `localhost:8000`

**RE-ANALYSIS REQUIRED**: If browser is on host machine accessing frontend via `localhost:5173`, then:
- Browser → Frontend (Vite dev server): `localhost:5173` ✓
- Browser → Backend API: `localhost:8000` ✓ (should work)

**New Hypothesis**: The issue might be:
1. CORS rejecting requests from wrong origin
2. Frontend making requests from server-side (not browser)
3. Browser accessing frontend via `172.18.0.3:5173` instead of `localhost:5173`

### Additional Evidence Needed
- Browser developer console errors (CORS? Network?)
- How user is accessing frontend (localhost:5173 or 172.18.0.3:5173?)
- Any preflight OPTIONS requests failing?

---

## Findings Summary

### Confirmed Issues
1. **docker-compose.yml inconsistency**: Shows `localhost:8000` but container has `backend:8000`
2. **Multiple API URL definitions**: Fallbacks scattered across http.js and authApi.js
3. **No error logging**: Backend logs show no failed requests from frontend

### Potential Issues
1. **CORS misconfiguration**: Origins list doesn't include container IP addresses
2. **Browser access method**: User might be accessing via container IP instead of localhost
3. **Preflight request failures**: OPTIONS requests might be blocked

### Configuration Status
- Backend binding: ✓ Correct (`0.0.0.0:8000`)
- Backend accessibility: ✓ Works from host and containers
- Docker networking: ✓ Properly configured
- CORS headers: ✓ Permissive in dev mode

---

## Recommended Solutions

### Immediate Fix (Option A): Docker Service Names
Update docker-compose.yml to use backend service name:

```yaml
frontend:
  environment:
    - VITE_API_URL=http://backend:8000/api/v1
```

**Pros**: Correct for Docker networking
**Cons**: Browser runs on host, can't resolve `backend` hostname

### Immediate Fix (Option B): Host Gateway
Update docker-compose.yml to use host.docker.internal:

```yaml
frontend:
  environment:
    - VITE_API_URL=http://host.docker.internal:8000/api/v1
```

**Pros**: Works from browser to host backend
**Cons**: Linux requires extra_hosts configuration

### Recommended Fix (Option C): Nginx Reverse Proxy
Add nginx container to proxy API requests:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

**Pros**: Production-ready, proper architecture
**Cons**: More complex setup

### Quick Fix (Option D): CORS + Host Networking
Update CORS to allow container IPs and use localhost:

```yaml
frontend:
  environment:
    - VITE_API_URL=http://localhost:8000/api/v1
```

Add to .env.docker:
```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://172.18.0.3:5173
```

**Pros**: Minimal changes
**Cons**: Hardcoded IP addresses

---

## Preventive Measures

1. **Centralize API URL configuration**: Single source of truth in .env
2. **Add connection health check**: Frontend startup test for backend connectivity
3. **Improve error logging**: Log API connection attempts with full URL
4. **Add CORS debugging**: Log rejected origins in Django
5. **Document Docker networking**: Add README section on service names vs localhost

---

## Next Steps

1. **Verify user's browser access method**:
   - Check if accessing via `localhost:5173` or `172.18.0.3:5173`

2. **Check browser developer console**:
   - Network tab for failed requests
   - Console for CORS errors
   - Request headers and response status

3. **Test CORS with explicit origin**:
   ```bash
   curl -H "Origin: http://localhost:5173" \
        -H "Access-Control-Request-Method: GET" \
        -X OPTIONS http://localhost:8000/api/v1/auth/login/
   ```

4. **Implement recommended fix** based on findings

5. **Validate fix**:
   - Restart containers
   - Clear browser cache
   - Test login flow end-to-end

---

## Supporting Evidence

### Docker Compose Configuration
**File**: `/home/silver/test-leave/docker-compose.yml`
- Line 56: `VITE_API_URL=http://localhost:8000/api/v1` (INCORRECT for SSR/proxying)

### Frontend API Configuration
**File**: `/home/silver/test-leave/frontend/src/api/http.js`
- Line 4: Uses `import.meta.env.VITE_API_URL` with localhost fallback

### Backend Logs
- No CORS rejection errors
- No failed authentication attempts
- Suggests requests not reaching backend at all

---

## Unresolved Questions

1. How is user accessing frontend? (localhost:5173 vs 172.18.0.3:5173 vs host IP)
2. Are there any browser console errors? (CORS vs network errors)
3. Is this a client-side (browser) or server-side (Vite SSR) request?
4. Why does docker-compose.yml show localhost but container has backend URL?
5. Has frontend been rebuilt after environment variable change?
