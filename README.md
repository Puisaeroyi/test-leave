# Leave Management System

A comprehensive, multi-tenant web application for managing employee leave requests, approvals, and analytics. Built with Django + React, featuring JWT authentication, hours-based leave tracking, and a complete approval workflow.

**Status:** Active Development (Phase 1 Complete, Phase 2 In Progress)

---

## Quick Links

- **API Documentation:** [docs/api-overview.md](docs/api-overview.md)
- **Database Schema:** [docs/database-schema-erd.md](docs/database-schema-erd.md)
- **Code Standards:** [docs/code-standards.md](docs/code-standards.md)
- **System Architecture:** [docs/system-architecture.md](docs/system-architecture.md)
- **Project Roadmap:** [docs/project-roadmap.md](docs/project-roadmap.md)

---

## Tech Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django + DRF | 6.0.1 |
| Database | PostgreSQL | 16 |
| Authentication | SimpleJWT | Latest |
| Server | Gunicorn | Latest |
| Language | Python | 3.12 |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 19.2 |
| Language | TypeScript | 5.9 |
| Build Tool | Vite | 7.2 |
| Styling | Tailwind CSS | 4.1 |
| Routing | React Router | 7.x |
| HTTP Client | Axios | Latest |

### Infrastructure

| Component | Technology | Version |
|-----------|-----------|---------|
| Containerization | Docker | Latest |
| Orchestration | Docker Compose | 3.8 |
| Development Port | Vite | 5173 |
| API Port | Gunicorn | 8000 |
| Database Port | PostgreSQL | 5432 |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Node.js 20+ (optional, for local frontend development)
- Python 3.12+ (optional, for local backend development)

### Running with Docker

```bash
# Clone the repository
git clone <repo-url>
cd test-leave

# Start all services
docker-compose up

# Wait for services to start (1-2 minutes)
# Access the application:
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

#### Backend Setup

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database
export DATABASE_URL=postgresql://user:password@localhost:5432/leave_db

# Run migrations
python manage.py migrate

# Load demo data
python manage.py loaddata demo_data

# Start development server
python manage.py runserver 0.0.0.0:8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

---

## Project Structure

```
test-leave/
├── backend/                    # Django settings package
├── users/                      # User authentication & profile app
│   ├── models.py              # Custom User model with roles
│   ├── views.py               # Auth endpoints
│   ├── serializers.py         # User data serialization
│   └── permissions.py         # Role-based permissions
├── organizations/             # Entity/Location/Department app
│   ├── models.py              # Org hierarchy models
│   └── views.py               # CRUD endpoints
├── leaves/                    # Leave management app
│   ├── models.py              # LeaveRequest, Balance, Category
│   ├── views.py               # Leave API endpoints (922 LOC)
│   ├── services.py            # LeaveApprovalService
│   ├── utils.py               # Date/hour calculations
│   └── serializers.py         # Leave data validation
├── core/                      # Notifications & audit app
│   ├── models.py              # Notification, AuditLog
│   └── views.py               # Notification endpoints
├── frontend/src/              # React application
│   ├── pages/                 # Page components
│   ├── components/            # Reusable components
│   ├── hooks/                 # Custom React hooks
│   ├── api/                   # Axios API client
│   ├── types/                 # TypeScript type definitions
│   └── App.tsx                # Route definitions
├── docs/                      # Project documentation
├── docker-compose.yml         # Multi-container setup
├── manage.py                  # Django CLI
└── README.md                  # This file
```

---

## Core Features

### User Management

- **Email-based authentication** with JWT tokens
- **Role-based access control:** EMPLOYEE, MANAGER, HR, ADMIN
- **Onboarding wizard** for entity/location/department assignment
- **Profile management** with department and role tracking

### Leave Management

- **Submit leave requests** with category, dates, and hours
- **Automatic validation** against available balance
- **Hours-based tracking** (8 hours/day default, dynamic EXEMPT_VACATION by years of service)
- **Weekend & holiday exclusion** in calculations
- **Partial day support** (0.5h, 1.0h, 1.5h increments)

### Approval Workflow

- **Manager approvals** for team member requests
- **Multi-tenant scoping** by department/location
- **Automatic balance updates** on approval
- **Rejection with reasons** capability
- **Audit trail** of all actions

### Team Collaboration

- **Team calendar** with color-coded leave visualization
- **Leave balance cards** showing hours used/remaining
- **Department-level reporting** for managers
- **Entity-wide analytics** for HR
- **In-app notifications** for requests and approvals

### Organizational Structure

- **Multi-tenant support** via Entity/Location/Department hierarchy
- **Timezone-aware** scheduling per location
- **Manager assignment** with DepartmentManager junction
- **Public holidays** scoped by location

### Audit & Compliance

- **Complete audit trail** of all leave actions
- **Action logging** with user, timestamp, and details
- **Request history** with status and approval notes
- **Balance change tracking** with adjustments

---

## API Overview

All endpoints require JWT authentication (except `/api/v1/auth/login/` and `/api/v1/auth/register/`).

### Authentication

```
POST   /api/v1/auth/register/           Register new user
POST   /api/v1/auth/login/              Get JWT tokens
POST   /api/v1/auth/refresh/            Refresh access token
POST   /api/v1/auth/logout/             Blacklist refresh token
GET    /api/v1/auth/me/                 Get current user
PUT    /api/v1/auth/onboarding/         Complete onboarding
```

### Leave Requests

```
GET    /api/v1/leaves/requests/         List all requests (scoped)
POST   /api/v1/leaves/requests/         Create new request
GET    /api/v1/leaves/requests/my/      Get user's requests
PUT    /api/v1/leaves/requests/{id}/approve/     Manager approves
PUT    /api/v1/leaves/requests/{id}/reject/      Manager rejects
PUT    /api/v1/leaves/requests/{id}/cancel/      User cancels
```

### Leave Data

```
GET    /api/v1/leaves/categories/       List leave types
GET    /api/v1/leaves/balance/my/       Get user's balance
GET    /api/v1/leaves/calendar/         Get team calendar
GET    /api/v1/leaves/reports/          Get analytics (HR only)
```

### Users & Organizations

```
GET    /api/v1/auth/                    List users (HR/Admin)
POST   /api/v1/auth/create/             Create user (HR/Admin)
PUT    /api/v1/auth/{id}/setup/         Assign role/dept (HR/Admin)
PUT    /api/v1/auth/{id}/balance/adjust/ Adjust balance (HR/Admin)

GET    /api/v1/organizations/entities/
GET    /api/v1/organizations/locations/
GET    /api/v1/organizations/departments/
GET    /api/v1/organizations/managers/
```

### Notifications

```
GET    /api/v1/notifications/           List notifications
PUT    /api/v1/notifications/{id}/      Mark as read
PUT    /api/v1/notifications/mark-all-read/
GET    /api/v1/notifications/unread-count/
```

**Full API documentation:** [docs/api-overview.md](docs/api-overview.md)

---

## Database Schema

The system uses PostgreSQL 16 with the following key tables:

- **users_user** - Custom user with roles and onboarding flags
- **organizations_entity** - Companies/subsidiaries
- **organizations_location** - Offices with timezone
- **organizations_department** - Organizational units
- **organizations_departmentmanager** - Manager assignments
- **leaves_leavecategory** - Leave types (Sick, Vacation, etc.)
- **leaves_leavebalance** - Annual allocation tracking
- **leaves_leaverequest** - Individual requests with full lifecycle
- **leaves_publicholiday** - Non-working days
- **core_notification** - In-app alerts
- **core_auditlog** - Complete action history

**Full schema documentation:** [docs/database-schema-erd.md](docs/database-schema-erd.md)

---

## User Roles & Permissions

| Role | Capabilities |
|------|--------------|
| **EMPLOYEE** | Submit leave, view own balance, see team calendar, manage notifications |
| **MANAGER** | All EMPLOYEE + approve/reject team requests, view team reports |
| **HR** | All MANAGER + user management, balance adjustments, entity-wide reports |
| **ADMIN** | Full system access, org structure management, configuration |

---

## Development Workflow

### Running Tests

```bash
# Backend tests
python manage.py test

# Frontend tests
cd frontend && npm run test

# Test coverage
python manage.py test --cov
```

### Code Quality

```bash
# Backend linting
flake8 . --exclude=venv

# Frontend linting
cd frontend && npm run lint

# Type checking
cd frontend && npx tsc --noEmit
```

### Building for Production

```bash
# Backend: Gunicorn handles serving
# Frontend: Build static assets
cd frontend && npm run build

# Output: frontend/dist/
```

---

## Configuration

### Environment Variables

**Backend (.env or docker-compose environment):**
```
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@db:5432/leave_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173

JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=3600      # 1 hour
JWT_REFRESH_TOKEN_LIFETIME=604800   # 7 days
```

**Frontend (.env.local):**
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Leave Management System
```

### Database Connection

Default: PostgreSQL running in Docker on port 5432

To use external database:
```bash
export DATABASE_URL=postgresql://user:password@host:5432/leave_db
python manage.py migrate
```

---

## Deployment

### Docker Production Build

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Run containers
docker-compose -f docker-compose.prod.yml up -d

# Scale backend servers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Requirements for Production

- [ ] Configure HTTPS/SSL certificates
- [ ] Set DEBUG=False
- [ ] Use strong SECRET_KEY
- [ ] Configure database backups
- [ ] Setup monitoring and logging
- [ ] Configure email service
- [ ] Review security settings
- [ ] Load test before go-live

**Deployment guide:** [docs/deployment-guide.md](docs/deployment-guide.md) (future)

---

## Troubleshooting

### Common Issues

**Docker services won't start:**
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Rebuild images
docker-compose down
docker-compose up --build
```

**Database connection error:**
```bash
# Verify PostgreSQL is running
docker-compose ps

# Check database migrations
docker-compose exec backend python manage.py migrate --check

# Reset database
docker-compose down -v  # Removes all volumes
docker-compose up       # Recreates everything
```

**Frontend API calls failing:**
- Verify backend is running on port 8000
- Check VITE_API_BASE_URL is correct
- Check CORS settings in Django
- Review browser console for errors

**JWT token errors:**
- Clear localStorage and login again
- Verify SECRET_KEY hasn't changed
- Check token expiration times

---

## Documentation

Comprehensive documentation available in `/docs`:

| Document | Purpose |
|----------|---------|
| [api-overview.md](docs/api-overview.md) | Complete API reference (1,095 lines) |
| [database-schema-erd.md](docs/database-schema-erd.md) | ERD and schema details |
| [code-standards.md](docs/code-standards.md) | Coding conventions and patterns |
| [system-architecture.md](docs/system-architecture.md) | Architecture diagrams and flows |
| [project-roadmap.md](docs/project-roadmap.md) | Development phases and timeline |
| [codebase-summary.md](docs/codebase-summary.md) | Codebase structure overview |
| [project-overview-pdr.md](docs/project-overview-pdr.md) | PDR and business requirements |

---

## Contributing

1. **Read code standards:** [docs/code-standards.md](docs/code-standards.md)
2. **Follow git conventions:** Conventional commits format
3. **Write tests:** Aim for > 80% coverage
4. **Code review:** All PRs require review before merge
5. **Update docs:** Keep documentation in sync with code changes

---

## Support & Issues

- **Bug reports:** GitHub Issues
- **Feature requests:** GitHub Discussions
- **Documentation:** /docs directory
- **Code examples:** [docs/sample-data-walkthrough.md](docs/sample-data-walkthrough.md)

---

## Roadmap

**Current Status:** Phase 1 Complete (100%), Phase 2 In Progress (60%)

**Upcoming:**
- Admin dashboard full implementation
- Approvals page with approval/rejection forms
- Mobile responsiveness improvements
- Email notifications integration
- Advanced reporting & analytics
- WebSocket real-time updates

**Full roadmap:** [docs/project-roadmap.md](docs/project-roadmap.md)

---

## License

[Add license information]

---

## Contact

**Project Lead:** [Team information]
**GitHub:** [Repository URL]
**Documentation:** See `/docs` directory

---

**Last Updated:** 2026-01-27 | **Version:** 1.0.0
