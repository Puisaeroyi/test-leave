# System Architecture

**Project:** Leave Management System
**Version:** 1.0.0
**Last Updated:** 2026-01-27

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser Client                          │
│                   (React 19 + TypeScript)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / Frontend                        │
│                    (Vite Dev Server / Nginx)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Django REST API (v1)                          │
│         (Gunicorn + Django 6.0.1 + DRF + SimpleJWT)            │
│                                                                 │
│  ┌────────┐  ┌────────────┐  ┌──────┐  ┌──────┐              │
│  │ users  │  │organizations│  │leaves│  │core  │              │
│  │  app   │  │    app      │  │ app  │  │ app  │              │
│  └────────┘  └────────────┘  └──────┘  └──────┘              │
└────────────────────────────┬────────────────────────────────────┘
                             │ TCP 5432
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               PostgreSQL 16 Database                            │
│                (users, organizations, leaves,                   │
│                notifications, audit logs)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layered Architecture

### 1. Presentation Layer (Frontend)

**Technology:** React 19 + TypeScript 5.9 + Vite 7.2

**Components:**
- **Pages:** LeaveRequestPage, CalendarPage, DashboardPage, AdminDashboard, etc.
- **Components:** Layout, Sidebar, Header, Forms, Cards, Modals
- **Hooks:** useAuth, useLeaveBalance, useNotifications
- **API Client:** Axios with JWT interceptor

**Responsibilities:**
- Render UI components
- Manage component state with useState/useContext
- Handle user interactions
- Call backend APIs via axios
- Display errors and loading states
- Manage authentication context

**Communication:**
- REST calls to `/api/v1/*` endpoints
- JWT tokens in Authorization header
- Axios auto-refresh on 401 response

---

### 2. API Layer (Django REST Framework)

**Technology:** Django 6.0.1 + DRF + SimpleJWT

**Components:**
- **ViewSets:** CRUD + custom actions for each app
- **Serializers:** Data validation and transformation
- **Permissions:** Role-based access control (IsManagerOrAdmin, IsHROrAdmin, etc.)
- **Routers:** Automatic URL generation from ViewSets
- **Middleware:** JWT token validation, CORS handling

**Endpoints Structure:**
```
/api/v1/
├── auth/
│   ├── register/              POST
│   ├── login/                 POST
│   ├── refresh/               POST
│   ├── logout/                POST
│   ├── me/                    GET
│   ├── onboarding/            PUT
│   └── (list/detail)          GET, PUT, DELETE
├── organizations/
│   ├── entities/              GET, POST
│   ├── locations/             GET, POST
│   ├── departments/           GET, POST
│   └── managers/              GET, POST
└── leaves/
    ├── requests/              GET, POST
    ├── categories/            GET
    ├── calendar/              GET
    ├── balance/my/            GET
    ├── reports/               GET
    └── notifications/         GET, PUT
```

**Responsibilities:**
- Validate incoming requests
- Enforce authentication/authorization
- Execute business logic via services
- Return JSON responses
- Log all actions for audit trail

---

### 3. Business Logic Layer (Services)

**Technology:** Python + Django ORM

**Key Services:**
- **LeaveApprovalService:** Approve/reject/cancel requests
- **NotificationService:** Send notifications on leave events
- **AuditLogService:** Log all state changes
- **DateCalculationService:** Calculate working hours/days

**Responsibilities:**
- Implement business rules
- Coordinate between models
- Handle complex workflows
- Maintain data consistency
- Log actions for audit trail

**Example Workflow (Leave Approval):**
```
1. Manager calls approve endpoint
2. ViewSet permission check (IsManagerOrAdmin)
3. Serializer validation
4. LeaveApprovalService.approve_request() called
   a. Fetch LeaveRequest
   b. Verify status is PENDING
   c. Update LeaveRequest.status = APPROVED
   d. Update LeaveBalance (deduct hours)
   e. Create Notification to user
   f. Log AuditLog entry
5. Return updated LeaveRequest to client
```

---

### 4. Data Access Layer (Django ORM)

**Technology:** Django ORM + PostgreSQL

**Models:**
- User (custom with roles)
- Entity, Location, Department
- DepartmentManager (junction)
- LeaveCategory, LeaveBalance, LeaveRequest
- PublicHoliday
- Notification, AuditLog

**Key Features:**
- Automatic timestamp management (created_at, updated_at)
- Foreign key relationships with cascading rules
- Composite indexes for query optimization
- Query optimization with select_related/prefetch_related

**Responsibilities:**
- Define data structure
- Enforce constraints
- Handle persistence
- Provide query interface to views/services

---

## Authentication & Authorization Flow

### JWT Authentication

```
┌─────────────────────────────────────────────────────────┐
│ 1. User submits email + password at /auth/login/       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Backend validates credentials                        │
│    - Query User by email                                │
│    - Check password hash                                │
└────────────────────┬────────────────────────────────────┘
                     │
                ┌────┴────┐
                │          │
             Valid      Invalid
                │          │
                ▼          ▼
        ┌────────────┐  ┌──────────┐
        │ Issue JWT  │  │ 401 Error│
        │ Tokens     │  └──────────┘
        └────┬───────┘
             │
             ▼
    ┌────────────────────┐
    │ Access Token       │
    │ (1h validity)      │
    │ + Refresh Token    │
    │ (7d validity)      │
    └────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Stored in          │
    │ localStorage       │
    │ (client-side)      │
    └────────────────────┘
```

### Request with JWT Token

```
┌───────────────────────────────────────────────────┐
│ 1. Frontend axios intercepts every request        │
│    Adds: Authorization: Bearer {access_token}     │
└─────────────────────┬─────────────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────────────┐
│ 2. Backend middleware validates token             │
│    - Decode JWT signature                         │
│    - Verify expiration                            │
│    - Extract user from token claims               │
└─────────────────────┬─────────────────────────────┘
                      │
                 ┌────┴────┐
                 │          │
             Valid      Expired/Invalid
                │          │
                ▼          ▼
        ┌────────────┐  ┌──────────┐
        │ Continue   │  │ 401 Error│
        │ Request    │  │ (trigger │
        │            │  │ refresh) │
        └────────────┘  └──────────┘
```

### Token Refresh on Expiry

```
┌─────────────────────────────────────────────────┐
│ 1. Axios interceptor detects 401 response       │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ 2. Send refresh request with refresh token      │
│    POST /api/v1/auth/refresh/                   │
│    Body: { refresh: "{refresh_token}" }         │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│ 3. Backend validates refresh token              │
│    - Check expiration (7d)                       │
│    - Check blacklist                            │
└────────────────────┬────────────────────────────┘
                     │
                ┌────┴────┐
                │          │
             Valid      Invalid
                │          │
                ▼          ▼
        ┌─────────────┐  ┌─────────┐
        │ Issue new   │  │ Redirect│
        │ access token│  │ to Login│
        └─────────────┘  └─────────┘
```

---

## Role-Based Authorization

### Permission Matrix

| Endpoint | EMPLOYEE | MANAGER | HR | ADMIN |
|----------|----------|---------|-------|-------|
| GET /leaves/requests/my/ | ✓ | ✓ | ✓ | ✓ |
| POST /leaves/requests/ | ✓ | ✓ | ✓ | ✓ |
| GET /leaves/approvals/ | ✗ | ✓ | ✓ | ✓ |
| PUT /leaves/requests/{id}/approve/ | ✗ | ✓ | ✓ | ✓ |
| GET /auth/ (list users) | ✗ | ✗ | ✓ | ✓ |
| PUT /auth/{id}/setup/ | ✗ | ✗ | ✓ | ✓ |
| GET /leaves/reports/ | ✗ | ✗ | ✓ | ✓ |
| POST /organizations/entities/ | ✗ | ✗ | ✗ | ✓ |

### Scoping Rules

**EMPLOYEE:**
- Can only access own leave requests
- Can only see own balance
- Can only view team calendar (read-only)

**MANAGER:**
- All EMPLOYEE permissions
- Can approve/reject team member requests
- Can view team analytics
- Only manages department members

**HR:**
- All MANAGER permissions
- Can view all users and adjust balances
- Can view entity-wide analytics
- Can manage leave categories

**ADMIN:**
- Full system access
- Can manage organization structure
- Can manage users and roles
- Can configure system settings

---

## Data Flow Examples

### Leave Request Submission

```
┌─────────────────┐
│ User fills form │
│ - Category      │
│ - Start date    │
│ - End date      │
│ - Hours         │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ Frontend validation  │
│ - Required fields    │
│ - Date ranges        │
│ - Hour amounts       │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────┐
│ POST /api/v1/leaves/     │
│ requests/                │
│ Authorization header     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Backend Serializer          │
│ - Validate format           │
│ - Check data types          │
│ - Verify user has balance   │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Create LeaveRequest Model    │
│ - Set status = PENDING      │
│ - Store all data            │
│ - Record created_at         │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Create Notifications         │
│ - Alert manager              │
│ - Alert HR (optional)        │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Log Audit Entry              │
│ - Action: CREATE_LEAVE_REQ   │
│ - User: requestor            │
│ - Timestamp                  │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Return 201 Created           │
│ - LeaveRequest data          │
│ - Status: PENDING            │
│ - Server-side ID             │
└──────────────────────────────┘
```

### Leave Approval Workflow

```
┌──────────────────────┐
│ Manager views pending│
│ approvals            │
└────────┬─────────────┘
         │
         ▼
┌────────────────────────────────┐
│ GET /api/v1/leaves/requests/    │
│ (filtered to team members)      │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Manager clicks Approve          │
│ - Reviews request details       │
│ - Checks calendar              │
│ - Clicks confirm button         │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ PUT /api/v1/leaves/requests/{id}│
│ /approve/                       │
│ Authorization header (manager)  │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Permission check                │
│ - IsManagerOrAdmin?             │
│ - Department matches?           │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ LeaveApprovalService            │
│ .approve_request():             │
│ 1. Get LeaveRequest             │
│ 2. Verify status = PENDING      │
│ 3. Get LeaveBalance             │
│ 4. Deduct hours_requested       │
│ 5. Set status = APPROVED        │
│ 6. Save both models             │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Create Notifications            │
│ - Employee: request approved    │
│ - HR: log approval              │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Log Audit Entry                 │
│ - Action: APPROVE_LEAVE         │
│ - Manager: approver_id          │
│ - Details: hours, dates         │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Return 200 OK                   │
│ - Updated LeaveRequest          │
│ - Status: APPROVED              │
│ - Balance updated               │
└────────────────────────────────┘
```

---

## Multi-Tenancy Architecture

### Organization Hierarchy

```
┌─────────────────────────────────────────┐
│           Entity (Company)               │
│      Acme Corporation                   │
└────────────┬────────────────────────────┘
             │
             ├─────────────────────────────┬──────────────────┐
             │                             │                  │
             ▼                             ▼                  ▼
    ┌──────────────────┐      ┌──────────────────┐   ┌────────────────┐
    │  Location: HCMC  │      │ Location: Bangkok│   │Location: Manila│
    │  TZ: Asia/HCMC   │      │ TZ: Asia/Bangkok │   │TZ: Asia/Manila │
    └────────┬─────────┘      └────────┬─────────┘   └────────┬───────┘
             │                         │                       │
      ┌──────┴──────┐          ┌──────┴──────┐        ┌────────┴────────┐
      │             │          │             │        │                 │
      ▼             ▼          ▼             ▼        ▼                 ▼
   ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐  ┌──────┐         ┌──────┐
   │Engg. │    │HR    │    │Engg. │    │Sales │  │Ops   │         │Admin │
   │Dept  │    │Dept  │    │Dept  │    │Dept  │  │Dept  │         │Dept  │
   └──────┘    └──────┘    └──────┘    └──────┘  └──────┘         └──────┘
     │            │          │            │        │                 │
   Users        Users       Users        Users    Users              Users
```

### Data Scoping

**User Sees Only:**
- Their own entity/location/department data
- Team members in same department
- Requests/approvals within their scope

**Manager Sees:**
- All department members
- All requests for their team
- Team calendar and reports

**HR Sees:**
- All users in entity
- All requests in entity
- All analytics for entity
- Can create users, adjust balances

**Admin Sees:**
- Everything across all entities
- Organization structure
- Configuration settings

---

## Database Schema Relationships

```
┌──────────────┐          ┌──────────────────┐
│   User       │          │   Entity         │
│              │◄─────┐   │                  │
│ id           │      │   │ id               │
│ email        │      │   │ name             │
│ password     │      │   └──────────────────┘
│ role         │      │
│ entity_id    │──────┘
│ location_id  │──┐
│ department_id├──┐
└──────────────┘  │
                  │    ┌──────────────────┐
                  │    │   Location       │
                  │    │                  │
                  └───►│ id               │
                       │ entity_id        │
                       │ timezone         │
                       └──────────────────┘
                              ▲
                              │
                       ┌──────┴───────────┐
                       │                  │
                       ▼                  ▼
            ┌──────────────────┐  ┌──────────────────┐
            │  Department      │  │  PublicHoliday   │
            │                  │  │                  │
            │ id               │  │ id               │
            │ location_id      │  │ entity_id        │
            │ name             │  │ location_id      │
            └────────┬─────────┘  │ date             │
                     │            └──────────────────┘
                     │
                     └─────────┬─────────────┐
                               │             │
                ┌──────────────┴─┐   ┌──────┴────────────┐
                │                │   │                   │
                ▼                ▼   ▼                   ▼
     ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
     │ DepartmentManager    │  │ LeaveBalance     │  │ LeaveCategory    │
     │ (junction table)     │  │                  │  │                  │
     │                      │  │ id               │  │ id               │
     │ manager_id (User)    │  │ user_id          │  │ name             │
     │ department_id        │  │ allocated_hours  │  │ (Sick, Vacation) │
     │                      │  │ hours_used       │  └──────────────────┘
     └──────────────────────┘  └────────┬─────────┘
                                        │
                        ┌───────────────┴────────────────┐
                        │                                │
                        ▼                                ▼
                 ┌──────────────────┐          ┌──────────────────┐
                 │ LeaveRequest     │          │ Notification     │
                 │                  │          │                  │
                 │ id               │          │ id               │
                 │ user_id          │          │ user_id          │
                 │ category_id      │          │ related_id       │
                 │ start_date       │          │ type             │
                 │ end_date         │          │ read             │
                 │ hours_requested  │          └──────────────────┘
                 │ status           │
                 └──────────────────┘
                        │
                        └────────────────┬─────────────────┐
                                         │                 │
                                         ▼                 ▼
                                 ┌──────────────────────────────┐
                                 │   AuditLog                   │
                                 │                              │
                                 │ id                           │
                                 │ user_id (who did it)         │
                                 │ action (CREATE, APPROVE...)  │
                                 │ object_id (record affected)  │
                                 │ timestamp                    │
                                 └──────────────────────────────┘
```

---

## Deployment Architecture

### Docker Compose Setup

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Host                            │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Database   │  │   Backend    │  │  Frontend    │ │
│  │              │  │              │  │              │ │
│  │ postgres:16  │  │ python:3.12  │  │ node:20      │ │
│  │ port 5432    │  │ port 8000    │  │ port 5173    │ │
│  │              │  │              │  │              │ │
│  │ /var/lib/    │  │ /code        │  │ /app         │ │
│  │ postgresql   │  │ (code volume)│  │ (src volume) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│       ▲                   ▲                   ▲         │
│       │                   │                   │         │
│       └───────────────────┴───────────────────┘         │
│           Docker Networks (bridge)                      │
└─────────────────────────────────────────────────────────┘
```

### Startup Sequence

```
1. Start Docker Compose
   docker-compose up

2. PostgreSQL Container
   - Starts postgres:16-alpine
   - Waits for port 5432 to be ready
   - Initializes empty database

3. Backend Container
   - Waits for db health check
   - Runs Django migrations
   - Loads demo data
   - Starts Gunicorn on port 8000

4. Frontend Container
   - Starts Vite dev server
   - Port 5173 ready for HMR
   - Configured to call backend at port 8000

5. System Ready
   - Access frontend at http://localhost:5173
   - Backend API at http://localhost:8000/api/v1
   - Database at localhost:5432
```

---

## API Communication Pattern

### Request/Response Cycle

```
┌─────────────────────────────────────┐
│  Frontend React Component           │
│  onClick → handleSubmit()           │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Axios Interceptor                  │
│  - Add JWT token to header          │
│  - Serialize request body           │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Network Request                    │
│  POST /api/v1/leaves/requests/      │
│  Headers: Authorization: Bearer...  │
│  Body: { category, startDate, ... } │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Django CORS Middleware             │
│  - Verify request origin            │
│  - Check preflight if needed        │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  JWT Middleware                     │
│  - Extract token from header        │
│  - Verify signature                 │
│  - Decode claims                    │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  URL Routing                        │
│  - Match to ViewSet                 │
│  - Instantiate view                 │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Permission Checks                  │
│  - IsAuthenticated?                 │
│  - IsManagerOrAdmin?                │
│  - has_object_permission?           │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Serializer Validation              │
│  - Check data types                 │
│  - Validate constraints             │
│  - Custom validation methods        │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  View Method (create/update/etc)    │
│  - Call service layer               │
│  - Handle business logic            │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  ORM Operations                     │
│  - Query/create/update/delete       │
│  - Execute SQL on PostgreSQL        │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Response Serialization             │
│  - Serialize model to JSON          │
│  - Include nested data              │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  HTTP Response                      │
│  201 Created                        │
│  Headers: Content-Type: application/│
│  json                               │
│  Body: { id, status, ... }          │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  Frontend Axios Handler             │
│  - Parse response JSON              │
│  - Dispatch state update            │
│  - Handle errors if any             │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  React State Update                 │
│  setState(newData)                  │
│  Component re-renders               │
└─────────────────────────────────────┘
```

---

## Performance Considerations

### Frontend Optimization

- **Code Splitting:** Routes lazy-loaded via React Router
- **Bundling:** Vite produces minimal JavaScript chunks
- **Caching:** Browser cache headers on static assets
- **State:** Minimal global state, prefer local component state

### Backend Optimization

- **Query Optimization:**
  - select_related for foreign keys
  - prefetch_related for reverse relations
  - Indexed fields in WHERE clauses

- **Pagination:**
  - List endpoints default to page size 20
  - Cursor-based pagination for large datasets (future)

- **Caching:**
  - Redis caching layer (future)
  - ETags for conditional requests (future)

### Database Optimization

- **Indexes:**
  - Composite indexes on (user_id, status) for LeaveRequest
  - Composite indexes on (entity_id, location_id) for filtering

- **Connection Pooling:**
  - Gunicorn manages connection pool
  - Default 10 connections per worker

---

## Error Handling Strategy

### Frontend Error Handling

```typescript
try {
  const data = await api.createLeaveRequest(formData);
  setState(data);
} catch (error) {
  if (error.response?.status === 401) {
    // Token expired, redirect to login
    navigate('/login');
  } else if (error.response?.status === 400) {
    // Validation error, show field errors
    setFieldErrors(error.response.data);
  } else {
    // Generic error, show toast
    showErrorToast(error.message);
  }
}
```

### Backend Error Handling

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_leave_request(request):
    try:
        serializer = LeaveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating leave request: {e}")
        return Response(
            {'detail': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

## Security Architecture

### Authentication Security

- **Password Hashing:** PBKDF2 with 600,000 iterations (Django default)
- **JWT Tokens:** Cryptographically signed with SECRET_KEY
- **Token Blacklist:** Revoked tokens stored in Redis (future)
- **HTTPS:** Enforced in production

### Authorization Security

- **Permission Classes:** All views require authentication or custom permissions
- **Role-based Scoping:** Users can only access own/team data
- **SQL Injection Prevention:** Django ORM parameterized queries
- **CSRF Protection:** CSRF tokens for state-changing requests

### Data Security

- **Encryption:** Passwords hashed, sensitive data not logged
- **Audit Trail:** All actions logged with user/timestamp
- **Input Validation:** All endpoints validate input type/format
- **Output Escaping:** React auto-escapes JSX, no XSS vulnerabilities

---

## Monitoring & Observability

### Logging Points

- User login/logout
- Leave request creation/approval/rejection
- User role changes
- Balance adjustments
- API errors and exceptions
- Database query performance (development)

### Audit Trail

Every significant action stored in AuditLog:
- Creator (who did it)
- Timestamp (when)
- Action type (what was done)
- Object ID (which record affected)
- Details (additional context)

---

## Scalability Roadmap

### Current Limitations

- Single database instance (no replication)
- No caching layer
- No load balancing
- WebSocket support not implemented

### Future Scaling

1. **Read Replicas:** PostgreSQL standby for read-heavy queries
2. **Caching:** Redis for frequently accessed data
3. **Load Balancing:** Multiple Gunicorn workers behind Nginx
4. **Async Tasks:** Celery for background jobs
5. **CDN:** CloudFlare for static asset delivery
6. **Microservices:** Separate notification/audit services (optional)

