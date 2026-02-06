# Code Review Summary: Notification Integration

## Scope
- **Files reviewed**: 7 files
  - Frontend: `notificationApi.js`, `use-notifications.js`, `header.jsx`
  - Backend: `notification-service.py`, `list_create.py`, `cancel.py`, `balance.py`
- **Review focus**: Notification integration implementation
- **Date**: 2026-02-04

---

## Overall Assessment
Notification integration is **functional but has critical bugs** that need immediate attention.

**CRITICAL**: Duplicate notification bug in `cancel.py` (line 51-52) - calls `create_leave_cancelled_notification()` twice for approved requests.

Frontend polling implementation is solid. Backend notification service is well-structured but missing transaction safety in bulk operations.

---

## Critical Issues

### 1. Duplicate Notification Bug (cancel.py:48-52)
**Severity**: CRITICAL - breaks user experience

```python
# Line 48: Already creates notification
create_leave_cancelled_notification(leave_request)

# Lines 51-52: WRONG - duplicates notification for approved requests
if previous_status == 'APPROVED' and leave_request.approved_by:
    create_leave_cancelled_notification(leave_request)  # DUPLICATE!
```

**Issue**: Creates duplicate notifications. Line 48 already handles all cases (approved/pending). The function itself contains logic to notify the correct party based on status.

**Fix**: Remove lines 51-52 entirely. The service function already handles the conditional logic.

### 2. Missing Transaction Safety (list_create.py:170-176)
**Severity**: HIGH - data inconsistency risk

```python
for manager_id in manager_ids:
    try:
        manager = User.objects.get(id=manager_id)
        create_leave_pending_notification(manager, leave_request)
    except User.DoesNotExist:
        pass  # Silent failure - notification creation partial
```

**Issue**: No transaction wrapper. If some notifications succeed before a failure, partial notifications created without rollback.

**Fix**: Wrap in `transaction.atomic()` or use `bulk_create()`.

### 3. Link Format Inconsistency (notification-service.py)
**Severity**: MEDIUM - broken navigation

Backend uses frontend routes directly as strings:
```python
link = "/pending-requests"  # Line 48
link = f"/leave-requests/{leave_request.id}"  # Line 69
```

Frontend `header.jsx` (line 87) only marks as read on click - **does NOT navigate**:
```javascript
onClick={() => !item.is_read && markAsRead(item.id)}
```

**Issue**: Links stored but never used for navigation. Users must manually find the related request.

**Fix**: Either use links for navigation or remove them entirely.

---

## High Priority Issues

### 4. No Error Handling for Notification Failures
All notification creation calls in views lack error handling:
- `list_create.py:174`
- `cancel.py:48`
- `balance.py:76`

If notification creation fails, the main operation still succeeds but user is never notified.

**Recommendation**: Log failures but don't block main operations:
```python
try:
    create_leave_pending_notification(manager, leave_request)
except Exception as e:
    logger.error(f"Failed to create notification: {e}")
```

### 5. Inefficient Polling (use-notifications.js:74)
```javascript
const POLLING_INTERVAL = 30000; // 30 seconds
```

Fetches both full list + unread count every 30s:
- Line 70: `fetchNotifications()` - full list
- Line 74: `fetchUnreadCount()` - every 30s

**Issue**: Full list fetched on mount but never refreshed. Only count polls.

**Recommendation**: Either poll both or implement WebSocket/SSE for real-time updates.

### 6. Missing Pagination on Frontend (notificationApi.js:6)
```javascript
export const getNotifications = async (params = {}) => {
  const res = await http.get(API_URL, { params });
  return res.data;
};
```

Hardcoded to `page: 1, page_size: 10` in hook (line 22). Users only see first 10 notifications ever.

---

## Medium Priority Issues

### 7. Unused Loading/Error States (header.jsx:132-133)
Hook returns `loading` and `error` but header component doesn't use them. No visual feedback for failed fetches.

### 8. Silent Failures in Backend (cancel.py:175)
```python
except User.DoesNotExist:
    pass  # Silent failure
```

At least log these failures for debugging.

### 9. Float Conversion in Balance Adjustment (balance.py:72)
```python
adjustment = float(allocated_hours - old_allocated)
```

Converts Decimal to float. Use Decimal throughout for financial calculations to avoid precision errors.

---

## Low Priority Issues

### 10. Magic Numbers
- `POLLING_INTERVAL = 30000` - should be configurable
- `page_size: 10` - hardcoded limit

### 11. No Notification Cleanup
Old notifications never deleted/archived. Table grows indefinitely.

### 12. Missing Type Safety
Frontend has no TypeScript. JSDoc comments would help:
```javascript
/**
 * @typedef {Object} Notification
 * @property {string} id
 * @property {string} title
 * @property {string} message
 * @property {boolean} is_read
 * @property {string} created_at
 */
```

---

## Positive Observations
✓ Clean separation of concerns - notification service well abstracted
✓ Proper indexing on Notification model (user/is_read, created_at)
✓ Good use of React hooks with useCallback for performance
✓ Optimistic UI updates (mark as read updates local state immediately)
✓ Proper permission checks on all endpoints
✓ Empty state handling in UI

---

## Recommended Actions

### Immediate (Before Deploy)
1. **Fix duplicate notification bug** - remove lines 51-52 in `cancel.py`
2. **Add transaction wrapper** for bulk notification creation in `list_create.py`

### High Priority
3. Add error logging for all notification failures
4. Implement navigation using notification links OR remove them
5. Fix pagination - fetch more than first 10 notifications

### Medium Priority
6. Use Decimal throughout balance calculations
7. Add visual feedback for failed notification fetches
8. Log silent failures instead of ignoring them

### Low Priority
9. Consider WebSocket/SSE for real-time notifications instead of polling
10. Implement notification cleanup/archival policy
11. Make polling interval configurable
12. Add JSDoc type comments

---

## Security Review
✓ No SQL injection risks (using ORM)
✓ Proper authorization checks (IsAuthenticated, role-based)
✓ No XSS in notification messages (user-controlled data escaped by React)
✓ No sensitive data in notifications
⚠️ Notification links not validated (could be manipulated)

---

## Unresolved Questions
1. Why store links if not used for navigation?
2. Should notifications be transactional with main operations?
3. Any requirement for real-time notifications vs polling?
4. Notification retention policy?

---

## Metrics
- **Type Coverage**: 0% (JavaScript, no TypeScript)
- **Test Coverage**: Not measured
- **Critical Bugs**: 1 (duplicate notification)
- **High Priority Issues**: 5
- **Medium Priority Issues**: 3
- **Low Priority Issues**: 3
