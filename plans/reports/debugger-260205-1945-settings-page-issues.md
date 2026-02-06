# Debug Report: User Management Settings Page Issues

**Date:** 2026-02-05 19:45
**Reported By:** user
**Status:** ROOT CAUSES IDENTIFIED

---

## Executive Summary

Two issues identified in the User Management Settings page:
1. **Pagination dropdown not working** - Missing state management for page size changes
2. **"Employees Without Approver" statistic incorrect** - Filter correctly excludes non-EMPLOYEE roles

Both issues are straightforward to fix with minimal code changes.

---

## Issue 1: Pagination Dropdown Not Working

### Symptoms
- User added `pageSizeOptions: ['10', '20', '50', '100']`
- Dropdown appears but changing page size has no effect
- Table remains at 20 items per page

### Root Cause
**Location:** `/home/silver/test-leave/frontend/src/pages/Settings.jsx:308-313`

The Table pagination config is **static** (not controlled by React state):

```jsx
pagination={{
  pageSize: 20,
  pageSizeOptions: ['10', '20', '50', '100'],
  showSizeChanger: true,
  showTotal: (total) => `Total ${total} users`,
}}
```

Ant Design Table's pagination becomes **controlled** when `onChange` is provided or when `pagination` object changes. Without state management:
- Initial `pageSize: 20` is hardcoded
- No handler to capture user's page size selection
- No state variable to store the current page size
- Table cannot update when user changes dropdown value

### Why It Happens
Ant Design Table pagination has two modes:
1. **Uncontrolled** (default): Ant Design manages pagination internally
2. **Controlled**: Component manages pagination state via props

When providing a static object with `pageSize`, Ant Design uses it as initial value but has no way to know when user changes it. Need either:
- State-controlled pagination with `onChange` handler, OR
- Remove static `pageSize` to let Ant Design manage it fully

### Evidence
- Lines 308-313: Static pagination object, no state management
- No `pagination` state variable exists in component
- No `onChange` handler provided to capture page size changes

---

## Issue 2: "Employees Without Approver" Statistic Incorrect

### Symptoms
- All 63 users have `approver_id` NULL in database
- Statistic shows "52" instead of "63"
- Expected: 63 (all users without approver)
- Actual: 52 (filtered count)

### Root Cause
**Location:** `/home/silver/test-leave/frontend/src/pages/Settings.jsx:248-250`

The calculation **correctly filters by role = EMPLOYEE only**:

```jsx
withoutApprover: users.filter(
  (u) => !u.approver && u.role === "EMPLOYEE"
).length,
```

### Database Verification

```sql
-- All users without approver: 63
SELECT COUNT(*) - COUNT(approver_id) FROM users;  -- Result: 63

-- Breakdown by role:
SELECT role, COUNT(*) - COUNT(approver_id) as without_approver
FROM users GROUP BY role;

-- Result:
-- EMPLOYEE | 52
-- MANAGER  | 6
-- HR       | 3
-- ADMIN    | 2
-- Total:   | 63
```

### Why It Happens

**The statistic is INTENTIONALLY filtering by EMPLOYEE role only.**

Line 249 explicitly checks `u.role === "EMPLOYEE"`, which means:
- 52 EMPLOYEEs without approver ✓ (counted)
- 6 MANAGERs without approver ✗ (excluded)
- 3 HR without approver ✗ (excluded)
- 2 ADMINs without approver ✗ (excluded)

This is **design intent**, not a bug:
- HR/Admin/Manager roles typically don't need approvers
- They are either approvers themselves or have different approval workflows
- Only EMPLOYEEs require approvers for leave requests

### User Confusion Point

User expected "all users without approver" but the UI shows "Employees Without Approver" (singular Employee, not users). The statistic label is **correct** - it counts EMPLOYEES without approver, not all users.

### Evidence
- Database query confirms 63 total users have NULL approver_id
- Frontend code at line 249 filters `u.role === "EMPLOYEE"`
- Only 52 EMPLOYEEs exist (confirmed by database: 52 EMPLOYEE, 6 MANAGER, 3 HR, 2 ADMIN)
- 52 + 6 + 3 + 2 = 63 ✓

---

## Recommended Fixes

### Fix 1: Enable Pagination State Management

**Option A: Uncontrolled (Simplest - Recommended)**
Remove the static `pageSize` to let Ant Design manage pagination:

```jsx
pagination={{
  pageSizeOptions: ['10', '20', '50', '100'],
  showSizeChanger: true,
  showTotal: (total) => `Total ${total} users`,
}}
```

**Option B: Controlled (If custom behavior needed)**
Add state management:

```jsx
const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });

// In Table component:
pagination={{
  current: pagination.current,
  pageSize: pagination.pageSize,
  pageSizeOptions: ['10', '20', '50', '100'],
  showSizeChanger: true,
  showTotal: (total) => `Total ${total} users`,
  onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
}}
```

### Fix 2: Clarify Statistic or Change Behavior

**Option A: Update label for clarity (Recommended)**
No code change needed - label is already accurate:
- Current: "Employees Without Approver" ✓
- Keep as-is, this is correct behavior

**Option B: If user really wants ALL users**
Remove the role filter (not recommended, breaks business logic):

```jsx
withoutApprover: users.filter((u) => !u.approver).length,
```

---

## Unresolved Questions

1. **Pagination:** Does user want specific default page size, or is Ant Design's default acceptable?
2. **Statistic:** Is the current behavior (counting only EMPLOYEEs) actually wrong, or was it just misunderstood? The label "Employees Without Approver" suggests the current behavior is intentional.

---

## Impact Assessment

| Issue | Severity | User Impact | Fix Complexity |
|-------|----------|-------------|----------------|
| Pagination | Medium | UX annoyance, cannot change page size | Low (1 line change) |
| Statistic | Low | Confusion, but behavior may be correct | None (may be working as designed) |

---

## Files to Modify

1. `/home/silver/test-leave/frontend/src/pages/Settings.jsx` - Line 309 (remove static pageSize)
