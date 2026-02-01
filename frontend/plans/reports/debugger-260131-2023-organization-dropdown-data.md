# Debug Report: Organization Dropdown Data Issue

**Date:** 2026-01-31
**Reporter:** Debugger Agent
**Issue:** Registration page dropdowns (Company, Location, Department) not receiving data from backend

---

## Executive Summary

**Root Cause Identified:** Three critical issues blocking organization dropdown data:

1. **Permission Issue (PRIMARY)**: All organization API endpoints require authentication (`IsAuthenticated`), but registration page is public/unauthenticated
2. **Response Format Mismatch**: Backend returns `{results: [...]}` but frontend expects flat array `[...]`
3. **Query Parameter Mismatch**: Backend expects `entity` param, frontend sends `entity_id` param

**Business Impact:** Users cannot complete registration - blocking all new user signups

---

## Technical Analysis

### Issue 1: Permission Barrier (CRITICAL)

**Location:** `/organizations/views.py` lines 13, 27, 51

**Problem:**
```python
# Entity view
permission_classes = [IsAuthenticated]  # Line 13

# Location view
permission_classes = [IsAuthenticated]  # Line 27

# Department view
permission_classes = [IsAuthenticated]  # Line 51
```

**Impact:** All requests from unauthenticated users (registration page) get `401 Unauthorized`

**Evidence:** Registration page is public (`/register`), users have no auth token when selecting organization

---

### Issue 2: Response Format Mismatch

**Backend Response:**
```python
# organizations/views.py line 22
return Response({'results': data})
```

**Frontend Expectation:**
```typescript
// frontend/src/api/organizations.ts lines 35-36
const response = await api.get<Entity[]>('/organizations/entities/');
return response.data;  // Expects Entity[] directly
```

**Impact:** Frontend receives `{results: [...]}` but tries to iterate over it as array, causing type errors

---

### Issue 3: Query Parameter Mismatch

**Backend Reads:**
```python
# organizations/views.py line 33
entity_id = request.query_params.get('entity')  # Looking for 'entity'
```

**Frontend Sends:**
```typescript
// frontend/src/api/organizations.ts line 43
const params = entityId ? { entity_id: entityId } : {};  // Sends 'entity_id'
```

**Impact:** Entity filter doesn't work - backend returns all locations/departments instead of filtered results

---

## Affected Files

### Backend
- `/organizations/views.py` (lines 13, 22, 27, 33, 46, 51, 57, 67)

### Frontend
- `/frontend/src/api/organizations.ts` (lines 35-36, 44, 53)
- `/frontend/src/pages/auth/RegisterPage.tsx` (calls affected API)

---

## Recommended Fix

### Priority 1: Fix Permissions (CRITICAL - blocks registration)

**File:** `/organizations/views.py`

Change all three views from `IsAuthenticated` to `AllowAny`:

```python
class EntityListView(generics.ListAPIView):
    permission_classes = [AllowAny]  # Was: IsAuthenticated
    # ...

class LocationListView(APIView):
    permission_classes = [AllowAny]  # Was: IsAuthenticated
    # ...

class DepartmentListView(APIView):
    permission_classes = [AllowAny]  # Was: IsAuthenticated
    # ...
```

**Justification:** Organization metadata (entities, locations, departments) is non-sensitive reference data needed for public registration

---

### Priority 2: Fix Response Format

**File:** `/organizations/views.py`

Change all three views to return flat arrays:

```python
# EntityListView line 22
return Response(data)  # Was: Response({'results': data})

# LocationListView line 46
return Response(data)  # Was: Response({'results': data})

# DepartmentListView line 67
return Response(data)  # Was: Response({'results': data})
```

---

### Priority 3: Fix Query Parameter

**File:** `/organizations/views.py`

Update parameter name to match frontend:

```python
# LocationListView line 33
entity_id = request.query_params.get('entity_id')  # Was: 'entity'

# DepartmentListView line 57
entity_id = request.query_params.get('entity_id')  # Was: 'entity'
```

---

## Security Considerations

**Q:** Is exposing organization data publicly safe?

**A:** YES - with conditions:
- Only active entities/locations/departments exposed (already filtered `is_active=True`)
- No sensitive data in response (names, codes, cities only)
- Read-only access (no create/update/delete)
- Standard practice for registration forms

**Recommendation:** Keep `AllowAny` for these three endpoints. Consider rate limiting if abuse becomes concern.

---

## Testing Validation

**After fix, verify:**
1. Visit `/register` page (unauthenticated)
2. Company dropdown populates with entities
3. Select company → Location dropdown populates
4. Select company → Department dropdown populates
5. Can complete registration successfully

**API Testing:**
```bash
# Test entities endpoint (should work without auth)
curl -X GET http://localhost:8000/api/v1/organizations/entities/

# Test locations with entity filter
curl -X GET "http://localhost:8000/api/v1/organizations/locations/?entity_id=<UUID>"

# Test departments with entity filter
curl -X GET "http://localhost:8000/api/v1/organizations/departments/?entity_id=<UUID>"
```

---

## Timeline

- **Impact Start:** Unknown (likely since registration feature added)
- **Discovery:** 2026-01-31 20:23 ICT
- **Investigation Duration:** ~5 minutes
- **Estimated Fix Time:** 5 minutes (3 simple changes)
- **Testing Time:** 5 minutes

---

## Prevention

**Root Cause of Root Cause:** Public endpoints defaulted to authenticated

**Future Prevention:**
1. Add test coverage for public registration flow
2. Document which endpoints must be public (`AllowAny`)
3. Use integration tests that simulate unauthenticated user journey
4. Add API contract validation (frontend types match backend serializers)

---

## Unresolved Questions

None - root cause definitively identified with clear fix path.
