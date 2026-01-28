# Project Overview & Product Development Requirements

**Status:** Active Development
**Version:** 1.0.0
**Last Updated:** 2026-01-27

---

## Project Description

Leave Management System is a comprehensive, multi-tenant web application for managing employee leave requests, approvals, and analytics. It supports complex organizational hierarchies with entity, location, and department scoping, enabling HR departments and managers to efficiently track leave hours across distributed teams.

**Tech Stack:**
- Backend: Django 6.0.1 + Django REST Framework
- Frontend: React 19.2 + TypeScript 5.9
- Database: PostgreSQL 16
- Deployment: Docker Compose 3.8

---

## Core Features

### 1. User Management & Authentication
- Email-based user registration and login
- JWT authentication (1h access token, 7d refresh token)
- Role-based access control (EMPLOYEE, MANAGER, HR, ADMIN)
- Onboarding wizard for new users
- User profile management

### 2. Organization Structure
- Multi-tenant architecture with Entity/Location/Department hierarchy
- Entity: Companies or subsidiaries
- Location: Offices with timezone settings
- Department: Organizational units within locations
- DepartmentManager junction table for manager assignments

### 3. Leave Management
- **Leave Requests:** Full lifecycle (PENDING → APPROVED/REJECTED/CANCELLED)
- **Leave Categories:** Configurable leave types (Sick, Personal, Vacation, etc.)
- **Leave Balance:** 96 hours/year default tracking with adjustments
- **Public Holidays:** Entity/location-scoped holiday calendars
- **Approval Workflow:** Manager hierarchy-based approvals

### 4. Leave Calculations
- Hours-based tracking (8 hours/day standard)
- Automatic weekend exclusion
- Public holiday deduction
- Partial day support (0.5, 1.0, 1.5+ hours)

### 5. Team & Reporting
- Team calendar with color-coded leave visualization
- HR analytics and leave reports
- Audit trail for all leave actions
- In-app notifications for requests/approvals

### 6. Notifications & Audit
- Real-time notifications (in-app)
- Complete action audit logging
- Notification preferences (future enhancement)

---

## User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **EMPLOYEE** | View own leave balance, request leave, view team calendar, manage notifications |
| **MANAGER** | All EMPLOYEE permissions + approve/reject team requests, view team reports |
| **HR** | All MANAGER permissions + user management, leave balance adjustments, entity-wide reports |
| **ADMIN** | Full system access, organization structure management, configuration |

---

## Functional Requirements

### User Management
- FR-1.1: Users register with email and password
- FR-1.2: Password validation (minimum 8 chars, mix of letter/number)
- FR-1.3: Email verification (future enhancement)
- FR-1.4: Onboarding assigns user to entity/location/department
- FR-1.5: Role assignment during onboarding or by HR/Admin

### Leave Requests
- FR-2.1: Employees submit leave requests with category, start date, end date, hours
- FR-2.2: System validates leave hours against balance
- FR-2.3: Prevents weekend/holiday inclusion in calculations
- FR-2.4: Managers receive notifications for pending approvals
- FR-2.5: Approved requests automatically deduct hours from balance
- FR-2.6: Rejected requests include reason/notes

### Approvals
- FR-3.1: Managers approve/reject requests for their team members
- FR-3.2: Multi-level approval chain if needed (future)
- FR-3.3: Approval history retained for audit trail
- FR-3.4: Automatic escalation for overdue approvals (future)

### Reporting
- FR-4.1: HR can view leave usage by department/location/employee
- FR-4.2: Trend analysis (usage over time)
- FR-4.3: Public holiday impact on leave balance
- FR-4.4: Export reports to CSV/PDF (future)

---

## Non-Functional Requirements

### Performance
- NFR-1.1: API response time < 500ms for 95% of requests
- NFR-1.2: Database queries optimized with appropriate indexing
- NFR-1.3: Frontend build size < 500KB (gzipped)

### Security
- NFR-2.1: All endpoints require authentication (except login/register)
- NFR-2.2: Password hashing with PBKDF2 (Django default)
- NFR-2.3: CORS properly configured for frontend domain
- NFR-2.4: SQL injection and XSS protection via ORM and React
- NFR-2.5: Token blacklist on logout

### Reliability
- NFR-3.1: 99.5% uptime SLA
- NFR-3.2: Database backups daily
- NFR-3.3: Error logging and monitoring (future)

### Scalability
- NFR-4.1: Support 10,000+ users
- NFR-4.2: Support 1,000+ concurrent requests
- NFR-4.3: Multi-region deployment (future)

### Compliance
- NFR-5.1: Complete audit trail of all leave actions
- NFR-5.2: Data retention per company policy (future)
- NFR-5.3: GDPR compliance for EU users (future)

---

## Business Rules

### Leave Balance
1. Default annual allocation: 96 hours (12 days at 8h/day)
2. Allocation resets on anniversary or custom date
3. HR can adjust balances (e.g., sign-on bonus, penalty)
4. No negative balances (request must not exceed available)
5. Unused hours may carry over (configurable, future)

### Request Submission
1. Minimum notice period: None currently (configurable future)
2. Cannot request more hours than current balance
3. Cannot request for past dates (except same-day emergency)
4. Category must be defined (not custom text)
5. Request once submitted cannot be edited (delete/resubmit)

### Approval Process
1. Employees submit to their department manager
2. Managers have up to 2 business days to respond
3. Escalation if no response (future)
4. Rejection includes mandatory reason/notes
5. Approved requests are locked (cannot be modified)

### Public Holidays
1. Defined per entity and location
2. Automatically excluded from leave calculations
3. Non-working days (weekends) also excluded
4. Affects leave hour calculations in request validation

---

## Data Model Highlights

### Key Entities
- **User:** Custom AbstractUser with roles and onboarding flags
- **Entity:** Company/subsidiary
- **Location:** Office with timezone
- **Department:** Org unit
- **DepartmentManager:** Manager assignment junction
- **LeaveCategory:** Leave type definition
- **LeaveBalance:** User's annual allocation tracking
- **LeaveRequest:** Individual leave request with full lifecycle
- **PublicHoliday:** Non-working day definition
- **Notification:** In-app notification records
- **AuditLog:** Complete action history

### Key Relationships
- User → Entity/Location/Department (via onboarding)
- Department → Location → Entity (hierarchy)
- DepartmentManager links User (manager) to Department
- LeaveRequest belongs to User, references LeaveCategory
- LeaveBalance tracks LeaveRequest impact on hours

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| User onboarding completion | > 95% | TBD |
| Leave request approval time | < 2 business days | TBD |
| System uptime | > 99.5% | TBD |
| API response time (p95) | < 500ms | TBD |
| Frontend load time | < 3s | TBD |

---

## Known Issues & Limitations

1. React Query installed but unused (migration planned)
2. Approvals and Admin pages are stubs awaiting full implementation
3. Mobile responsiveness limited (fixed 256px sidebar)
4. No error boundary component in React
5. WebSocket real-time updates not implemented
6. Email notifications not implemented (in-app only)
7. Multi-level approval chain not yet supported
8. Leave request editing not allowed (by design, future enhancement)

---

## Deployment Architecture

### Docker Services
- **db:** PostgreSQL 16 (port 5432)
- **backend:** Gunicorn + Django (port 8000)
- **frontend:** Vite dev server (port 5173)

### Environment Setup
- Database migrations run on backend startup
- Demo data seeded for development
- CORS configured for frontend domain
- JWT token settings configurable via settings.py

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-27 | Initial project documentation |

