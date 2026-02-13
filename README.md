# Leave Management System

A comprehensive web application for managing employee leave requests, approvals, and analytics. Built with Django + React, featuring JWT authentication, hours-based tracking, and multi-tenant organizational support.

**Status:** Active Development | **Phase 1:** Complete ✓ | **Phase 2:** 70% In Progress

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Running with Docker

```bash
git clone <repo-url>
cd test-leave
docker compose up

# Wait 1-2 minutes for services to start
# Frontend: http://localhost:5173
# API: http://localhost:8000/api/v1
# Admin: http://localhost:8000/admin
```

**Demo Credentials:**
```
Email: employee@example.com
Password: demo123456
```

### Local Development

**Backend:**
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:pass@localhost:5432/leave_db
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 + TypeScript, Vite, Ant Design, Axios |
| **Backend** | Django 6.0 + DRF, PostgreSQL 16, SimpleJWT |
| **Infrastructure** | Docker Compose, Gunicorn (4w × 4t) |
| **Testing** | pytest (backend) |

---

## Core Features

### User Management
- Email-based JWT authentication with token refresh
- Role-based access: EMPLOYEE, MANAGER, HR, ADMIN
- Onboarding wizard (entity/location/department assignment)
- Profile management with approver relationships

### Leave Management
- Submit requests with category, dates, partial days (0.5-1.5h)
- Automatic working day calculation (Mon-Fri, 8h/day)
- Holiday exclusion from calculations
- Four leave types: EXEMPT_VACATION, NON_EXEMPT_VACATION, EXEMPT_SICK, NON_EXEMPT_SICK
- Dynamic EXEMPT_VACATION by years of service (Y1: 8h/mo, Y2-5: 80h, Y6-10: 120h, Y11-15: 160h, Y16+: 200h)

### Approval Workflow
- Manager approval/rejection with atomic balance updates
- Approver-based permissions (not role-based)
- 24-hour rejection rule for approved leaves
- Automatic notifications and audit trail

### Team Collaboration
- Team calendar with color-coded leaves
- Drag-to-create requests on calendar
- Department-level leave reports
- Business trip tracking with overlap detection

### Organizational Structure
- Multi-tenant: Entity → Location → Department hierarchy
- 33 timezone options per location
- Manager assignments (many-to-many)
- Public holidays (scoped: global, entity, location)

---

## API Overview

**All endpoints** require JWT authentication (except login/register).

```
Auth:
  POST   /api/v1/auth/register/           Register
  POST   /api/v1/auth/login/              Login
  POST   /api/v1/auth/refresh/            Refresh token
  POST   /api/v1/auth/logout/             Logout

Leaves:
  GET    /api/v1/leaves/requests/         List requests
  POST   /api/v1/leaves/requests/         Create request
  PUT    /api/v1/leaves/requests/{id}/approve/    Approve
  PUT    /api/v1/leaves/requests/{id}/reject/     Reject
  PUT    /api/v1/leaves/requests/{id}/cancel/     Cancel
  GET    /api/v1/leaves/balance/my/       My balance
  GET    /api/v1/leaves/calendar/         Team calendar
  POST   /api/v1/leaves/export/           Export to CSV

Organizations:
  GET    /api/v1/organizations/entities/              List entities
  POST   /api/v1/organizations/entities/create/       Create entity (HR/Admin)
  PATCH  /api/v1/organizations/entities/{id}/update/  Update entity (HR/Admin)
  PATCH  /api/v1/organizations/entities/{id}/soft-delete/  Soft-delete with cascade (HR/Admin)
  GET    /api/v1/organizations/entities/{id}/delete-impact/  Get deletion impact counts
  GET    /api/v1/organizations/locations/             List locations
  GET    /api/v1/organizations/departments/           List departments

Notifications:
  GET    /api/v1/notifications/           List notifications
  PUT    /api/v1/notifications/{id}/      Mark read
```

**Full API docs:** http://localhost:8000/api/v1/docs/ (Swagger)

---

## Documentation

Comprehensive documentation in `/docs` directory:
- **[project-overview-pdr.md](./docs/project-overview-pdr.md)** - Product requirements, user roles, core features
- **[codebase-summary.md](./docs/codebase-summary.md)** - Project structure, Django apps, frontend architecture
- **[code-standards.md](./docs/code-standards.md)** - Coding conventions, API patterns, testing guidelines
- **[system-architecture.md](./docs/system-architecture.md)** - Complete technical reference (database schema, ALL API routes, business logic)
- **[deployment-guide.md](./docs/deployment-guide.md)** - Docker setup, environment variables, production checklist
- **[development-roadmap.md](./docs/development-roadmap.md)** - Phases, milestones, progress tracking
- **[project-changelog.md](./docs/project-changelog.md)** - Version history, changes, migration guides

---

## Project Structure

```
test-leave/
├── backend/              Django settings
├── users/               Auth & user management
├── organizations/       Entity/Location/Department
├── leaves/              Leave management core
│   ├── views/          Endpoint implementations
│   ├── services.py     LeaveApprovalService
│   └── utils.py        Calculations (working days, overlap)
├── core/               Notifications & audit logs
├── frontend/src/       React SPA
│   ├── pages/          9 main pages
│   ├── components/     5 reusable components
│   ├── api/            API client files
│   └── auth/           AuthContext
├── docs/               Project documentation
└── docker-compose.yml  Multi-container setup
```

---

## Database

PostgreSQL 16 with key tables:
- `users_user` - Custom user (roles, approver FK, join_date)
- `organizations_*` - Entity/Location/Department hierarchy
- `leaves_*` - LeaveRequest, LeaveBalance (Decimal), LeaveCategory, PublicHoliday
- `core_*` - Notification, AuditLog

---

## Configuration

**Environment Variables:**

Backend (.env or docker-compose):
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@db:5432/leave_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800
```

Frontend (.env.local):
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Development

### Running Tests

```bash
# Backend
python -m pytest --verbosity=2
cd frontend && npm test  # Frontend tests
```

### Code Quality

```bash
flake8 . --exclude=venv
cd frontend && npx tsc --noEmit
```

---

## Deployment

### Docker Production Build

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Configure HTTPS/SSL certificates
- [ ] Set DEBUG=False
- [ ] Use strong SECRET_KEY
- [ ] Configure database backups
- [ ] Setup monitoring and logging
- [ ] Configure CORS origins to HTTPS only
- [ ] Enable HSTS headers
- [ ] Load test before launch

---

## Troubleshooting

**Docker services won't start:**
```bash
docker compose logs backend
docker compose logs frontend
docker compose down
docker compose up --build
```

**Database connection error:**
```bash
docker compose exec backend python manage.py migrate --check
docker compose down -v  # Reset everything
docker compose up       # Fresh start
```

**JWT token errors:**
- Clear browser localStorage and login again
- Verify SECRET_KEY hasn't changed
- Check token expiration times

---

## User Roles & Permissions

| Role | Capabilities |
|------|--------------|
| **EMPLOYEE** | Submit leave, view balance, see team calendar |
| **MANAGER** | Employee + approve/reject team requests, team reports |
| **HR** | Manager + user management, balance adjustments, entity reports |
| **ADMIN** | Full system access, org structure, configuration |

---

## Contributing

1. Read [docs/code-standards.md](./docs/code-standards.md)
2. Follow conventional commit format: `feat:`, `fix:`, `docs:`, etc.
3. Write tests (80%+ coverage target)
4. Ensure all tests pass before PR
5. Update docs if changing features

---

## Support

- **Issues:** GitHub Issues
- **API Docs:** http://localhost:8000/api/v1/docs/
- **Full Roadmap:** [development-roadmap.md](./docs/development-roadmap.md)

---

## Nginx Reverse Proxy Config

If deploying behind nginx with SSL, add these location blocks to your server config:

```nginx
# Backend API
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Django media files (user uploads)
location /media/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Django static files (admin CSS/JS)
location /static/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Django admin
location /admin/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Frontend (catch-all)
location / {
    proxy_pass http://127.0.0.1:5173;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

**Last Updated:** 2026-02-09 | **Version:** 1.1.2
