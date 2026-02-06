# Django Test Suite Analysis Report
**Date:** 2026-02-05 | **Time:** 23:53 UTC | **Environment:** Docker Compose Backend

---

## Executive Summary

Django test suite executed via `docker compose exec -T backend python -m pytest --verbosity=2` shows **32 failing tests** out of 42 total. Issues fall into 3 main categories:

1. **Entity Model Mismatch** (24 test errors) - Tests use incorrect field names
2. **API Endpoint Missing** (4 test failures) - Audit logs endpoint not implemented
3. **Registration API Changes** (4 test failures) - Endpoint requires entity/location/department

**Status:** CRITICAL - Core test suite non-functional due to model/API changes

---

## Test Results Overview

```
Platform: Linux | Python: 3.12.12 | pytest: 9.0.2 | Django: 6.0.2

Total Tests: 42
✓ Passed: 10 (23.8%)
✗ Failed: 8 (19.0%)
⚠ Errors: 24 (57.1%)

Execution Time: 10.66 seconds
```

### Test Breakdown by Module

| Module | Total | Pass | Fail | Error |
|--------|-------|------|------|-------|
| users/tests/test_auth.py | 9 | 5 | 4 | 0 |
| core/tests/test_notifications.py | 5 | 5 | 0 | 0 |
| core/tests/test_audit_logs.py | 4 | 0 | 4 | 0 |
| leaves/tests/test_holidays.py | 8 | 0 | 0 | 8 |
| leaves/tests/test_reports.py | 3 | 0 | 0 | 3 |
| leaves/tests/test_requests.py | 13 | 0 | 0 | 13 |
| organizations/tests | 0 | 0 | 0 | 0 |

---

## Critical Issues Summary

### Issue 1: Entity Model Field Name Mismatch (24 Errors)

**Severity:** CRITICAL - Blocks 24 tests
**Root Cause:** Tests use `name=` parameter but model uses `entity_name=`

**Affected Tests (24):**
- leaves/tests/test_holidays.py (8 tests) - All fail during setup_holidays fixture
- leaves/tests/test_reports.py (3 tests) - All fail during setup
- leaves/tests/test_requests.py (13 tests) - All fail during fixture

**Error Details:**
```
TypeError: Entity() got unexpected keyword arguments: 'name'
  at organizations.models.Entity.__init__()
```

**Model Reality:**
```python
class Entity(models.Model):
    entity_name = models.CharField(max_length=100, unique=True)  # Not 'name'
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
```

**Test Usage (WRONG):**
```python
entity = Entity.objects.create(name='Test Entity', code='TEST')
```

**Affected Files:**
- `/home/silver/test-leave/leaves/tests/test_requests.py` - Line setup fixture
- `/home/silver/test-leave/leaves/tests/test_holidays.py` - Line 17 setup_holidays
- `/home/silver/test-leave/leaves/tests/test_reports.py` - Line setup fixture

---

### Issue 2: Audit Logs Endpoint Not Implemented (4 Failures)

**Severity:** CRITICAL - Missing API endpoint
**Root Cause:** Tests expect `/api/v1/notifications/audit-logs/` endpoint but it's not registered

**Affected Tests (4):**
- core/tests/test_audit_logs.py::TestAuditLogs::test_list_audit_logs_admin
- core/tests/test_audit_logs.py::TestAuditLogs::test_list_audit_logs_employee_forbidden
- core/tests/test_audit_logs.py::TestAuditLogs::test_filter_audit_logs_by_action
- core/tests/test_audit_logs.py::TestAuditLogs::test_filter_audit_logs_by_entity_type

**Error Details:**
```
AssertionError: assert 404 == 200
  Response Status: 404 Not Found
  Endpoint Requested: /api/v1/notifications/audit-logs/

AssertionError: assert 404 == 403
  Response Status: 404 Not Found (should be 403 Forbidden)
```

**Current Implementation:**
- `/home/silver/test-leave/core/urls.py` - Only has notification endpoints
- `/home/silver/test-leave/core/views.py` - NotificationListView exists but no AuditLogListView

**Missing Endpoint:**
```python
# Not implemented in core/urls.py or core/views.py
path('audit-logs/', AuditLogListView.as_view(), name='audit_logs')
```

---

### Issue 3: User Registration API Changed (4 Failures)

**Severity:** HIGH - API contract changed
**Root Cause:** RegisterSerializer now requires `entity`, `location`, `department` UUIDs as mandatory fields

**Affected Tests (4):**
- users/tests/test_auth.py::TestAuthentication::test_register_user_success
- users/tests/test_auth.py::TestAuthentication::test_login_success
- users/tests/test_auth.py::TestAuthentication::test_logout_success
- users/tests/test_auth.py::TestAuthentication::test_onboarding_success

**Error Details:**
```
Test: test_register_user_success
Expected Status: 201 Created
Actual Status: 400 Bad Request
Issue: Missing required fields entity, location, department

Test: test_onboarding_success
TypeError: Entity() got unexpected keyword arguments: 'name'
```

**Serializer Reality:**
```python
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    password_confirm = serializers.CharField(required=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    employee_code = serializers.CharField(required=False)
    # These are NEW REQUIRED fields:
    entity = serializers.UUIDField(required=True)          # NEW
    location = serializers.UUIDField(required=True)        # NEW
    department = serializers.UUIDField(required=True)      # NEW
```

**Test Usage (INCOMPLETE):**
```python
response = client.post('/api/v1/auth/register/', {
    'email': 'test@example.com',
    'password': 'TestPass123!',
    'password_confirm': 'TestPass123!',
    'first_name': 'Test',
    'last_name': 'User',
    # Missing: entity, location, department UUIDs
})
```

---

## Passing Tests (10/42)

All notification tests pass successfully:

✓ core/tests/test_notifications.py::TestNotifications::test_list_notifications
✓ core/tests/test_notifications.py::TestNotifications::test_unread_count
✓ core/tests/test_notifications.py::TestNotifications::test_mark_notification_read
✓ core/tests/test_notifications.py::TestNotifications::test_mark_all_read
✓ core/tests/test_notifications.py::TestNotifications::test_notification_not_found

Partial user auth tests pass:

✓ users/tests/test_auth.py::TestAuthentication::test_register_user_password_mismatch
✓ users/tests/test_auth.py::TestAuthentication::test_register_user_duplicate_email
✓ users/tests/test_auth.py::TestAuthentication::test_login_invalid_credentials
✓ users/tests/test_auth.py::TestAuthentication::test_get_user_me_authenticated
✓ users/tests/test_auth.py::TestAuthentication::test_get_user_me_unauthenticated

---

## Detailed Failure Analysis

### A. Entity Model Errors (24 tests)

**File:** `/home/silver/test-leave/organizations/models.py`

Current model definition (correct):
```python
class Entity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_name = models.CharField(max_length=100, unique=True)  # ← This is the field
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
```

All test files use wrong field:
```python
Entity.objects.create(name='Test Entity', code='TEST')  # WRONG: 'name'
```

**Test Files to Fix:**
1. `/home/silver/test-leave/leaves/tests/test_requests.py`
   - Fixture: setup_user_with_entity (implied in test class)
   - Fix: Change `name=` to `entity_name=`

2. `/home/silver/test-leave/leaves/tests/test_holidays.py`
   - Line 17: `entity = Entity.objects.create(name='Test Entity', code='TEST')`
   - Fix: Change to `entity_name='Test Entity'`

3. `/home/silver/test-leave/leaves/tests/test_reports.py`
   - Similar setup issues
   - Fix: Change `name=` to `entity_name=`

Same issue with Location and Department models:
```python
# Location uses location_name, not name
# Department uses department_name, not name
```

---

### B. Audit Logs Endpoint (4 failures)

**File:** `/home/silver/test-leave/core/urls.py`

Current implementation only registers notification endpoints:
```python
urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<uuid:pk>/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('unread-count/', NotificationUnreadCountView.as_view(), name='notification_unread_count'),
]
```

Missing audit logs endpoint. Tests expect:
- GET `/api/v1/notifications/audit-logs/` - List with pagination
- Query filters: `?action=`, `?entity_type=`
- Permission: ADMIN only (403 for regular employees)

**Related Files:**
- `/home/silver/test-leave/core/models.py` - Has AuditLog model
- `/home/silver/test-leave/core/views.py` - Missing AuditLogListView
- `/home/silver/test-leave/core/tests/test_audit_logs.py` - Tests expect the endpoint

---

### C. Registration Endpoint (4 failures)

**File:** `/home/silver/test-leave/users/serializers/serializers.py`

RegisterSerializer now requires organization data at registration time (recent change):

```python
class RegisterSerializer(serializers.Serializer):
    # ... email, password fields ...
    # NEW REQUIRED FIELDS:
    entity = serializers.UUIDField(required=True)
    location = serializers.UUIDField(required=True)
    department = serializers.UUIDField(required=True)

    def validate_entity(self, value):
        return validate_active_relationship(Entity, value, 'entity')
```

Old test flow (no longer works):
1. Register user without entity/location/department
2. Call `/api/v1/auth/onboarding/` to assign them later

New test flow (required):
1. Create Entity, Location, Department test fixtures first
2. Pass their UUIDs during registration
3. Onboarding is completed automatically

---

## Test Coverage Analysis

**Critical Gaps:**
- Audit log functionality (endpoint missing)
- Leave allocation functions (leaves/services.py) - No tests for new functions
- Exempt vacation command (new management command) - No tests
- Balance type functionality (new feature) - No tests
- Notification routing (new feature) - No tests for routing logic

**Tested Areas:**
- Notification CRUD (✓)
- User authentication basics (partial ✓)
- Password validation (✓)
- Basic onboarding structure (✗ broken by fixture)

---

## Recommendations

### Priority 1: Fix Entity Model Field References (Unblock 24 tests)

1. **File:** `/home/silver/test-leave/leaves/tests/test_holidays.py`
   - Line 17: `Entity.objects.create(name=` → `Entity.objects.create(entity_name=`
   - Line 18: `Location.objects.create(name=` → `Location.objects.create(location_name=`
   - Line 22: `Department.objects.create(name=` → `Department.objects.create(department_name=`

2. **File:** `/home/silver/test-leave/leaves/tests/test_reports.py`
   - Update similar field references

3. **File:** `/home/silver/test-leave/leaves/tests/test_requests.py`
   - Update similar field references

### Priority 2: Implement Audit Logs Endpoint (Fix 4 failures)

1. **Add view:** `/home/silver/test-leave/core/views.py`
   ```python
   class AuditLogListView(generics.ListAPIView):
       """List audit logs with filtering"""
       permission_classes = [IsAuthenticated, IsAdmin]
       queryset = AuditLog.objects.all().order_by('-created_at')
       filter_fields = ['action', 'entity_type']
       # Add pagination
   ```

2. **Register URL:** `/home/silver/test-leave/core/urls.py`
   ```python
   path('audit-logs/', AuditLogListView.as_view(), name='audit_logs'),
   ```

3. **Add AuditLog serializer** if not exists

### Priority 3: Update Registration Tests (Fix 4 failures)

1. **Update test fixtures** to create Entity/Location/Department before registration
2. **Pass required UUIDs** in registration payload
3. **Remove redundant onboarding tests** if registration now completes onboarding

### Priority 4: Add Tests for New Features

1. **Allocation functions** (leaves/services.py)
   - Test new allocation functions
   - Test balance calculations with new balance_type

2. **Exempt vacation command** (leaves/management/commands/recalculate_exempt_vacation.py)
   - Test command execution
   - Test data transformations

3. **Balance view changes** (leaves/views/balances.py)
   - Test new fields returned
   - Test filtering by balance_type

4. **Signal changes** (users/signals.py)
   - Test signal handler execution
   - Test side effects

---

## Files Affected by Recent Changes

### Changes Requiring Test Updates:

1. **organizations/models.py**
   - Entity: `name` → `entity_name`
   - Location: `name` → `location_name`
   - Department: `name` → `department_name`
   - Status: All test files use old field names

2. **users/serializers/serializers.py**
   - RegisterSerializer added 3 required fields
   - Old tests don't provide these UUIDs
   - Status: 4 tests fail with 400 Bad Request

3. **users/signals.py**
   - Updated signal (no test coverage)
   - Status: Unknown behavior

4. **leaves/services.py**
   - New allocation functions (no test coverage)
   - Status: Not tested

5. **leaves/views/balances.py**
   - Updated balance view (no specific tests)
   - Status: Partial coverage

6. **leaves/management/commands/recalculate_exempt_vacation.py**
   - New management command (no test coverage)
   - Status: Not tested

---

## Unresolved Questions

1. **What is the intended registration flow?**
   - Should users be able to register without organizational data?
   - Should entity/location/department be assigned later?
   - Or is it now mandatory at registration time?

2. **Where should audit logs endpoint be registered?**
   - In core.urls.py alongside notifications?
   - In a separate admin.urls.py?

3. **Are allocation functions tested elsewhere?**
   - Are there integration tests for allocation logic?
   - Is there a test for the new `recalculate_exempt_vacation` command?

4. **What is the expected behavior of updated signals?**
   - What does users/signals.py do now?
   - Should there be tests for signal side effects?

5. **Is there test coverage for new balance_type functionality?**
   - Tests for filtering by balance_type?
   - Tests for different allocation rates per type?

---

## Next Steps

1. Fix Entity/Location/Department field names in all test files (30 min)
2. Implement AuditLogListView and register endpoint (45 min)
3. Update registration test fixtures and payloads (30 min)
4. Run full test suite again to verify fixes
5. Add tests for new features (allocation, balance_type, command) (2-3 hours)
6. Aim for >80% code coverage on critical paths

---

**Report Generated:** 2026-02-05 23:53 UTC
**Test Environment:** Docker Compose with PostgreSQL 16
**Python Version:** 3.12.12
**Django Version:** 6.0.2
