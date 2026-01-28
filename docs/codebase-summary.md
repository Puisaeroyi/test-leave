# Codebase Summary

**Project:** Leave Management System
**Last Updated:** 2026-01-27
**Total Python LOC:** ~4,234
**Total TypeScript LOC:** ~5,036

---

## Directory Structure

```
/home/silver/test/test-leave/
├── backend/                    # Django project settings
├── users/                      # User authentication & profile app
├── organizations/              # Entity/Location/Department models
├── leaves/                     # Leave requests & balance app
├── core/                       # Notifications & audit logging app
├── frontend/src/               # React application
├── docs/                       # Project documentation
├── docker-compose.yml          # Multi-container setup
└── manage.py                   # Django management CLI
```

---

## Backend Django Applications

### 1. users/ (Custom Auth & User Management)

**Primary Files:**
- `models.py` (104 LOC) - AbstractUser with email auth, roles (EMPLOYEE/MANAGER/HR/ADMIN)
- `views.py` (408 LOC) - Auth endpoints, user listing, onboarding, balance adjustments
- `serializers.py` (226 LOC) - User data validation and serialization
- `permissions.py` - Role-based permission checks
- `urls.py` - API route definitions

**Key Models:**
- `User` - Custom user with role field, onboarding flags, department assignment

**Key Endpoints:**
- POST `/api/v1/auth/register/` - User registration
- POST `/api/v1/auth/login/` - JWT token issue
- GET `/api/v1/auth/me/` - Current user details
- PUT `/api/v1/auth/onboarding/` - Complete onboarding
- GET `/api/v1/auth/` - List users (HR/Admin)
- PUT `/api/v1/auth/<id>/setup/` - Assign role/department
- PUT `/api/v1/auth/<id>/balance/adjust/` - Adjust leave balance

**Authentication:**
- SimpleJWT: 1h access token, 7d refresh token
- Token blacklist on logout

---

### 2. organizations/ (Hierarchy & Structure)

**Primary Files:**
- `models.py` (140 LOC) - Entity, Location, Department, DepartmentManager
- `views.py` - CRUD endpoints for org structure
- `serializers.py` - Org data serialization

**Key Models:**
- `Entity` - Company/subsidiary
- `Location` - Office with timezone field
- `Department` - Org unit within location
- `DepartmentManager` - Junction table linking managers to departments

**Key Endpoints:**
- `/api/v1/organizations/entities/`
- `/api/v1/organizations/locations/` - Filtered by entity
- `/api/v1/organizations/departments/` - Filtered by location
- `/api/v1/organizations/managers/` - Manager assignments

**Design Pattern:**
- Hierarchical: Entity > Location > Department
- Managers assigned via DepartmentManager junction
- Timezone per location for leave calculations

---

### 3. leaves/ (Leave Requests & Balance)

**Primary Files:**
- `views.py` (922 LOC) - Leave API endpoints (largest backend file)
- `services.py` (224 LOC) - LeaveApprovalService, validation logic
- `serializers.py` (155 LOC) - Leave data serialization
- `utils.py` (161 LOC) - Date/hour calculations, weekend/holiday exclusion
- `models.py` (133 LOC) - LeaveRequest, LeaveBalance, LeaveCategory, PublicHoliday

**Key Models:**
- `LeaveCategory` - Leave type (Sick, Vacation, Personal, etc.)
- `LeaveBalance` - Annual allocation tracking (96h default)
- `LeaveRequest` - Individual request (PENDING/APPROVED/REJECTED/CANCELLED)
- `PublicHoliday` - Non-working days per entity/location

**Key Endpoints:**
- GET `/api/v1/leaves/calendar/` - Team calendar data
- GET `/api/v1/leaves/categories/` - Available leave types
- GET `/api/v1/leaves/balance/my/` - User's balance
- GET/POST `/api/v1/leaves/requests/` - List/create requests
- PUT `/api/v1/leaves/requests/<id>/approve/` - Manager approval
- PUT `/api/v1/leaves/requests/<id>/reject/` - Manager rejection
- GET `/api/v1/leaves/reports/` - HR analytics

**Business Logic:**
- Hours-based tracking (8 hours/day standard)
- Automatic weekend exclusion
- Public holiday deduction
- Partial day support (0.5h, 1.0h, 1.5h+)
- LeaveApprovalService handles approval workflow
- Audit logging on all state changes

---

### 4. core/ (Notifications & Audit)

**Primary Files:**
- `views.py` (175 LOC) - Notification endpoints, audit logs
- `models.py` - Notification, AuditLog models
- `signals.py` - Auto-trigger notifications on leave events

**Key Models:**
- `Notification` - In-app alerts (read/unread states)
- `AuditLog` - Complete action history with user/timestamp/changes

**Key Endpoints:**
- GET `/api/v1/notifications/` - List user notifications
- PUT `/api/v1/notifications/<id>/` - Mark as read
- PUT `/api/v1/notifications/mark-all-read/`
- GET `/api/v1/notifications/unread-count/`

**Audit Scope:**
- Leave request creation/approval/rejection/cancellation
- User role changes
- Leave balance adjustments
- Login/logout events

---

### Backend Configuration

**Key Files:**
- `backend/settings.py` (225 LOC) - Django configuration, database, JWT settings, CORS
- `backend/urls.py` - API v1 route aggregation

**Settings Highlights:**
- PostgreSQL database
- INSTALLED_APPS: users, organizations, leaves, core, rest_framework, corsheaders
- JWT token limits: 1h access, 7d refresh
- CORS whitelist for frontend domain
- Debug mode configurable via environment

---

## Frontend React Application

### Architecture

**State Management:**
- `AuthContext` - Global auth state, user roles
- Component-level `useState` hooks
- No Redux/Zustand (React Query installed but unused)

**API Client:**
- Axios instance with JWT interceptor
- Auto token refresh on 401 response
- Base URL configurable

**Routing:**
- React Router v7
- Protected routes based on user role
- Public routes: /login, /register
- Protected: /, /onboarding, /leaves/new, /calendar, /approvals, /admin

---

### Page Components

| File | LOC | Purpose |
|------|-----|---------|
| LeaveRequestPage.tsx | 632 | Leave form with category/date/hours |
| CalendarPage.tsx | 610 | Team calendar visualization |
| DashboardPage.tsx | 603 | Main dashboard with stats/notifications |
| OnboardingPage.tsx | 331 | 4-step setup wizard |
| NotificationsPage.tsx | 326 | Notification center |
| AdminDashboard.tsx | 180 | Admin panel (stub) |
| RegisterPage.tsx | 216 | User registration form |
| LoginPage.tsx | 163 | Authentication form |
| App.tsx | 145 | Route definitions & auth wrapper |

---

### Component Library

**Layout:**
- `Layout.tsx` - Main wrapper with sidebar + header
- `Sidebar.tsx` - Navigation menu
- `Header.tsx` - Top bar with user menu

**UI Components:**
- `Button.tsx` - Standard button variants
- `Card.tsx` - Content container
- `Modal.tsx` - Dialog component
- `Input.tsx` - Form field wrapper
- `Spinner.tsx` - Loading indicator
- `Badge.tsx` - Status/tag display

**Leave-Specific:**
- `LeaveBalance.tsx` - Balance card display
- `LeaveRequestForm.tsx` - Reusable form
- `LeaveCalendarGrid.tsx` - Calendar visualization
- `NotificationCenter.tsx` (271 LOC) - Notification UI

---

### API Integration

**API Modules:**
- `api/auth.ts` - Login, register, refresh token
- `api/leaves.ts` - Leave CRUD operations
- `api/users.ts` - User management endpoints
- `api/notifications.ts` - Notification fetching

**TypeScript Types:**
- `types/index.ts` (140 LOC) - All TypeScript interfaces/types
- Covers: User, LeaveRequest, LeaveBalance, Organization, Notification

**Axios Configuration:**
- Base URL: `http://localhost:8000/api/v1`
- Headers: `Authorization: Bearer {token}`
- Interceptors: auto-refresh on 401

---

### Styling

- **Tailwind CSS 4.1** - Utility-first CSS
- **Custom Theme:**
  - Primary color: Blue (customizable)
  - Dark mode support
  - Responsive breakpoints
- **Global Styles:** `src/index.css`

---

## Database Schema (PostgreSQL 16)

**Key Tables:**
- `users_user` - Custom user with role, timestamps
- `organizations_entity` - Companies
- `organizations_location` - Offices with timezone
- `organizations_department` - Org units
- `organizations_departmentmanager` - Manager assignments
- `leaves_leavecategory` - Leave types
- `leaves_leavebalance` - Annual allocation
- `leaves_leaverequest` - Individual requests with timestamps
- `leaves_publicholiday` - Non-working days
- `core_notification` - Alerts
- `core_auditlog` - Action history

**Indexes:**
- User email (unique)
- Department manager (composite)
- LeaveRequest dates + user
- Notification user + read status

---

## Docker Composition

**Services:**

| Service | Image | Port | Health Check |
|---------|-------|------|--------------|
| db | postgres:16-alpine | 5432 | pg_isready |
| backend | python:3.12-slim | 8000 | Gunicorn |
| frontend | node:20-alpine | 5173 | Vite dev |

**Startup Sequence:**
1. DB container waits for postgres to be ready
2. Backend runs migrations and seeds demo data
3. Frontend dev server starts with HMR

**Volumes:**
- Backend: `/code` for live editing
- Frontend: `/app` for source code
- DB: `/var/lib/postgresql/data` for persistence

---

## Build & Development

**Backend:**
- Language: Python 3.12
- Framework: Django 6.0.1
- Package Manager: pip
- Test Runner: Django test suite

**Frontend:**
- Language: TypeScript 5.9
- Framework: React 19.2
- Build Tool: Vite 7.2
- Package Manager: npm
- Test Runner: Vitest (installed, not configured)

**Commands:**
- Backend: `python manage.py runserver`
- Frontend: `npm run dev`
- Production: `npm run build` + Gunicorn

---

## Testing Infrastructure

**Backend Tests:**
- Located in app `tests/` directories
- Test cases documented in `docs/test-cases.md`
- Coverage includes: models, views, serializers, permissions

**Frontend Tests:**
- Vitest configured in `vite.config.ts`
- Test files: `__tests__/` directories
- Not yet implemented for components

---

## API Versioning & Documentation

**API Version:** v1
**Base URL:** `http://localhost:8000/api/v1`
**Format:** REST + JSON
**Authentication:** JWT Bearer tokens
**Documentation:** `docs/api-overview.md` (1,095 LOC)

**Endpoint Patterns:**
- GET `/resource/` - List with filters
- POST `/resource/` - Create
- GET `/resource/<id>/` - Retrieve
- PUT `/resource/<id>/` - Update
- DELETE `/resource/<id>/` - Delete
- Custom actions: `/resource/<id>/{action}/`

---

## Configuration & Environment

**Backend (.env):**
- `DEBUG` - Development mode
- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - Django secret
- `ALLOWED_HOSTS` - CORS whitelist
- `JWT_*` - Token lifetime settings

**Frontend (.env):**
- `VITE_API_BASE_URL` - Backend URL
- `VITE_APP_NAME` - App title

**Docker:**
- Services configured in `docker-compose.yml`
- Environment variables passed via `environment:` blocks
- Health checks ensure startup sequence

---

## Dependencies Summary

**Backend Key Packages:**
- Django 6.0.1, djangorestframework, djangorestframework-simplejwt
- psycopg2 (PostgreSQL adapter)
- python-decouple (environment variables)
- django-cors-headers (CORS support)

**Frontend Key Packages:**
- React 19.2, react-router-dom 7.x, axios
- TypeScript 5.9, Vite 7.2
- Tailwind CSS 4.1, tailwind-merge
- @radix-ui components (installed)

---

## Code Organization Principles

1. **Separation of Concerns:**
   - Models handle data
   - Views/serializers handle HTTP
   - Services handle business logic
   - Utils handle helpers

2. **Reusability:**
   - Component-based UI
   - API module functions
   - Shared TypeScript types
   - DRY principle across files

3. **Scalability:**
   - Multi-tenant organization scoping
   - Modular Django apps
   - Lazy loading in React
   - Indexed database queries

---

## Performance Characteristics

**Backend:**
- Database queries optimized with select_related/prefetch_related
- Pagination on list endpoints
- Caching layer (future enhancement)

**Frontend:**
- Code splitting by route
- Image optimization in Tailwind
- Bundle size: ~450KB gzipped (target < 500KB)
- Load time: < 3s target

**Database:**
- PostgreSQL indexes on foreign keys
- Composite indexes for common queries
- Connection pooling via Gunicorn

