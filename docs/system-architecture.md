# System Architecture

**Last Updated:** 2026-02-07 | **Version:** 1.1.0

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Layer                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Web Browser (React 19 + TypeScript)                       │ │
│  │  - Dashboard, Calendar, Leave Request Forms                │ │
│  │  - Manager Approval UI                                     │ │
│  │  - Notifications (polling every 30s)                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/Axios
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway / Load Balancer                 │
│  (Docker Compose in dev, Nginx/HAProxy in production)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                       Application Layer                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Django REST Framework (Port 8000)                         │ │
│  │  - Authentication (JWT with refresh tokens)                │ │
│  │  - Leave Management APIs                                   │ │
│  │  - User & Organization Management                          │ │
│  │  - Notification & Audit Services                           │ │
│  │  Gunicorn: 4 workers × 4 threads                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ TCP
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL 16 (Port 5432)                                 │ │
│  │  - User & Organizational Data                              │ │
│  │  - Leave Requests & Balances                               │ │
│  │  - Audit Logs & Notifications                              │ │
│  │  - Business Trips & Public Holidays                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Architecture

### 1. Frontend Layer (React 19 SPA)

**Technology Stack:**
- Framework: React 19 + TypeScript
- Build: Vite 7.2.4
- UI: Ant Design 6.2.2
- HTTP: Axios
- Routing: React Router 7
- State: AuthContext (no Redux)
- Date/Time: Dayjs

**Component Structure:**

```
App.tsx (Routes)
├── AuthContext Provider
├── Route: /login → Login Page
├── Route: /signup → Signup Page
├── Route: / → MainLayout
│   ├── Header (Notifications, User Menu)
│   ├── Sidebar (Navigation)
│   └── Content
│       ├── /dashboard → Dashboard (overview cards, pending approvals)
│       ├── /calendar → Calendar (entity-level visibility + drag-to-create)
│       ├── /my-leaves → My Requests (list with status)
│       ├── /manager-ticket → Approval Form (for managers)
│       ├── /business-trips → Trip History
│       ├── /profile → User Profile (info, balances)
│       ├── /settings → Settings
│       └── /change-password → Password Change
```

**Key Features:**
- JWT authentication with automatic token refresh
- Notification polling every 30 seconds
- Role-aware navigation (sidebar changes per role)
- Modal forms for new requests (2-step wizard)
- Real-time balance calculations
- Drag-and-drop calendar event creation
- Entity-level calendar visibility (all employees in same entity)
- Bidirectional approver-subordinate visibility

**API Integration:**
```
Axios Instance (http.js)
├── Request Interceptor: Attach JWT token
├── Response Interceptor: Handle 401, refresh token
└── 10-second timeout per request

API Clients
├── authApi.js (register, login, refresh, logout)
├── userApi.js (profile, balance, my-subordinates)
├── leaveApi.js (requests CRUD, approve, reject, calendar)
├── notificationApi.js (list, mark read)
└── businessTripApi.js (CRUD, cancel)
```

---

### 2. Application Layer (Django REST Framework)

**Technology Stack:**
- Framework: Django 6.0.1
- REST: djangorestframework 3.14.0
- Authentication: SimpleJWT 5.3.0
- Database ORM: Django ORM (PostgreSQL backend)
- API Documentation: drf-spectacular (Swagger/ReDoc)
- Server: Gunicorn (4 workers, 4 threads)

**Project Structure:**

```
backend/
└── settings.py          # Django configuration
    urls.py            # Root URL dispatcher
    asgi.py            # ASGI config
    wsgi.py            # WSGI config (production)

users/                   # Authentication & User Management
├── models.py           # Custom User (email auth, roles, approver FK)
├── views/              # Auth & profile endpoints
│   ├── __init__.py
│   ├── auth.py         # register, login, refresh, logout, me
│   ├── profile.py      # profile GET/PUT
│   ├── management.py   # HR/Admin user CRUD
│   └── balance.py      # Balance adjustments
├── serializers/
│   ├── serializers.py  # User, Auth serializers
│   └── utils.py        # Validators
├── permissions.py      # Role checks, approver checks
├── signals.py          # Create default LeaveBalance on user creation
└── tests/              # Unit tests

organizations/          # Entity/Location/Department Hierarchy
├── models.py          # Entity, Location, Department, DepartmentManager
├── views.py           # CRUD endpoints
├── admin.py           # Django admin
└── tests/

leaves/                # Leave Management Core
├── models.py          # LeaveRequest, LeaveBalance, PublicHoliday, etc.
├── views/
│   ├── __init__.py
│   ├── requests/      # Leave request CRUD
│   │   ├── __init__.py
│   │   ├── create.py
│   │   ├── retrieve.py
│   │   ├── update.py
│   │   └── approve_reject.py
│   ├── balances.py    # Balance endpoints
│   ├── categories.py  # Leave type endpoints
│   ├── holidays.py    # Public holiday management
│   ├── calendar.py    # Team calendar view
│   ├── export.py      # CSV export
│   ├── file_upload.py # Attachment handling
│   └── business_trips.py
├── serializers.py     # Leave data serialization
├── services.py        # LeaveApprovalService (atomic approve/reject)
├── utils.py           # Calculations (working days, overlap)
├── constants.py       # Enums, status choices
├── management/commands/
│   ├── seed_data.py        # Demo data generation
│   └── recalculate_exempt_vacation.py
└── tests/

core/                  # Notifications & Audit Logs
├── models.py         # Notification, AuditLog
├── views.py          # Notification endpoints
├── services/
│   └── notification_service.py  # Creation logic
└── tests/
```

**API Routing:**

```
/api/v1/
├── auth/
│   ├── register/ (POST)
│   ├── login/ (POST)
│   ├── refresh/ (POST)
│   ├── logout/ (POST)
│   ├── me/ (GET)
│   ├── change-password/ (POST)
│   └── onboarding/ (PUT)
│
├── users/
│   ├── (GET - list, HR/Admin)
│   ├── create/ (POST - HR/Admin)
│   ├── {id}/ (GET, PUT, DELETE)
│   ├── {id}/balance/adjust/ (PUT - HR/Admin)
│   ├── {id}/setup/ (PUT - role/dept assignment)
│   └── my-subordinates/ (GET - managers)
│
├── leaves/
│   ├── requests/
│   │   ├── (GET, POST - list/create)
│   │   ├── my/ (GET - user's requests)
│   │   ├── {id}/ (GET, PUT, DELETE)
│   │   ├── {id}/approve/ (PUT - manager)
│   │   ├── {id}/reject/ (PUT - manager)
│   │   └── {id}/cancel/ (PUT - user)
│   ├── balance/my/ (GET)
│   ├── balance/adjust/ (PUT - HR)
│   ├── categories/ (GET)
│   ├── calendar/ (GET - team calendar)
│   ├── holidays/ (GET, POST, PUT, DELETE)
│   ├── export/ (POST - CSV)
│   └── business-trips/
│       ├── (GET, POST)
│       ├── {id}/ (GET, PUT, DELETE)
│       └── {id}/cancel/ (PUT)
│
├── organizations/
│   ├── entities/ (GET, POST, PUT, DELETE)
│   ├── locations/ (GET, POST, PUT, DELETE)
│   ├── departments/ (GET, POST, PUT, DELETE)
│   ├── managers/ (GET - filter by dept)
│   └── audit-logs/ (GET - future)
│
└── notifications/
    ├── (GET - list)
    ├── {id}/ (PUT - mark read)
    ├── mark-all-read/ (PUT)
    └── unread-count/ (GET)
```

**Authentication Flow:**

```
1. User Registration (POST /auth/register/)
   ├── Email + Password validation
   ├── Create User + default LeaveBalance records
   └── Return success

2. User Login (POST /auth/login/)
   ├── Validate email + password
   ├── Generate access_token (1 hour TTL)
   ├── Generate refresh_token (7 days TTL)
   └── Return both tokens + user data

3. Token Refresh (POST /auth/refresh/)
   ├── Validate refresh_token (not blacklisted)
   ├── Generate new access_token
   └── Return new access_token

4. Logout (POST /auth/logout/)
   ├── Blacklist refresh_token
   └── Return success

5. Subsequent Requests
   ├── Include Authorization: Bearer {access_token}
   ├── JWT middleware validates token
   ├── If expired: client calls refresh endpoint
   └── Retry original request with new token
```

**Calendar Visibility Model:**

```
Entity-Level Filtering:
├── Primary Scope: All active users in same entity
├── Secondary Scope: User's direct subordinates (approver relationship)
└── Tertiary Scope: User's assigned approver (bidirectional visibility)

Calendar Query (TeamCalendarView):
├── Q(entity=user.entity)           # Same entity
├── Q(approver=user)                # Direct subordinates
├── Q(id=user.approver.pk)          # User's approver
└── Combined with OR, distinct()

Use Cases:
├── Employees: See all entity members + their manager
├── Managers: See entity + their subordinates + their own manager
├── HR/Admin: Same as employees (entity-scoped)
└── Cross-entity approval: Managers can approve cross-entity subordinates
```

**Holiday Scoping:**

```
Priority Order: Global → Entity → Location

Query Logic (cascading):
├── Base: Q(is_active=True)
├── Global: Q(entity__isnull=True)
├── Entity: Q(entity=user.entity)
├── Location: Q(location=user.location)
└── Applied with OR logic (most specific wins)

Fields:
├── holiday_name (NOT name - fixed field reference)
├── start_date, end_date (supports multi-day holidays)
└── entity, location (nullable FKs)
```

**Performance Considerations for Large Entities:**

```
Entities > 500 users:
├── Consider pagination for team member list
├── Add database index on (entity_id, is_active)
├── Cache holiday queries (scoped by location)
└── Use select_related() for user FK queries

Current optimizations:
├── distinct() to prevent duplicates
├── filter(is_active=True)
└── select_related('leave_category', 'user')
```

**Leave Approval Flow:**

```
1. User submits LeaveRequest
   ├── Validate dates, hours, balance
   ├── Check overlaps with existing requests
   ├── Status: PENDING
   ├── Create Notification for approver
   └── Create AuditLog entry

2. Manager approves (atomic transaction)
   ├── Lock LeaveRequest row
   ├── Check approver has permission (relationship)
   ├── Deduct hours from LeaveBalance
   ├── Set status: APPROVED
   ├── Create Notification for user
   ├── Create AuditLog entry
   └── Unlock row

3. Manager rejects (within 24 hours if already approved)
   ├── Lock LeaveRequest row
   ├── If APPROVED: check 24-hour rule
   ├── If valid: restore hours to LeaveBalance
   ├── Set status: REJECTED
   ├── Store rejection reason
   ├── Create Notification for user
   └── Create AuditLog entry

4. User cancels
   ├── If status: APPROVED
   │   ├── Restore hours to LeaveBalance
   │   └── Notify manager
   ├── If status: PENDING
   │   └── Simply cancel
   ├── Set status: CANCELLED
   └── Create AuditLog entry
```

**Key Services:**

```python
LeaveApprovalService
├── approve(leave, approver) → atomic deduction + status change
├── reject(leave, approver, reason) → atomic restoration + reason storage
├── get_pending_requests_for_manager(user) → cross-entity approval support
├── get_approval_history_for_manager(user) → historical approvals
├── validate_approver_permission(leave, approver) → relationship check
└── get_request_detail_with_conflicts(leave) → balance + team conflicts

CalculationService
├── calculate_working_days(start, end, exclude_holidays)
├── calculate_exempt_vacation_hours(join_date, ref_date)
├── detect_overlapping_leaves(user, start, end)
└── calculate_hours_from_days(days, hours_per_day=8)

NotificationService
├── create_leave_notification(leave, action, recipient)
├── create_balance_notification(user, action, old_balance, new_balance)
└── mark_as_read(notification_id)
```

---

### 3. Data Layer (PostgreSQL 16)

**Database Schema Overview:**

**Users:**
```sql
users_user
├── id (PK)
├── email (UNIQUE, indexed)
├── password_hash
├── first_name, last_name
├── role (EMPLOYEE, MANAGER, HR, ADMIN)
├── approver_id (FK to self, nullable)
├── join_date (DateField, for YoS calculation)
├── entity_id, location_id, department_id (FKs to org tables)
├── is_active, is_staff
├── has_completed_onboarding (computed property)
├── created_at, updated_at
└── indexed: email, approver_id, entity_id, department_id
```

**Organizations:**
```sql
organizations_entity
├── id (PK)
├── entity_name (indexed)
└── created_at, updated_at

organizations_location
├── id (PK)
├── entity_id (FK to Entity)
├── location_name (indexed)
├── timezone (CharField, 33 options)
└── created_at, updated_at

organizations_department
├── id (PK)
├── location_id (FK to Location)
├── entity_id (FK to Entity, for scoping)
├── department_name (indexed)
└── created_at, updated_at

organizations_departmentmanager
├── id (PK)
├── department_id (FK to Department)
├── user_id (FK to User)
├── UNIQUE(department_id, user_id)
└── created_at
```

**Leaves:**
```sql
leaves_leavecategory
├── id (PK)
├── name (VACATION, SICK, PERSONAL, etc.)
├── description
├── requires_approval (boolean)
└── created_at, updated_at

leaves_leavebalance
├── id (PK)
├── user_id (FK, indexed)
├── category_id (FK to LeaveCategory)
├── balance_year (IntegerField, e.g., 2026)
├── hours (DecimalField max_digits=5, decimal_places=2)
├── UNIQUE(user_id, category_id, balance_year)
└── created_at, updated_at

leaves_leaverequest
├── id (PK)
├── user_id (FK, indexed)
├── category_id (FK to LeaveCategory)
├── start_date (DateField, indexed)
├── end_date (DateField)
├── hours (DecimalField)
├── status (PENDING, APPROVED, REJECTED, CANCELLED)
├── approver_id (FK to User, nullable)
├── rejection_reason (TextField, nullable)
├── notes (TextField)
├── attachment_url (CharField, nullable)
├── created_at, updated_at
└── indexed: user_id, status, start_date, approver_id

leaves_publicholiday
├── id (PK)
├── name (holiday name)
├── date (DateField, indexed)
├── scope (GLOBAL, ENTITY, LOCATION)
├── entity_id, location_id (FK, based on scope)
└── created_at, updated_at

leaves_businesstrip
├── id (PK)
├── user_id (FK, indexed)
├── start_date (DateField)
├── end_date (DateField)
├── notes (TextField)
├── status (ACTIVE, CANCELLED)
└── created_at, updated_at
```

**Audit & Notifications:**
```sql
core_auditlog
├── id (PK)
├── user_id (FK to User)
├── action (SUBMIT, APPROVE, REJECT, CANCEL, etc.)
├── content_type_id (FK to ContentType, for generic relations)
├── object_id (ID of affected object)
├── changes_json (JSONField with before/after)
├── reason (TextField, optional)
├── created_at (indexed)
└── indexed: user_id, created_at, action

core_notification
├── id (PK)
├── user_id (FK to User, indexed)
├── notification_type (LEAVE_SUBMITTED, APPROVED, REJECTED, etc.)
├── title, message
├── is_read (BooleanField)
├── related_object_id (ID of related LeaveRequest, etc.)
├── created_at (indexed)
└── updated_at
```

**Indexing Strategy:**
- Foreign keys: Automatic indexes
- Status fields: Multi-column indexes (user_id, status)
- Date ranges: B-tree indexes on start_date, end_date
- Lookups: Indexed on frequently filtered fields (email, category, dates)

**Performance Considerations:**
- LeaveBalance accessed per user/category/year (indexed)
- LeaveRequest queried by user + date range (indexed)
- PublicHoliday scoped by location (indexed)
- AuditLog queries filtered by user + action + date (indexed)

---

## Data Management Patterns

### Soft-Delete Cascade Pattern

**Use Case:** Entity deactivation cascades to Locations and Departments

**Implementation:**
- Service function: `soft_delete_entity_cascade(entity_id)`
- Transaction-wrapped operation ensures atomicity
- Sets `is_active=False` on Entity + all related Locations + Departments
- Pre-delete impact check: `get_entity_delete_impact(entity_id)`

**Frontend Flow:**
1. User clicks Delete → API call to get impact counts
2. Warning modal shows: "This will deactivate X Locations and Y Departments"
3. User confirms → API call to soft-delete with cascade
4. Success message shows deactivated counts
5. Table refreshes to show inactive status

**Benefits:**
- Preserves historical data (no hard delete)
- Atomic operation prevents partial updates
- User awareness of impact before deletion
- Reversible (can reactivate if needed)

**Backend Pattern:**
```python
@transaction.atomic
def soft_delete_entity_cascade(entity_id):
    entity = Entity.objects.get(id=entity_id, is_active=True)
    # Cascade to locations
    location_count = entity.locations.update(is_active=False)
    # Cascade to departments
    department_count = entity.departments.update(is_active=False)
    # Deactivate entity
    entity.is_active = False
    entity.save()
    return location_count, department_count
```

---

## Data Flow Diagrams

### Leave Request Submission Flow

```
User Form Submit
    ↓
Frontend Validation
    ├─ Check date format
    ├─ Check hours > 0
    └─ Check dates logical
    ↓
POST /api/v1/leaves/requests/
    ↓
Backend Serializer Validation
    ├─ Email exists
    ├─ Dates are valid
    ├─ Hours > 0 and <= 16
    └─ Hours matches working days
    ↓
Backend Service Logic
    ├─ Check user has completed onboarding
    ├─ Calculate working days
    ├─ Exclude weekends, holidays
    ├─ Check balance availability
    └─ Detect overlaps with existing requests
    ↓
Database Transaction BEGIN
    ├─ Create LeaveRequest (status: PENDING)
    ├─ Create Notification for approver
    └─ Create AuditLog entry
    ↓
Database Transaction COMMIT
    ↓
Return 201 Created + request data
    ↓
Frontend Shows Confirmation
```

### Leave Approval Flow

```
Manager Views Pending Requests
    ↓
GET /api/v1/leaves/requests/?status=PENDING
    ↓
Backend Filters by manager's team
    ├─ Get manager's departments
    └─ Filter requests by those departments
    ↓
Display Approval Form with Request Details
    ↓
Manager Clicks "Approve" (or "Reject")
    ↓
PUT /api/v1/leaves/requests/{id}/approve/
    ↓
Backend Validation
    ├─ Verify approver-user relationship
    ├─ Check request status is PENDING
    └─ Check balance sufficiency
    ↓
Database Transaction BEGIN
    ├─ Lock LeaveRequest row
    ├─ SELECT LeaveBalance FOR UPDATE
    ├─ Deduct hours: balance.hours -= leave.hours
    ├─ UPDATE LeaveBalance
    ├─ UPDATE LeaveRequest (status: APPROVED, approver_id)
    ├─ Create Notification (to employee)
    └─ Create AuditLog entry
    ↓
Database Transaction COMMIT
    ↓
Return 200 OK + updated request
    ↓
Frontend Updates UI (approval successful)
```

### Notification Polling Flow

```
Frontend Component Mounts
    ↓
useEffect → setInterval(pollNotifications, 30000)
    ↓
Every 30 Seconds:
    ├─ GET /api/v1/notifications/unread-count/
    ├─ Update notification badge
    └─ If user navigates to notifications page:
        └─ GET /api/v1/notifications/?limit=20
            └─ Display in list with "Mark as Read" option
    ↓
User Clicks "Mark as Read"
    ↓
PUT /api/v1/notifications/{id}/
    ├─ Set is_read: true
    └─ Update updated_at
    ↓
Frontend Removes from unread count
```

---

## Scalability & Future Architecture

### Current State (Single Instance)
```
Load Balancer
    ↓
Django (Gunicorn: 4 workers × 4 threads)
    ↓
PostgreSQL Single Instance
```

### Future State (Scalable)
```
Load Balancer (Nginx/HAProxy)
    ├─ Django Instance 1 (Gunicorn)
    ├─ Django Instance 2 (Gunicorn)
    └─ Django Instance N (Gunicorn)
    ↓
Redis Cache Layer (Token blacklist, session store)
    ↓
PostgreSQL Primary (with replication)
    ├─ Read Replicas (reporting queries)
    └─ Backup
    ↓
Elasticsearch (future - audit log search, analytics)
```

### Optimization Opportunities
1. **Caching:** Redis for token blacklist, user data, holiday lists
2. **Query Optimization:** Add database indexes, reduce N+1 queries
3. **Async Tasks:** Celery for notifications, exports, recalculations
4. **Real-time Updates:** WebSocket + Django Channels (replace polling)
5. **Search:** Elasticsearch for audit logs, leave history
6. **CDN:** CloudFront/Cloudflare for static assets (frontend build)

---

## Security Architecture

### Authentication & Authorization

```
User Login
    ├─ Hash password with Django's PBKDF2 + salt
    ├─ Verify against stored hash
    ├─ Generate JWT:
    │   ├─ access_token (1 hour, contains user_id, role, exp)
    │   ├─ refresh_token (7 days, stored in database)
    │   └─ Both signed with SECRET_KEY
    └─ Return to frontend

Subsequent Requests
    ├─ JWT in Authorization header
    ├─ Middleware decodes + validates signature
    ├─ Check expiration
    └─ Set request.user = decoded payload

Token Refresh
    ├─ Exchange refresh_token for new access_token
    ├─ Check refresh_token not blacklisted
    └─ Generate new access_token

Logout
    ├─ Add refresh_token to blacklist (database table)
    ├─ Frontend removes tokens from localStorage
    └─ Subsequent requests with old tokens fail

Permission Checks
    ├─ Role-based: @permission_classes([IsAuthenticated, IsManager])
    ├─ Approver-based: Verify request.user.id == leave.approver_id
    └─ Scoping: Filter by user's entity/department
```

### Data Security

```
Secrets Management
├─ SECRET_KEY: Django setting, stored in environment
├─ JWT_SECRET_KEY: Separate from SECRET_KEY
├─ DB_PASSWORD: Environment variable, never in code
└─ CORS_ALLOWED_ORIGINS: Whitelist (dev: *, prod: HTTPS only)

Sensitive Data
├─ Passwords: Hashed with PBKDF2
├─ JWT Tokens: Signed, expiring
├─ Email Addresses: NOT hashed (needed for login)
├─ Attachments: Stored on disk/S3 with access control
└─ Audit Logs: Preserved for 7 years (GDPR)

HTTPS/TLS
├─ Production: HTTPS only (HSTS header)
├─ Cookies: Secure flag, HttpOnly, SameSite=Strict
├─ API: No sensitive data in URL, use POST body
└─ Development: HTTP allowed locally
```

### Rate Limiting & DDoS Protection

```
Anonymous Users
├─ 20 requests/minute on auth endpoints
└─ 50 requests/minute on other endpoints

Authenticated Users
├─ 60 requests/minute on all endpoints
└─ 10 requests/minute on expensive operations (export, recalculate)

Brute Force Protection
├─ Lock account after 5 failed login attempts
├─ 15-minute cooldown
└─ Log suspicious activity
```

---

## Deployment Architecture

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    ports: [5432:5432]
    environment:
      POSTGRES_DB: leave_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes: [pgdata:/var/lib/postgresql/data]

  backend:
    build: ./Dockerfile.backend
    ports: [8000:8000]
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/leave_db
      DEBUG: 'True'
      SECRET_KEY: dev-key
      CORS_ALLOWED_ORIGINS: http://localhost:5173
    depends_on: [db]
    command: >
      sh -c "python manage.py migrate &&
             python manage.py seed_data &&
             gunicorn backend.wsgi:application --bind 0.0.0.0:8000"

  frontend:
    build: ./frontend
    ports: [5173:5173]
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
    depends_on: [backend]
    command: npm run dev

volumes:
  pgdata:
```

### Production Deployment (Future)

```
Cloud Provider (AWS/GCP/Azure)
├─ Load Balancer (ALB/NLB)
├─ ECR/Docker Registry
├─ RDS PostgreSQL (managed, backups, replicas)
├─ ElastiCache Redis (optional)
├─ ECS/Kubernetes for container orchestration
├─ CloudFront CDN for static assets
├─ S3 for file uploads/backups
└─ CloudWatch/Monitoring for alerts
```

---

## Integration Points

### External Integrations (Future)

```
SMTP Server (Email Notifications)
├─ Django signals trigger email tasks
└─ Format: HTML templates with request details

HRIS/ERP System
├─ REST API endpoints for user sync
├─ Entity/location/department sync
└─ Join date updates for YoS recalculation

Single Sign-On (SAML 2.0 / OAuth 2.0)
├─ Replace local authentication
├─ Map SAML attributes to Django user
└─ Auto-create users on first login

Calendar Systems (Google Calendar, Outlook)
├─ Export approved leaves as calendar events
├─ Sync public holidays
└─ Accept calendar invites for time off
```

---

## Monitoring & Observability

### Logging Strategy

```
Application Logs
├─ Django logger (DEBUG, INFO, WARNING, ERROR, CRITICAL)
├─ Log level: DEBUG in dev, INFO in production
├─ Output: stdout (Docker captures), rotated files
└─ Fields: timestamp, level, logger, message, exc_info

Audit Logs (Business Events)
├─ Model: core.AuditLog
├─ Events: SUBMIT, APPROVE, REJECT, CANCEL, ADJUST_BALANCE
├─ Fields: user_id, action, timestamp, changes, reason
└─ Retention: 7 years (GDPR)

Error Tracking (Future)
├─ Sentry integration
├─ Track exceptions, performance, releases
└─ Alert on critical errors
```

### Metrics to Monitor

```
System Metrics
├─ CPU usage (target: < 70%)
├─ Memory usage (target: < 80%)
├─ Disk I/O (target: < 50%)
└─ Database connection count (target: < max_connections/2)

Application Metrics
├─ Request rate (req/s)
├─ Response time (p50, p95, p99)
├─ Error rate (4xx, 5xx percentage)
├─ Database query time
└─ Cache hit rate (if implemented)

Business Metrics
├─ Daily active users
├─ Leave requests submitted/day
├─ Approval turnaround time
├─ System uptime (target: 99.5%)
└─ User satisfaction (NPS)
```

---

*For API endpoint details, see [codebase-summary.md](./codebase-summary.md). For code patterns, see [code-standards.md](./code-standards/index.md).*
