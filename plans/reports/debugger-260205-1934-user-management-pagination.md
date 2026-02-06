# User Management Settings Page - Pagination Issues Report

**Date**: 2026-02-05 19:34
**Issue**: Only 50 out of 60 users displayed, pagination dropdown not working
**Status**: Root cause identified

---

## Executive Summary

**Root Causes Identified:**

1. **Backend PAGE_SIZE Limit**: Django REST Framework configured with `PAGE_SIZE: 50`, causing API to return only 50 users
2. **Frontend Not Handling Pagination**: Frontend doesn't send `page_size` parameter to backend or handle paginated responses
3. **Client-Side vs Server-Side Pagination Mismatch**: Table configured for client-side pagination but data is server-paginated

**Impact**: HR/Admin users cannot see all 60 users in the system, missing 10 users entirely.

---

## Technical Analysis

### 1. Backend Configuration

**File**: `/home/silver/test-leave/backend/settings.py` (lines 243-253)

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,  # <-- LIMITING FACTOR
}
```

**Issue**: The `PAGE_SIZE: 50` setting causes the `UserViewSet` to return paginated responses with:
- `count`: 60 (total users)
- `results`: Array of 50 users
- `next`: URL for page 2
- `previous`: null

### 2. Backend ViewSet

**File**: `/home/silver/test-leave/users/viewsets.py` (lines 13-104)

```python
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (HR/Admin only)

    - list: GET /api/v1/auth/users/ - List all users
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """HR/Admin can see all users"""
        user = self.request.user
        if user.role in [User.Role.HR, User.Role.ADMIN]:
            return User.objects.all().select_related('entity', 'location', 'department', 'approver')
        # ... other roles
```

**Issue**: The ViewSet doesn't override pagination settings, so it uses the global `PAGE_SIZE: 50`.

**Queryset returns**: All 60 users from database, but pagination truncates to 50.

### 3. Frontend Implementation

**File**: `/home/silver/test-leave/frontend/src/pages/Settings.jsx`

#### Problem 1: API Call Without Pagination (lines 52-56)

```javascript
const fetchUsers = async () => {
  setLoading(true);
  try {
    const data = await getAllUsers();  // No params passed!
    setUsers(data.results || data);     // Handle both paginated & direct
  } catch (error) {
    message.error("Failed to load users: " + error.message);
  } finally {
    setLoading(false);
  }
};
```

**Issue**: `getAllUsers()` is called without any parameters, so backend uses default `PAGE_SIZE: 50`.

#### Problem 2: API Implementation (lines 7-10 of `/home/silver/test-leave/frontend/src/api/userApi.js`)

```javascript
export const getAllUsers = async (params = {}) => {
  const response = await http.get("/auth/users/", { params });
  return response.data;
};
```

**Issue**: Function accepts `params` but frontend never passes `{ page_size: 100 }` or similar.

#### Problem 3: Table Pagination Config (lines 308-312)

```javascript
<Table
  columns={columns}
  dataSource={users}  // Only contains 50 users!
  rowKey="id"
  loading={loading}
  scroll={{ x: 1200 }}
  pagination={{
    pageSize: 20,           // Client-side pagination of 50 items
    showSizeChanger: true,  // Shows dropdown but only affects client-side
    showTotal: (total) => `Total ${total} users`,  // Shows 50, not 60!
  }}
/>
```

**Issue**: This is CLIENT-SIDE pagination on 50 items. The dropdown works for changing page size (10/20/50/100), but:
- It only paginates the 50 items already loaded
- "Total 50 users" displays instead of "Total 60 users"
- Missing 10 users are nowhere in the data

---

## Database Verification

**Query executed**:
```sql
SELECT COUNT(*) FROM users;
-- Result: 60

SELECT role, COUNT(*) FROM users GROUP BY role;
-- ADMIN    |     2
-- EMPLOYEE |    51
-- HR       |     2
-- MANAGER  |     5
```

**Confirmed**: Database has 60 users total.

---

## Why Pagination Dropdown Doesn't Work

The Ant Design Table `showSizeChanger` dropdown (10/20/50/100 options) DOES work, but:

1. **It only affects client-side pagination** of the 50 items already loaded
2. **Backend still only sends 50 users** regardless of dropdown selection
3. **User perception**: "I select 100/page but still only see 50 users total"

---

## API Response Structure (Expected vs Actual)

### Actual Response (Current Behavior)

```json
{
  "count": 60,
  "next": "http://localhost:8000/api/v1/auth/users/?page=2",
  "previous": null,
  "results": [
    // 50 user objects
  ]
}
```

### What Frontend Needs

Either:
1. **Non-paginated response** for user list (all 60 users)
2. **Proper pagination handling** (fetch all pages, handle next/previous)

---

## Solutions

### Option 1: Disable Pagination for User List (RECOMMENDED)

**Backend**: Modify `/home/silver/test-leave/users/viewsets.py`

```python
from rest_framework.pagination import LimitOffsetPagination

class UserViewSet(viewsets.ModelViewSet):
    pagination_class = None  # Disable pagination
    # OR
    pagination_class = LimitOffsetPagination  # Use unlimited pagination
```

**Pros**:
- Simple fix
- All 60 users loaded
- Works with current frontend code

**Cons**:
- Not scalable for 1000+ users
- Slower initial load

### Option 2: Frontend Fetches All Pages

**Frontend**: Modify `/home/silver/test-leave/frontend/src/pages/Settings.jsx`

```javascript
const fetchUsers = async () => {
  setLoading(true);
  try {
    // Request larger page size
    const data = await getAllUsers({ page_size: 100 });

    // Or fetch all pages recursively
    let allUsers = [];
    let nextPage = '/auth/users/';

    while (nextPage) {
      const response = await http.get(nextPage);
      allUsers = [...allUsers, ...response.data.results];
      nextPage = response.data.next;
    }

    setUsers(allUsers);
  } catch (error) {
    message.error("Failed to load users: " + error.message);
  } finally {
    setLoading(false);
  }
};
```

**Pros**:
- Scalable
- Follows REST best practices

**Cons**:
- More complex
- Multiple API calls

### Option 3: Frontend Implements Server-Side Pagination

**Frontend**: Modify Settings.jsx to handle proper pagination

```javascript
const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

const fetchUsers = async (page = 1, pageSize = 20) => {
  setLoading(true);
  try {
    const response = await http.get("/auth/users/", {
      params: { page, page_size: pageSize }
    });

    setUsers(response.data.results);
    setPagination({
      current: page,
      pageSize: pageSize,
      total: response.data.count
    });
  } catch (error) {
    message.error("Failed to load users");
  } finally {
    setLoading(false);
  }
};

<Table
  dataSource={users}
  pagination={{
    ...pagination,
    onChange: (page, pageSize) => fetchUsers(page, pageSize),
    showSizeChanger: true,
    showTotal: (total) => `Total ${total} users`
  }}
/>
```

**Pros**:
- Best for scalability
- Follows REST patterns
- Efficient for large datasets

**Cons**:
- Most complex to implement
- Requires significant frontend changes

---

## Recommended Action Plan

### Immediate Fix (Option 1)

1. **Backend**: Disable pagination for `UserViewSet`
2. **Test**: Verify all 60 users load
3. **Deploy**: Quick fix to restore functionality

### Long-term Solution (Option 3)

1. **Frontend**: Implement server-side pagination
2. **Backend**: Keep pagination but ensure `page_size` parameter works
3. **Add**: Maximum page size limit (e.g., 100)
4. **Test**: Verify with 60+ users

---

## Unresolved Questions

1. **User Growth**: How many users is the system expected to handle? (For deciding between Option 1 vs Option 3)
2. **Performance**: Are there any performance concerns with loading 60+ users at once?
3. **Other Views**: Do other pages (like leave requests) have similar pagination issues?
4. **Mobile Support**: Should the user list be optimized for mobile devices (smaller page size)?

---

## Files Requiring Changes

### For Option 1 (Quick Fix):
- `/home/silver/test-leave/users/viewsets.py` - Add `pagination_class = None`

### For Option 2 (Fetch All Pages):
- `/home/silver/test-leave/frontend/src/pages/Settings.jsx` - Modify `fetchUsers()` function

### For Option 3 (Proper Pagination):
- `/home/silver/test-leave/frontend/src/pages/Settings.jsx` - Full pagination implementation
- `/home/silver/test-leave/frontend/src/api/userApi.js` - Add pagination helper functions

---

## Related Code

**Backend Settings**: `/home/silver/test-leave/backend/settings.py` (lines 243-253)
**Frontend API**: `/home/silver/test-leave/frontend/src/api/userApi.js` (lines 7-10)
**Frontend Component**: `/home/silver/test-leave/frontend/src/pages/Settings.jsx` (lines 52-56, 302-313)
**Backend ViewSet**: `/home/silver/test-leave/users/viewsets.py` (lines 13-104)
