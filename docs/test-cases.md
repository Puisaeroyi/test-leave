# Leave Management System - Test Cases

> **Version:** 1.0 | **Updated:** 2026-01-19
> **Coverage:** Unit, Integration, E2E, Edge Cases
> **Balance Model:** Unified 96h pool (hours-based)

---

## Table of Contents

1. [Authentication & OAuth](#1-authentication--oauth)
2. [Onboarding Flow](#2-onboarding-flow)
3. [Role-Based Access Control](#3-role-based-access-control)
4. [Leave Balance](#4-leave-balance)
5. [Leave Request - Creation](#5-leave-request---creation)
6. [Leave Request - Edit/Cancel](#6-leave-request---editcancel)
7. [Approval Workflow](#7-approval-workflow)
8. [Team Calendar](#8-team-calendar)
9. [Notifications](#9-notifications)
10. [HR Admin Functions](#10-hr-admin-functions)
11. [Public Holidays](#11-public-holidays)
12. [Year Boundary & Time](#12-year-boundary--time)
13. [API Security](#13-api-security)
14. [Performance](#14-performance)
15. [Database Integrity](#15-database-integrity)

---

## 1. Authentication & OAuth

### 1.1 Google OAuth Login

| ID | Test Case | Precondition | Steps | Expected Result |
|----|-----------|--------------|-------|-----------------|
| AUTH-001 | First-time Google login | User not in DB | Click "Sign in with Google" → Complete OAuth | User created with status=ACTIVE, redirect to onboarding |
| AUTH-002 | Returning user login | User exists, has dept | Click "Sign in with Google" | Redirect to dashboard |
| AUTH-003 | Returning user without dept | User exists, no dept | Login | Redirect to onboarding page |
| AUTH-004 | OAuth token expired | Session expired | Access protected route | Redirect to login page |
| AUTH-005 | OAuth callback error | Google returns error | OAuth fails | Show error message, stay on login |
| AUTH-006 | Invalid OAuth state | CSRF attack attempt | Manipulated state param | Reject, show error |
| AUTH-007 | Logout | User logged in | Click logout | Session destroyed, redirect to login |
| AUTH-008 | Multiple tabs logout | Logged in multiple tabs | Logout in one tab | All tabs redirected on next action |

### 1.2 Session Management

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| AUTH-009 | Session persistence | Session survives browser refresh |
| AUTH-010 | Session timeout | Auto-logout after inactivity period |
| AUTH-011 | Concurrent sessions | Allow multiple device logins |

---

## 2. Onboarding Flow

### 2.1 Entity-Location-Department Selection

| ID | Test Case | Precondition | Steps | Expected Result |
|----|-----------|--------------|-------|-----------------|
| ONB-001 | Load onboarding page | New user, no dept | Access /onboarding | Show form with Entity dropdown enabled, Location/Dept disabled |
| ONB-002 | Select entity | On onboarding | Select entity | Location dropdown enabled, filtered by entity |
| ONB-003 | Select location | Entity selected | Select location | Department dropdown enabled, filtered by entity |
| ONB-004 | Complete onboarding | All fields filled | Submit | User updated with entity/location/dept, redirect to dashboard |
| ONB-005 | Skip onboarding attempt | No dept assigned | Try to access /dashboard | Redirect back to onboarding |
| ONB-006 | Empty entity list | No entities in DB | Load onboarding | Show "Contact admin" message |
| ONB-007 | Validation - missing entity | Location selected, no entity | Submit | Error: "Entity required" |
| ONB-008 | Validation - missing location | Entity selected, no location | Submit | Error: "Location required" |
| ONB-009 | Validation - missing dept | Entity+Location selected | Submit | Error: "Department required" |
| ONB-010 | Pre-filled name | OAuth provided name | Load page | Name field pre-filled from OAuth |

### 2.2 Auto Balance Creation

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| ONB-011 | Balance created on onboarding complete | LeaveBalance record created (96h allocated, 0 used) |
| ONB-012 | Balance year matches current year | Balance.year = current year |

---

## 3. Role-Based Access Control

### 3.1 Permission Matrix

| ID | Test Case | Role | Action | Expected |
|----|-----------|------|--------|----------|
| RBAC-001 | Employee submit leave | EMPLOYEE | POST /api/leaves/requests/ | 201 Created |
| RBAC-002 | Employee view own balance | EMPLOYEE | GET /api/leaves/balance/me/ | 200 OK |
| RBAC-003 | Employee view others balance | EMPLOYEE | GET /api/leaves/balance/other-user/ | 403 Forbidden |
| RBAC-004 | Employee approve request | EMPLOYEE | POST /api/leaves/requests/{id}/approve/ | 403 Forbidden |
| RBAC-005 | Manager approve team request | MANAGER | Approve direct report | 200 OK |
| RBAC-006 | Manager approve non-team | MANAGER | Approve different dept | 403 Forbidden |
| RBAC-007 | HR view all users | HR | GET /api/users/ | 200 OK with all users |
| RBAC-008 | HR adjust balance | HR | PUT /api/users/{id}/balance/ | 200 OK |
| RBAC-009 | Admin configure categories | ADMIN | POST /api/leaves/categories/ | 201 Created |
| RBAC-010 | Admin access Django admin | ADMIN | GET /admin/ | 200 OK |
| RBAC-011 | Non-admin access Django admin | EMPLOYEE | GET /admin/ | 403 Forbidden |

### 3.2 DEPARTMENT_MANAGER Junction

| ID | Test Case | Setup | Expected |
|----|-----------|-------|----------|
| RBAC-012 | Manager sees only assigned dept+location | Manager assigned to Engineering@HCMC | Only sees Engineering@HCMC requests |
| RBAC-013 | Manager with multiple assignments | Manager → Eng@HCMC + Eng@Singapore | Sees both locations |
| RBAC-014 | No manager assigned | Dept has no DepartmentManager | Requests go to HR/Admin |
| RBAC-015 | Inactive manager assignment | DepartmentManager.is_active=false | Manager cannot approve |

---

## 4. Leave Balance

### 4.1 Balance Display

| ID | Test Case | Data | Expected |
|----|-----------|------|----------|
| BAL-001 | Fresh balance | allocated=96, used=0, adjusted=0 | Remaining: 96h |
| BAL-002 | Partial used | allocated=96, used=24, adjusted=0 | Remaining: 72h |
| BAL-003 | With adjustment | allocated=96, used=24, adjusted=+8 | Remaining: 80h |
| BAL-004 | Negative adjustment | allocated=96, used=0, adjusted=-16 | Remaining: 80h |
| BAL-005 | Exhausted balance | allocated=96, used=96 | Remaining: 0h |
| BAL-006 | Over-used (edge) | allocated=96, used=100 | Remaining: -4h (show warning) |

### 4.2 Balance API

| ID | Test Case | Request | Expected |
|----|-----------|---------|----------|
| BAL-007 | Get current year balance | GET /api/leaves/balance/me/ | Returns 2026 balance |
| BAL-008 | Get specific year | GET /api/leaves/balance/me/?year=2025 | Returns 2025 balance |
| BAL-009 | Get non-existent year | GET /api/leaves/balance/me/?year=2030 | 404 or auto-create |
| BAL-010 | Balance pie chart data | GET /api/leaves/balance/me/ | Returns allocated, used, remaining |

---

## 5. Leave Request - Creation

### 5.1 Full Day Requests

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| REQ-001 | Single full day | start=Jan20, end=Jan20, shift_type=FULL_DAY | total_hours=8 |
| REQ-002 | Multi-day (3 days) | start=Jan20, end=Jan22, shift_type=FULL_DAY | total_hours=24 |
| REQ-003 | Week (5 days) | start=Mon, end=Fri | total_hours=40 |
| REQ-004 | Includes weekend | start=Fri, end=Mon (4 calendar days) | total_hours=16 (skip Sat/Sun) |
| REQ-005 | Includes holiday | start=Jan1, end=Jan3, Jan1=holiday | total_hours=16 (skip holiday) |

### 5.2 Custom Hours Requests

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| REQ-006 | Half day morning | start=Jan20, end=Jan20, shift=CUSTOM, 09:00-13:00 | total_hours=4 |
| REQ-007 | Half day afternoon | start=Jan20, end=Jan20, shift=CUSTOM, 13:00-17:00 | total_hours=4 |
| REQ-008 | Custom 5 hours | start=Jan20, end=Jan20, shift=CUSTOM, 09:00-14:00 | total_hours=5 |
| REQ-009 | Custom hours validation | start_time > end_time | Error: "End time must be after start" |

### 5.3 Validation

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| REQ-010 | End before start | end_date < start_date | Error: "End date must be >= start" |
| REQ-011 | Past date | start_date = yesterday | Error: "Cannot request leave in past" |
| REQ-012 | Insufficient balance | Request 100h, balance=72h | Warning (allow or block based on config) |
| REQ-013 | Overlapping request | Existing approved Jan20-22, new Jan21-23 | Error: "Overlapping request exists" |
| REQ-014 | Missing category | No leave_category_id | Allow (category optional for reporting) |
| REQ-015 | Category requires doc | category.requires_document=true, no attachment | Warning or error |

### 5.4 Status Flow

| ID | Test Case | Expected |
|----|-----------|----------|
| REQ-016 | New request status | status=PENDING |
| REQ-017 | Request creates notification | Manager receives notification |
| REQ-018 | Request creates audit log | AuditLog entry with action=CREATE |

---

## 6. Leave Request - Edit/Cancel

### 6.1 Edit Request

| ID | Test Case | Precondition | Action | Expected |
|----|-----------|--------------|--------|----------|
| EDIT-001 | Edit pending request | status=PENDING | Change dates | Success, hours recalculated |
| EDIT-002 | Edit approved request | status=APPROVED | Try edit | Error: "Cannot edit approved request" |
| EDIT-003 | Edit rejected request | status=REJECTED | Try edit | Error: "Cannot edit rejected request" |
| EDIT-004 | Edit cancelled request | status=CANCELLED | Try edit | Error: "Cannot edit cancelled request" |
| EDIT-005 | Edit creates audit log | Edit successful | Check audit | Old/new values logged |

### 6.2 Cancel Request

| ID | Test Case | Precondition | Expected |
|----|-----------|--------------|----------|
| CANCEL-001 | Cancel pending | status=PENDING | status→CANCELLED, no balance change |
| CANCEL-002 | Cancel approved | status=APPROVED | Error or restore balance (design decision) |
| CANCEL-003 | Cancel rejected | status=REJECTED | Error: "Already rejected" |
| CANCEL-004 | Cancel confirmation | Click cancel | Show confirmation dialog |
| CANCEL-005 | Cancel notifies manager | Cancel successful | Manager receives notification |

---

## 7. Approval Workflow

### 7.1 Manager Inbox

| ID | Test Case | Setup | Expected |
|----|-----------|-------|----------|
| APPR-001 | Inbox shows team requests | Manager for Engineering@HCMC | Only Eng@HCMC pending requests |
| APPR-002 | Inbox empty state | No pending requests | "No pending requests" message |
| APPR-003 | Inbox badge count | 5 pending requests | Sidebar shows "(5)" |
| APPR-004 | Inbox sorting | Multiple requests | Oldest first by default |
| APPR-005 | Inbox filtering | Filter by employee name | Filtered results |

### 7.2 Approve Action

| ID | Test Case | Action | Expected |
|----|-----------|--------|----------|
| APPR-006 | Approve request | Click approve | status=APPROVED, balance deducted |
| APPR-007 | Approve with comment | Add optional comment | Comment saved, visible to employee |
| APPR-008 | Balance deduction | Approve 24h request | used_hours += 24 |
| APPR-009 | Approve notifies employee | Approve | Employee receives notification |
| APPR-010 | Approve creates audit log | Approve | AuditLog with action=APPROVE |
| APPR-011 | Approve removed from inbox | Approve | Request no longer in inbox |

### 7.3 Reject Action

| ID | Test Case | Action | Expected |
|----|-----------|--------|----------|
| APPR-012 | Reject without reason | Click reject, no reason | Error: "Reason required" |
| APPR-013 | Reject with reason | Provide reason (10+ chars) | status=REJECTED, reason saved |
| APPR-014 | Reject no balance change | Reject | used_hours unchanged |
| APPR-015 | Reject notifies employee | Reject | Employee sees rejection + reason |
| APPR-016 | Reject short reason | Reason < 10 chars | Error: "Reason too short" |

### 7.4 Request Detail View

| ID | Test Case | Expected Content |
|----|-----------|------------------|
| APPR-017 | Detail shows employee info | Name, department, email |
| APPR-018 | Detail shows leave info | Category, dates, hours, shift type |
| APPR-019 | Detail shows balance | Employee's remaining hours |
| APPR-020 | Detail shows conflicts | "Also off: John (Jan 10-12)" |
| APPR-021 | Detail shows attachment | Link to uploaded document |

---

## 8. Team Calendar

### 8.1 Calendar Display

| ID | Test Case | Data | Expected |
|----|-----------|------|----------|
| CAL-001 | Load month view | January 2026 | Calendar grid with Jan dates |
| CAL-002 | Navigate next month | Click → | February 2026 |
| CAL-003 | Navigate prev month | Click ← | December 2025 |
| CAL-004 | Today highlighted | Current date | Ring border on today |

### 8.2 Team Member Panel

| ID | Test Case | Expected |
|----|-----------|----------|
| CAL-005 | Show team members | List of same entity+location+dept members |
| CAL-006 | Member color bullets | Each member has unique color |
| CAL-007 | Toggle member visibility | Uncheck → member leaves hidden |
| CAL-008 | "(You)" indicator | Current user marked |

### 8.3 Leave Display Styles

| ID | Test Case | Data | Expected Display |
|----|-----------|------|------------------|
| CAL-009 | Partial day (CUSTOM_HOURS) | Jan 20, 09:00-14:00 | Bullet + "9:00 AM - 2:00 PM Minh" |
| CAL-010 | Single full day | Jan 20, FULL_DAY | Colored bar, "Minh's Leave" |
| CAL-011 | Multi-day span | Jan 20-22 | Continuous bar across 3 days |
| CAL-012 | Overlapping leaves | John Jan 20-22, Jane Jan 21-23 | Both visible, stacked |
| CAL-013 | Tooltip on hover | Hover over leave | Full name, category, hours |

---

## 9. Notifications

### 9.1 In-App Notifications

| ID | Test Case | Trigger | Recipients |
|----|-----------|---------|------------|
| NOTIF-001 | Request submitted | Employee submits | Manager, HR |
| NOTIF-002 | Request approved | Manager approves | Employee |
| NOTIF-003 | Request rejected | Manager rejects | Employee |
| NOTIF-004 | Request cancelled | Employee cancels | Manager, HR |
| NOTIF-005 | Balance adjusted | HR adjusts | Employee |

### 9.2 Notification UI

| ID | Test Case | Expected |
|----|-----------|----------|
| NOTIF-006 | Bell icon badge | Shows unread count |
| NOTIF-007 | Dropdown list | Last 20 notifications |
| NOTIF-008 | Click notification | Navigate to relevant page |
| NOTIF-009 | Mark as read | Click marks single as read |
| NOTIF-010 | Mark all read | Button marks all as read |
| NOTIF-011 | Unread count updates | Real-time or polling update |

### 9.3 Email Notifications (If implemented)

| ID | Test Case | Trigger | Email To |
|----|-----------|---------|----------|
| NOTIF-012 | Request submitted email | Submit | Manager only |
| NOTIF-013 | Approved email | Approve | Employee only |
| NOTIF-014 | Rejected email | Reject | Employee only |
| NOTIF-015 | No email to HR | Any event | HR gets in-app only |

---

## 10. HR Admin Functions

### 10.1 User Setup Workflow

| ID | Test Case | Action | Expected |
|----|-----------|--------|----------|
| HR-001 | List pending users | GET /api/users/?status=PENDING_SETUP | Users without dept |
| HR-002 | Setup user form | Click user | Form with dept, manager, role, balance |
| HR-003 | Complete setup | Fill form, submit | User activated, balance created |
| HR-004 | Apply default balance | Click button | allocated_hours = 96 |

### 10.2 Balance Adjustment

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| HR-005 | Increase allocation | allocated_hours: 96→120 | Balance updated |
| HR-006 | Add adjustment | adjusted_hours: +8 | Remaining increases by 8 |
| HR-007 | Negative adjustment | adjusted_hours: -8 | Remaining decreases by 8 |
| HR-008 | Reason required | No reason provided | Error: "Reason required" |
| HR-009 | Audit log created | Any adjustment | AuditLog with old/new values |

### 10.3 Leave Categories

| ID | Test Case | Action | Expected |
|----|-----------|--------|----------|
| HR-010 | List categories | GET /api/leaves/categories/ | All categories |
| HR-011 | Add category | POST with name, code, color | Category created |
| HR-012 | Edit category | PUT | Category updated |
| HR-013 | Deactivate category | is_active=false | Soft deleted, hidden from forms |
| HR-014 | Reorder categories | Update sort_order | Display order changes |
| HR-015 | Duplicate code | Same code as existing | Error: "Code must be unique" |

---

## 11. Public Holidays

### 11.1 Holiday Management

| ID | Test Case | Data | Expected |
|----|-----------|------|----------|
| HOL-001 | Add holiday | name, date, entity, location | Holiday created |
| HOL-002 | Entity-scoped holiday | entity_id set, location_id null | Applies to all locations in entity |
| HOL-003 | Location-scoped holiday | entity_id + location_id set | Applies to specific location |
| HOL-004 | Global holiday | entity_id=null, location_id=null | Applies to all |
| HOL-005 | Recurring holiday | is_recurring=true | Copy to next year option |

### 11.2 Holiday Impact on Leave Calculation

| ID | Test Case | Setup | Expected |
|----|-----------|-------|----------|
| HOL-006 | Holiday excluded from hours | Jan 1 holiday, request Jan 1-3 | total_hours=16 (not 24) |
| HOL-007 | User location matches holiday | User@HCMC, holiday@HCMC | Holiday applies |
| HOL-008 | User location differs | User@Singapore, holiday@HCMC only | Holiday doesn't apply |

---

## 12. Year Boundary & Time

### 12.1 Year Transitions

| ID | Test Case | Setup | Expected |
|----|-----------|-------|----------|
| YEAR-001 | Balance per year | User has 2025 and 2026 balances | Each year independent |
| YEAR-002 | New year auto-create | User accesses 2027, no balance | Create 2027 balance (96h default) |
| YEAR-003 | Historical balance view | Request year=2025 | Show 2025 read-only |
| YEAR-004 | Cross-year request | Dec 28 - Jan 5 | Deduct from start_date year (2025) |
| YEAR-005 | Year filter on history | Filter by 2025 | Only 2025 requests shown |

### 12.2 Time-Based Testing

| ID | Test Case | Mock Time | Expected |
|----|-----------|-----------|----------|
| YEAR-006 | Balance on Dec 31 | 2026-12-31 23:59 | Returns 2026 balance |
| YEAR-007 | Balance on Jan 1 | 2027-01-01 00:01 | Returns/creates 2027 balance |
| YEAR-008 | Request on year boundary | Submit Dec 31 for Jan 2 | Uses 2027 start_date year |

---

## 13. API Security

### 13.1 Authentication

| ID | Test Case | Request | Expected |
|----|-----------|---------|----------|
| SEC-001 | No auth token | Any protected endpoint | 401 Unauthorized |
| SEC-002 | Invalid token | Malformed JWT/session | 401 Unauthorized |
| SEC-003 | Expired token | Expired JWT | 401 Unauthorized |
| SEC-004 | Valid token | Correct auth | 200 OK |

### 13.2 Authorization

| ID | Test Case | Request | Expected |
|----|-----------|---------|----------|
| SEC-005 | Access other user's data | GET /api/users/{other-id}/balance/ | 403 Forbidden |
| SEC-006 | Modify other user's request | PUT /api/leaves/requests/{other}/ | 403 Forbidden |
| SEC-007 | Approve own request | POST /api/leaves/requests/{own}/approve/ | 403 Forbidden |
| SEC-008 | IDOR attempt | Guess UUID | 403 or 404 |

### 13.3 Input Validation

| ID | Test Case | Input | Expected |
|----|-----------|-------|----------|
| SEC-009 | SQL injection | reason: "'; DROP TABLE users;--" | Sanitized, no SQL exec |
| SEC-010 | XSS attempt | reason: "<script>alert(1)</script>" | Escaped in output |
| SEC-011 | Oversized payload | 10MB request body | 413 Payload Too Large |
| SEC-012 | Invalid UUID | GET /api/users/not-a-uuid/ | 400 Bad Request |

---

## 14. Performance

### 14.1 Load Testing

| ID | Test Case | Load | Expected |
|----|-----------|------|----------|
| PERF-001 | Dashboard load | 100 concurrent users | < 500ms response |
| PERF-002 | Calendar load | Large team (50 members), 1 month | < 1s response |
| PERF-003 | Approval inbox | 100 pending requests | < 500ms response |
| PERF-004 | Balance calculation | Complex balance | < 100ms |

### 14.2 Database Performance

| ID | Test Case | Query | Expected |
|----|-----------|-------|----------|
| PERF-005 | Index on leave_requests | Filter by user_id, status | Uses index |
| PERF-006 | Index on notifications | Filter by user_id, is_read | Uses index |
| PERF-007 | Pagination | GET /api/leaves/requests/?page=10 | Efficient offset |

---

## 15. Database Integrity

### 15.1 Constraints

| ID | Test Case | Action | Expected |
|----|-----------|--------|----------|
| DB-001 | Unique user email | Insert duplicate email | Constraint error |
| DB-002 | Unique balance per year | Insert duplicate user+year | Constraint error |
| DB-003 | FK user→entity | Delete entity with users | Cascade or restrict |
| DB-004 | FK request→user | Delete user with requests | Cascade or restrict |

### 15.2 Data Consistency

| ID | Test Case | Scenario | Expected |
|----|-----------|----------|----------|
| DB-005 | Balance after approval | Approve 24h | used_hours += 24 atomically |
| DB-006 | Concurrent approvals | Two managers approve same request | One succeeds, one fails |
| DB-007 | Balance never negative (if enforced) | Approve when balance=0 | Error or warning |

---

## Test Data Seeds

### Users
```sql
INSERT INTO users (email, role, entity_id, location_id, department_id) VALUES
('employee@test.com', 'EMPLOYEE', 'entity-1', 'loc-hcmc', 'dept-eng'),
('manager@test.com', 'MANAGER', 'entity-1', 'loc-hcmc', 'dept-eng'),
('hr@test.com', 'HR', 'entity-1', 'loc-hcmc', 'dept-hr'),
('admin@test.com', 'ADMIN', 'entity-1', 'loc-hcmc', 'dept-hr');
```

### Balances
```sql
INSERT INTO leave_balances (user_id, year, allocated_hours, used_hours, adjusted_hours) VALUES
('employee-id', 2026, 96.00, 24.00, 0.00),  -- Normal
('manager-id', 2026, 120.00, 40.00, 8.00);  -- Higher allocation + adjustment
```

### Leave Requests
```sql
INSERT INTO leave_requests (user_id, start_date, end_date, shift_type, total_hours, status) VALUES
('employee-id', '2026-01-20', '2026-01-20', 'FULL_DAY', 8.00, 'PENDING'),
('employee-id', '2026-01-25', '2026-01-27', 'FULL_DAY', 24.00, 'APPROVED'),
('employee-id', '2026-02-01', '2026-02-01', 'CUSTOM_HOURS', 4.00, 'REJECTED');
```

---

## Test Execution Checklist

- [ ] Unit tests: Models, serializers, utils
- [ ] Integration tests: API endpoints
- [ ] E2E tests: Full user flows (Cypress/Playwright)
- [ ] Security tests: Auth, authz, injection
- [ ] Performance tests: Load, stress
- [ ] Year boundary tests: Time mocking
- [ ] Mobile responsiveness: Viewport tests

---

## Unresolved Questions

1. **Cross-year request handling:** Deduct from start_date year or split?
2. **Cancel approved request:** Allow with balance restore or block?
3. **Negative balance:** Allow with warning or hard block?
4. **Concurrent approval race condition:** Optimistic locking needed?
