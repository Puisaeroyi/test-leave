# Leave Management System - API Overview

> **Version:** 1.0 | **Updated:** 2026-01-20
> **Backend:** Django 5.x + Django REST Framework
> **Auth:** OAuth 2.0 (Google) via django-allauth + Session/JWT
> **Base URL:** `/api/v1/`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Users](#2-users)
3. [Organizations](#3-organizations)
4. [Leave Balances](#4-leave-balances)
5. [Leave Requests](#5-leave-requests)
6. [Leave Categories](#6-leave-categories)
7. [Public Holidays](#7-public-holidays)
8. [Notifications](#8-notifications)
9. [Audit Logs](#9-audit-logs)
10. [Error Handling](#10-error-handling)
11. [Rate Limiting](#11-rate-limiting)

---

## 1. Authentication

### 1.1 OAuth Login Flow

| Step | Endpoint | Method | Description |
|------|----------|--------|-------------|
| 1 | `/auth/google/login/` | GET | Redirect to Google OAuth |
| 2 | `/auth/google/callback/` | GET | OAuth callback handler |
| 3 | `/auth/logout/` | POST | End session |

### 1.2 Session/Token Info

```
GET /api/v1/auth/me/
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@company.com",
  "first_name": "Minh",
  "last_name": "Nguyen",
  "role": "EMPLOYEE",
  "status": "ACTIVE",
  "entity": { "id": "uuid", "name": "Acme Corp" },
  "location": { "id": "uuid", "name": "HCMC Office" },
  "department": { "id": "uuid", "name": "Engineering" },
  "avatar_url": "https://...",
  "is_onboarded": true
}
```

**Permissions:** Authenticated

---

## 2. Users

### 2.1 List Users

```
GET /api/v1/users/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter: `ACTIVE`, `INACTIVE` |
| `role` | string | Filter: `EMPLOYEE`, `MANAGER`, `HR`, `ADMIN` |
| `entity_id` | uuid | Filter by entity |
| `location_id` | uuid | Filter by location |
| `department_id` | uuid | Filter by department |
| `search` | string | Search by name/email |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Response:**
```json
{
  "count": 50,
  "next": "/api/v1/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "email": "user@company.com",
      "first_name": "Minh",
      "last_name": "Nguyen",
      "role": "EMPLOYEE",
      "status": "ACTIVE",
      "department": { "id": "uuid", "name": "Engineering" },
      "location": { "id": "uuid", "name": "HCMC" }
    }
  ]
}
```

**Permissions:** HR, ADMIN

---

### 2.2 Get User Details

```
GET /api/v1/users/{id}/
```

**Response:** Full user object with nested entity/location/department

**Permissions:** Self, HR, ADMIN

---

### 2.3 Update User Profile

```
PATCH /api/v1/users/{id}/
```

**Request Body:**
```json
{
  "first_name": "Minh",
  "last_name": "Nguyen",
  "avatar_url": "https://..."
}
```

**Permissions:** Self (limited fields), HR/ADMIN (all fields)

---

### 2.4 Complete Onboarding

```
POST /api/v1/users/onboarding/
```

**Request Body:**
```json
{
  "entity_id": "uuid",
  "location_id": "uuid",
  "department_id": "uuid",
  "full_name": "Minh Nguyen"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "ACTIVE",
  "entity": { ... },
  "location": { ... },
  "department": { ... },
  "balance": {
    "year": 2026,
    "allocated_hours": 96.00,
    "used_hours": 0.00,
    "remaining_hours": 96.00
  }
}
```

**Notes:**
- Auto-creates leave balance for current year
- Sets user status to ACTIVE

**Permissions:** Self (not yet onboarded)

---

### 2.5 HR: Setup User

```
POST /api/v1/users/{id}/setup/
```

**Request Body:**
```json
{
  "department_id": "uuid",
  "role": "EMPLOYEE",
  "join_date": "2026-01-15",
  "allocated_hours": 96.00
}
```

**Permissions:** HR, ADMIN

---

## 3. Organizations

### 3.1 List Entities

```
GET /api/v1/organizations/entities/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Acme Corp",
    "code": "ACME",
    "is_active": true
  }
]
```

**Permissions:** Authenticated

---

### 3.2 List Locations

```
GET /api/v1/organizations/locations/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `entity_id` | uuid | Filter by entity (required for cascading) |

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "HCMC Office",
    "city": "Ho Chi Minh City",
    "country": "Vietnam",
    "timezone": "Asia/Ho_Chi_Minh"
  }
]
```

**Permissions:** Authenticated

---

### 3.3 List Departments

```
GET /api/v1/organizations/departments/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `entity_id` | uuid | Filter by entity |

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Engineering",
    "code": "ENG"
  }
]
```

**Permissions:** Authenticated

---

### 3.4 Get Team Members

```
GET /api/v1/organizations/team/
```

**Response:** List of users in same entity + location + department as requester

**Permissions:** Authenticated

---

## 4. Leave Balances

### 4.1 Get My Balance

```
GET /api/v1/leaves/balance/me/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `year` | int | Year (default: current year) |

**Response:**
```json
{
  "id": "uuid",
  "year": 2026,
  "allocated_hours": 96.00,
  "used_hours": 24.00,
  "adjusted_hours": 8.00,
  "remaining_hours": 80.00,
  "remaining_days": 10.0
}
```

**Computed Fields:**
- `remaining_hours = allocated_hours + adjusted_hours - used_hours`
- `remaining_days = remaining_hours / 8`

**Permissions:** Authenticated

---

### 4.2 Get User Balance (HR)

```
GET /api/v1/leaves/balance/{user_id}/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `year` | int | Year (default: current year) |

**Permissions:** HR, ADMIN, MANAGER (team only)

---

### 4.3 Adjust Balance (HR)

```
POST /api/v1/leaves/balance/{user_id}/adjust/
```

**Request Body:**
```json
{
  "year": 2026,
  "allocated_hours": 120.00,
  "adjustment_hours": 8.00,
  "reason": "Promoted to Manager tier"
}
```

**Notes:**
- `allocated_hours`: Override base allocation (optional)
- `adjustment_hours`: Add/subtract from adjusted_hours (optional)
- `reason`: Required for audit trail

**Response:**
```json
{
  "id": "uuid",
  "year": 2026,
  "allocated_hours": 120.00,
  "used_hours": 24.00,
  "adjusted_hours": 8.00,
  "remaining_hours": 104.00,
  "audit_log_id": "uuid"
}
```

**Permissions:** HR, ADMIN

---

## 5. Leave Requests

### 5.1 List My Requests

```
GET /api/v1/leaves/requests/me/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED` |
| `year` | int | Filter by year of start_date |
| `page` | int | Page number |
| `page_size` | int | Items per page |

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": "uuid",
      "start_date": "2026-01-20",
      "end_date": "2026-01-22",
      "shift_type": "FULL_DAY",
      "start_time": null,
      "end_time": null,
      "total_hours": 24.00,
      "status": "APPROVED",
      "category": { "id": "uuid", "name": "Annual Leave", "color": "#4CAF50" },
      "reason": "Family vacation",
      "approved_by": { "id": "uuid", "name": "Manager Name" },
      "approved_at": "2026-01-18T10:30:00Z",
      "created_at": "2026-01-15T09:00:00Z"
    }
  ]
}
```

**Permissions:** Authenticated

---

### 5.2 Create Leave Request

```
POST /api/v1/leaves/requests/
```

**Request Body (Full Day):**
```json
{
  "start_date": "2026-01-20",
  "end_date": "2026-01-22",
  "shift_type": "FULL_DAY",
  "leave_category_id": "uuid",
  "reason": "Family vacation",
  "attachment_url": "https://..."
}
```

**Request Body (Custom Hours):**
```json
{
  "start_date": "2026-01-20",
  "end_date": "2026-01-20",
  "shift_type": "CUSTOM_HOURS",
  "start_time": "09:00",
  "end_time": "13:00",
  "leave_category_id": "uuid",
  "reason": "Doctor appointment"
}
```

**Response:**
```json
{
  "id": "uuid",
  "start_date": "2026-01-20",
  "end_date": "2026-01-22",
  "shift_type": "FULL_DAY",
  "total_hours": 24.00,
  "status": "PENDING",
  "created_at": "2026-01-15T09:00:00Z"
}
```

**Hours Calculation:**
- `FULL_DAY`: working_days × 8 (excludes weekends + holidays)
- `CUSTOM_HOURS`: end_time - start_time

**Validation:**
- `end_date >= start_date`
- `start_date >= today`
- No overlapping requests
- Sufficient balance (warning if insufficient)

**Side Effects:**
- Creates notification for manager(s)

**Permissions:** Authenticated (with dept assigned)

---

### 5.3 Get Request Details

```
GET /api/v1/leaves/requests/{id}/
```

**Response:** Full request object with user, category, approver details

**Permissions:** Owner, Manager (team), HR, ADMIN

---

### 5.4 Update Request

```
PATCH /api/v1/leaves/requests/{id}/
```

**Request Body:**
```json
{
  "start_date": "2026-01-21",
  "end_date": "2026-01-23",
  "reason": "Updated reason"
}
```

**Validation:**
- Only `PENDING` requests can be edited
- Recalculates `total_hours`

**Permissions:** Owner (PENDING only)

---

### 5.5 Cancel Request

```
POST /api/v1/leaves/requests/{id}/cancel/
```

**Response:**
```json
{
  "id": "uuid",
  "status": "CANCELLED",
  "cancelled_at": "2026-01-16T10:00:00Z"
}
```

**Validation:**
- Only `PENDING` requests can be cancelled

**Side Effects:**
- Notifies manager(s)

**Permissions:** Owner (PENDING only)

---

### 5.6 Manager: List Pending Approvals

```
GET /api/v1/leaves/requests/pending/
```

**Response:** List of PENDING requests for manager's assigned dept+location combinations via DEPARTMENT_MANAGER junction

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Search by employee name |
| `sort` | string | `created_at` (default), `-created_at` |

**Permissions:** MANAGER, HR, ADMIN

---

### 5.7 Approve Request

```
POST /api/v1/leaves/requests/{id}/approve/
```

**Request Body:**
```json
{
  "comment": "Approved. Enjoy your vacation!"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "APPROVED",
  "approved_by": { "id": "uuid", "name": "Manager Name" },
  "approved_at": "2026-01-18T10:30:00Z",
  "approver_comment": "Approved. Enjoy your vacation!"
}
```

**Side Effects:**
- Deducts `total_hours` from employee's `used_hours`
- Creates notification for employee
- Creates audit log

**Permissions:** MANAGER (team via DEPARTMENT_MANAGER), HR, ADMIN

---

### 5.8 Reject Request

```
POST /api/v1/leaves/requests/{id}/reject/
```

**Request Body:**
```json
{
  "reason": "Insufficient team coverage during this period. Please reschedule."
}
```

**Validation:**
- `reason` required (min 10 characters)

**Response:**
```json
{
  "id": "uuid",
  "status": "REJECTED",
  "rejection_reason": "Insufficient team coverage...",
  "approved_by": { "id": "uuid", "name": "Manager Name" },
  "approved_at": "2026-01-18T10:30:00Z"
}
```

**Side Effects:**
- Creates notification for employee
- No balance change

**Permissions:** MANAGER (team), HR, ADMIN

---

### 5.9 Team Calendar

```
GET /api/v1/leaves/calendar/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `month` | int | Month (1-12) |
| `year` | int | Year |
| `member_ids` | uuid[] | Filter by specific members (optional) |

**Response:**
```json
{
  "month": 1,
  "year": 2026,
  "team_members": [
    {
      "id": "uuid",
      "name": "Minh Nguyen",
      "color": "#4CAF50",
      "is_current_user": true
    }
  ],
  "leaves": [
    {
      "id": "uuid",
      "member_id": "uuid",
      "start_date": "2026-01-20",
      "end_date": "2026-01-22",
      "is_full_day": true,
      "start_time": null,
      "end_time": null,
      "category": "Annual Leave",
      "total_hours": 24.00
    },
    {
      "id": "uuid",
      "member_id": "uuid",
      "start_date": "2026-01-25",
      "end_date": "2026-01-25",
      "is_full_day": false,
      "start_time": "09:00",
      "end_time": "13:00",
      "category": "Personal Leave",
      "total_hours": 4.00
    }
  ],
  "holidays": [
    {
      "date": "2026-01-01",
      "name": "New Year's Day"
    }
  ]
}
```

**Display Logic:**
- `is_full_day = true` → Multi-day bar with name
- `is_full_day = false` → Bullet + "HH:MM AM - HH:MM PM Name"

**Permissions:** Authenticated

---

## 6. Leave Categories

### 6.1 List Categories

```
GET /api/v1/leaves/categories/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `is_active` | bool | Filter active only (default: true) |

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Annual Leave",
    "code": "AL",
    "color": "#4CAF50",
    "requires_document": false,
    "sort_order": 1,
    "is_active": true
  },
  {
    "id": "uuid",
    "name": "Sick Leave",
    "code": "SL",
    "color": "#F44336",
    "requires_document": true,
    "sort_order": 2,
    "is_active": true
  }
]
```

**Note:** Categories are for reporting only, not separate balances.

**Permissions:** Authenticated

---

### 6.2 Create Category (Admin)

```
POST /api/v1/leaves/categories/
```

**Request Body:**
```json
{
  "name": "Parental Leave",
  "code": "PL",
  "color": "#9C27B0",
  "requires_document": true,
  "sort_order": 5
}
```

**Permissions:** ADMIN

---

### 6.3 Update Category (Admin)

```
PATCH /api/v1/leaves/categories/{id}/
```

**Permissions:** ADMIN

---

### 6.4 Deactivate Category (Admin)

```
DELETE /api/v1/leaves/categories/{id}/
```

**Note:** Soft delete (sets `is_active = false`)

**Permissions:** ADMIN

---

## 7. Public Holidays

### 7.1 List Holidays

```
GET /api/v1/holidays/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `year` | int | Filter by year |
| `entity_id` | uuid | Filter by entity |
| `location_id` | uuid | Filter by location |

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "New Year's Day",
    "date": "2026-01-01",
    "entity": null,
    "location": null,
    "is_recurring": true
  },
  {
    "id": "uuid",
    "name": "Tet Holiday",
    "date": "2026-01-29",
    "entity": { "id": "uuid", "name": "Acme Vietnam" },
    "location": null,
    "is_recurring": true
  }
]
```

**Scope Logic:**
- `entity=null, location=null` → Global holiday
- `entity=X, location=null` → All locations in entity
- `entity=X, location=Y` → Specific location only

**Permissions:** Authenticated

---

### 7.2 Create Holiday (Admin)

```
POST /api/v1/holidays/
```

**Request Body:**
```json
{
  "name": "Company Anniversary",
  "date": "2026-03-15",
  "entity_id": "uuid",
  "location_id": null,
  "is_recurring": true
}
```

**Permissions:** ADMIN

---

### 7.3 Update Holiday (Admin)

```
PATCH /api/v1/holidays/{id}/
```

**Permissions:** ADMIN

---

### 7.4 Delete Holiday (Admin)

```
DELETE /api/v1/holidays/{id}/
```

**Permissions:** ADMIN

---

### 7.5 Copy Holidays to Next Year

```
POST /api/v1/holidays/copy/
```

**Request Body:**
```json
{
  "from_year": 2026,
  "to_year": 2027,
  "recurring_only": true
}
```

**Permissions:** ADMIN

---

## 8. Notifications

### 8.1 List My Notifications

```
GET /api/v1/notifications/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `is_read` | bool | Filter by read status |
| `page` | int | Page number |
| `page_size` | int | Items per page (default: 20) |

**Response:**
```json
{
  "unread_count": 3,
  "results": [
    {
      "id": "uuid",
      "type": "LEAVE_APPROVED",
      "title": "Leave Request Approved",
      "message": "Your leave request for Jan 20-22 has been approved.",
      "link": "/leaves/requests/uuid",
      "is_read": false,
      "created_at": "2026-01-18T10:30:00Z"
    }
  ]
}
```

**Notification Types:**
- `LEAVE_SUBMITTED` - New request (to manager)
- `LEAVE_APPROVED` - Request approved (to employee)
- `LEAVE_REJECTED` - Request rejected (to employee)
- `LEAVE_CANCELLED` - Request cancelled (to manager)
- `BALANCE_ADJUSTED` - Balance changed (to employee)

**Permissions:** Authenticated

---

### 8.2 Mark as Read

```
PATCH /api/v1/notifications/{id}/
```

**Request Body:**
```json
{
  "is_read": true
}
```

**Permissions:** Owner

---

### 8.3 Mark All as Read

```
POST /api/v1/notifications/mark-all-read/
```

**Response:**
```json
{
  "updated_count": 5
}
```

**Permissions:** Authenticated

---

### 8.4 Get Unread Count

```
GET /api/v1/notifications/unread-count/
```

**Response:**
```json
{
  "count": 3
}
```

**Permissions:** Authenticated

---

## 9. Audit Logs

### 9.1 List Audit Logs (Admin)

```
GET /api/v1/audit-logs/
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `user_id` | uuid | Filter by actor |
| `entity_type` | string | Filter: `leave_request`, `leave_balance`, `user` |
| `action` | string | Filter: `CREATE`, `UPDATE`, `DELETE`, `APPROVE`, `REJECT` |
| `start_date` | date | From date |
| `end_date` | date | To date |

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "user": { "id": "uuid", "name": "Manager Name" },
      "action": "APPROVE",
      "entity_type": "leave_request",
      "entity_id": "uuid",
      "old_values": { "status": "PENDING" },
      "new_values": { "status": "APPROVED" },
      "ip_address": "192.168.1.1",
      "created_at": "2026-01-18T10:30:00Z"
    }
  ]
}
```

**Permissions:** ADMIN

---

## 10. Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "start_date": ["Start date cannot be in the past"],
      "end_date": ["End date must be after start date"]
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `UNAUTHORIZED` | 401 | Not authenticated |
| `FORBIDDEN` | 403 | No permission |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Duplicate or overlap |
| `INSUFFICIENT_BALANCE` | 422 | Not enough leave hours |
| `INTERNAL_ERROR` | 500 | Server error |

---

## 11. Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Read endpoints | 100 requests | 1 minute |
| Write endpoints | 30 requests | 1 minute |
| File uploads | 10 requests | 1 minute |

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706104800
```

---

## API Versioning

- Current version: `v1`
- Version in URL: `/api/v1/...`
- Deprecation policy: 6 months notice before removal

---

## SDK Auto-Documentation

Django REST Framework auto-generates interactive API docs:

- **Swagger UI:** `/api/docs/`
- **ReDoc:** `/api/redoc/`
- **OpenAPI Schema:** `/api/schema/`

---

## Unresolved Questions

1. **Cancel approved request:** Should it restore balance or require HR adjustment?
2. **Negative balance:** Hard block or warning with override?
3. **Email domain validation:** Config file or database table?
4. **Pagination default:** 20 or 50 items per page?
