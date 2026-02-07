# Codebase Summary

**Last Updated:** 2026-02-07 | **Version:** 1.1.0

## Overview

The Leave Management System is a comprehensive, full-stack web application for managing employee leave requests, approvals, and analytics. Built with Django REST Framework and React, it provides a complete leave lifecycle management platform with multi-tenant organizational support.

**LOC:** 7,177 total (Backend: 1,900, Frontend: 5,277)

---

## Directory Structure

```
test-leave/
├── backend/                  # Django settings package
├── users/                    # User authentication & profile
├── organizations/            # Entity/Location/Department hierarchy
├── leaves/                   # Leave management core
├── core/                     # Notifications & audit logging
├── frontend/src/             # React 19 SPA
├── docs/                     # Project documentation
├── docker-compose.yml        # Multi-container setup
├── manage.py                 # Django CLI
├── requirements.txt          # Python dependencies
├── pytest.ini                # Test configuration
└── README.md                 # Project overview
```

---

## Django Apps Architecture

### 1. users/
**Purpose:** Authentication, user management, and profile management.

**Key Files:**
- `models.py` - Custom User model with roles (EMPLOYEE/MANAGER/HR/ADMIN), approver FK, join_date, onboarding flags
- `views/` - Auth endpoints (register, login, refresh, logout, onboarding, user creation)
- `views/auth.py` - Authentication endpoints using shared create_initial_leave_balance utility
- `views/profile.py` - Profile retrieval and updates
- `views/management.py` - HR/Admin user management
- `views/balance.py` - User balance endpoints
- `serializers/serializers.py` - User and auth data serialization, UserCreateSerializer
- `serializers/utils.py` - Validation utilities
- `viewsets.py` - UserViewSet with create endpoint (POST /api/v1/auth/users/)
- `permissions.py` - Role-based permission checks
- `signals.py` - Create default LeaveBalance on user creation (skip if exists)
- `utils.py` - create_initial_leave_balance utility function
- `resources.py` - Import/export resources

**Key Features:**
- Email-based JWT authentication with token rotation
- Role-based access control (RBAC)
- Approver self-referential relationship
- Onboarding wizard (entity/location/department assignment)
- Password change on first login
- HR/Admin user creation via Settings modal with auto-default password
- User import/export functionality
- Auto-create all 4 leave balance types on user creation

### 2. organizations/
**Purpose:** Organizational hierarchy and timezone management.

**Key Files:**
- `models.py` - Entity, Location, Department, DepartmentManager models
- `views.py` - CRUD endpoints for org hierarchy, EntityCreateView, EntityUpdateView, EntitySoftDeleteView, EntityDeleteImpactView
- `serializers/entity_serializers.py` - EntitySerializer, EntityCreateSerializer, EntityUpdateSerializer
- `serializers/__init__.py` - Serializer exports
- `services.py` - Business logic (soft_delete_entity_cascade, get_entity_delete_impact)
- `admin.py` - Django admin configuration
- `resources.py` - Import/export resources

**Key Features:**
- Multi-tenant support: Entity → Location → Department hierarchy
- 33 timezone options per location
- DepartmentManager junction table (many-to-many)
- Soft-delete patterns with cascade (Entity → Locations → Departments)
- Entity CRUD management (HR/Admin only)
- Delete impact preview before cascade operations

### 3. leaves/
**Purpose:** Leave request lifecycle, balance management, and approval workflow.

**Key Files:**
- `models.py` - LeaveCategory, LeaveBalance, LeaveRequest, PublicHoliday, BusinessTrip
- `services.py` - LeaveApprovalService (atomic approve/reject), balance calculations
- `utils.py` - Date/hour calculations (working days, overlap detection)
- `constants.py` - Leave type enums, status enums
- `serializers.py` - Leave data validation
- `views/requests/` - Leave request CRUD, approve/reject, cancel
- `views/balances.py` - Balance endpoints
- `views/categories.py` - Category endpoints
- `views/holidays.py` - Public holiday management
- `views/calendar.py` - Team calendar view
- `views/export.py` - CSV export for approved leaves
- `views/file_upload.py` - Attachment handling
- `views/business_trips.py` - Business trip CRUD
- `management/commands/seed_data.py` - Demo data generation
- `management/commands/recalculate_exempt_vacation.py` - Annual balance recalculation

**Key Features:**
- Hours-based leave tracking (LeaveBalance uses Decimal)
- Four leave types: EXEMPT_VACATION, NON_EXEMPT_VACATION, EXEMPT_SICK, NON_EXEMPT_SICK
- Dynamic EXEMPT_VACATION allocation by years of service (YoS tiers: Y1 prorate, 2-5: 80h, 6-10: 120h, 11-15: 160h, 16+: 200h)
- Working day calculation (Mon-Fri, 8h/day default)
- Holiday scoping: global → entity → location priority
- Overlap detection for leaves and business trips
- 24-hour rejection rule for approved leaves
- Atomic approval/rejection with balance restoration
- Approver-relationship-based permissions (no role bypass)

### 4. core/
**Purpose:** Notifications and audit logging.

**Key Files:**
- `models.py` - Notification, AuditLog models
- `views.py` - Notification list, mark read endpoints
- `services/notification_service.py` - Notification creation
- `tests/` - Unit tests

**Key Features:**
- In-app notifications for leave requests/approvals
- Audit trail of all actions (user, timestamp, action type, details)
- Unread count tracking

### 5. backend/
**Purpose:** Django project configuration.

**Key Files:**
- `settings.py` - Django settings (DEBUG, DATABASE, INSTALLED_APPS, MIDDLEWARE, JWT config, CORS, DRF)
- `urls.py` - Root URL routing
- `wsgi.py` - Production WSGI entry point
- `asgi.py` - ASGI configuration

---

## Frontend Architecture

**Framework:** React 19 + TypeScript (Vite)
**UI Library:** Ant Design 6.2.2
**HTTP Client:** Axios
**Routing:** React Router 7
**State Management:** AuthContext (no Redux)
**Date Library:** Dayjs
**Charts:** Recharts

### Directory Structure

```
frontend/src/
├── api/                    # API client files (8 files)
│   ├── authApi.js         # Auth endpoints
│   ├── userApi.js         # User management (createUser function)
│   ├── dashboardApi.js    # Dashboard data
│   ├── notificationApi.js # Notifications
│   ├── businessTripApi.js # Business trips
│   ├── organizationApi.js # Entity/Location/Department cascading
│   ├── entityApi.js       # Entity CRUD operations
│   └── http.js            # Axios instance + interceptors
├── auth/                  # Authentication
│   └── authContext.jsx    # Global user state
├── components/            # Reusable components (8 main)
│   ├── header.jsx         # Top bar + notifications
│   ├── sidebar.jsx        # Role-aware navigation
│   ├── NewLeaveRequestModal.jsx # 2-step form
│   ├── NewBusinessTripModal.jsx
│   ├── CreateEventModal.jsx
│   ├── AddUserModal.jsx    # HR/Admin add user modal with cascading dropdowns
│   ├── EntityManagement.jsx # Entity table with CRUD actions
│   └── EntityForm.jsx      # Modal form for create/edit entities
├── hooks/                 # Custom React hooks
│   └── use-notifications.js # Polling every 30s
├── layouts/               # Page layouts
│   ├── mainLayout.jsx     # Authenticated layout
│   └── authLayout.jsx     # Login/signup layout
├── pages/                 # 9 main pages
│   ├── Dashboard.jsx
│   ├── Calendar.jsx
│   ├── ManagerTicket.jsx
│   ├── Profile.jsx
│   ├── Settings.jsx
│   ├── BusinessTripHistory.jsx
│   ├── Login.jsx
│   ├── Signup.jsx
│   └── ChangePassword.jsx
├── App.tsx               # Route definitions
└── index.css             # Global styles
```

### Key Pages

- **Dashboard:** Overview cards (leave balance, upcoming requests, pending approvals)
- **Calendar:** Entity-level team calendar with color-coded leaves, drag-to-create, bidirectional approser visibility
- **ManagerTicket:** Manager approval/rejection form
- **Profile:** User info and balance cards
- **Settings:** General settings and preferences, Users and Entities tabs
  - HR/Admin "Add New User" modal with cascading dropdowns
  - HR/Admin Entity management (create, edit, soft-delete with cascade warning)
- **BusinessTripHistory:** Business trip list and details
- **Login/Signup:** Authentication forms
- **ChangePassword:** Password update form

---

## Database Schema (Key Tables)

| Table | Purpose |
|-------|---------|
| users_user | Custom user (email, roles, join_date, approver_id, onboarding flags) |
| organizations_entity | Companies/subsidiaries |
| organizations_location | Offices with timezone |
| organizations_department | Organizational units |
| organizations_departmentmanager | Manager assignments (M2M) |
| leaves_leavecategory | Leave types (Sick, Vacation, etc.) |
| leaves_leavebalance | Annual allocation tracking (Decimal hours) |
| leaves_leaverequest | Individual requests (status, dates, hours, attachments) |
| leaves_publicholiday | Non-working days (scoped: global/entity/location) |
| leaves_businesstrip | Business trip records |
| core_notification | In-app alerts |
| core_auditlog | Complete action history |

---

## API Endpoints (Summary)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/auth/register/ | POST | User registration |
| /api/v1/auth/login/ | POST | JWT login |
| /api/v1/auth/refresh/ | POST | Token refresh |
| /api/v1/auth/logout/ | POST | Token blacklist |
| /api/v1/auth/me/ | GET | Current user info |
| /api/v1/auth/users/ | POST | HR/Admin create user |
| /api/v1/leaves/requests/ | GET/POST | Leave requests CRUD |
| /api/v1/leaves/requests/my/ | GET | User's requests |
| /api/v1/leaves/requests/{id}/approve/ | PUT | Manager approve |
| /api/v1/leaves/requests/{id}/reject/ | PUT | Manager reject |
| /api/v1/leaves/requests/{id}/cancel/ | PUT | User cancel |
| /api/v1/leaves/balance/my/ | GET | User's balance |
| /api/v1/leaves/categories/ | GET | Leave types |
| /api/v1/leaves/calendar/ | GET | Team calendar |
| /api/v1/organizations/entities/ | GET | Entity list |
| /api/v1/organizations/entities/create/ | POST | Create entity (HR/Admin) |
| /api/v1/organizations/entities/{id}/update/ | PATCH | Update entity (HR/Admin) |
| /api/v1/organizations/entities/{id}/soft-delete/ | PATCH | Soft-delete entity with cascade (HR/Admin) |
| /api/v1/organizations/entities/{id}/delete-impact/ | GET | Get deletion impact counts |
| /api/v1/organizations/locations/ | GET | Location list |
| /api/v1/organizations/departments/ | GET | Department list |
| /api/v1/notifications/ | GET | Notifications list |

*Full endpoint documentation available via Swagger UI at `/api/docs/` (DEBUG mode)*

---

## Key Patterns

### Decimal for Hours
All hour values use `Decimal` type for precision:
```python
# In models
balance = models.DecimalField(max_digits=5, decimal_places=2)

# In validation
Decimal('8.0') represents 8 hours
```

### User Onboarding
User must have entity + location + department set before accessing features:
```python
@property
def has_completed_onboarding(self):
    return all([self.entity, self.location, self.department])
```

### Approver Relationship
Users have optional self-referential approver:
```python
approver = models.ForeignKey(
    'self', null=True, blank=True, on_delete=models.SET_NULL
)
```

### Leave Balance Types
```python
BALANCE_TYPES = {
    'EXEMPT_VACATION': 'Exempt Vacation',
    'NON_EXEMPT_VACATION': 'Non-Exempt Vacation',
    'EXEMPT_SICK': 'Exempt Sick',
    'NON_EXEMPT_SICK': 'Non-Exempt Sick'
}
```

### Years of Service Calculation
```python
# YoS = floor((reference_date - join_date).days / 365.25) + 1
# Reference date = Jan 1 of balance year, NOT current date
# Edge case: 365 days = YoS 1 (not 2) due to 365.25 divisor
```

---

## Testing

**Backend:** pytest with fixtures, mocking, and transaction tests
**Frontend:** (Limited coverage)

```bash
# Run backend tests
docker compose exec -T backend python -m pytest --verbosity=2

# Run with coverage
docker compose exec -T backend python -m pytest --cov
```

**Known Test Issues (pre-existing):**
- 32 test failures unrelated to new code
- Entity model field mismatch (`name` vs `entity_name`)
- Missing audit logs endpoint
- Registration API requires entity/location/department UUIDs

---

## Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| db | postgres:16-alpine | 5432 | PostgreSQL database |
| backend | Custom Python 3.12 | 8000 | Django + Gunicorn |
| frontend | Node.js | 5173 | Vite dev server |

**Startup Flow:**
1. Wait for db
2. Run migrations
3. Execute seed_data command
4. Start Gunicorn (4 workers, 4 threads)

---

## Dependencies

**Backend (Python):**
- Django 6.0.1, djangorestframework 3.14.0, djangorestframework-simplejwt 5.3.0
- django-cors-headers 4.3.0, drf-spectacular 0.27.0
- django-import-export 4.0.0, openpyxl 3.1.0
- psycopg2-binary 2.9.0, python-dotenv 1.0.0
- gunicorn 21.0.0

**Frontend (Node.js):**
- react 19.2, react-router-dom 7.x
- axios (latest), dayjs (latest)
- ant-design 6.2.2, recharts (latest)
- vite 7.2.4, typescript 5.9

---

## Configuration

**Environment Variables:**
- DEBUG, SECRET_KEY, DATABASE_URL
- JWT_SECRET_KEY, JWT_ACCESS_TOKEN_LIFETIME, JWT_REFRESH_TOKEN_LIFETIME
- ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS
- VITE_API_BASE_URL (frontend)

**Key Settings:**
- Rate limiting: anon 20/min, user 60/min
- HTTPS only in production
- HSTS 1-year preload
- Secure cookies, CSRF protection

---

## Management Commands

**seed_data:** Creates demo entity, locations, departments, categories, holidays, and 4 users
- Flags: None (auto-generated based on environment)
- Usage: `python manage.py seed_data`

**recalculate_exempt_vacation:** Yearly balance recalculation
- Flags: `--year` (specify year), `--dry-run` (preview changes), `--all-types` (recalculate all types)
- Usage: `python manage.py recalculate_exempt_vacation --year 2025 --dry-run`

---

## Performance Considerations

- Gunicorn: 4 workers × 4 threads (16 concurrent requests default)
- Notification polling: 30-second intervals (can be optimized with WebSockets)
- Database indexes on frequently queried fields (user_id, dates, status)
- Decimal precision for financial accuracy

---

## Security Features

- JWT token rotation with blacklist
- CORS whitelisting (dev: all, prod: HTTPS only)
- Input validation on all endpoints
- Password requirements on first login
- Rate limiting on auth endpoints
- Approver-relationship-based permissions (can't bypass with roles)
- Secure session handling

---

## Known Limitations & Future Improvements

- No email notifications (in-app only)
- Notification polling instead of WebSocket
- Limited frontend test coverage
- No SMS notifications
- No calendar export (ICS)
- No bulk leave request approval
- Limited analytics dashboard
- No API rate limiting per user

---

*For detailed information, see individual documentation files in `/docs`.*
