# Project Overview & Product Development Requirements

**Last Updated:** 2026-02-07 | **Version:** 1.1.0

---

## Executive Summary

The Leave Management System is a comprehensive web application designed to streamline employee leave request submission, manager approval workflows, and organizational leave balance tracking. It supports multi-tenant organizations with complex hierarchies (Entity → Location → Department), role-based access control, and dynamic leave allocation based on years of service.

**Current Status:** Phase 1 Complete (100%), Phase 2 In Progress (70%)

---

## Business Context

### Problem Statement

Traditional leave management relies on spreadsheets, email chains, and manual approval processes, leading to:
- Inconsistent leave balance tracking
- Delayed approval workflows
- Difficulty in generating organizational leave analytics
- Lack of audit trail for compliance
- No visibility into team availability

### Solution

A centralized, web-based platform providing:
- Real-time leave request tracking
- Automated approval workflows
- Accurate balance calculations
- Complete audit trails
- Team calendar visibility

---

## Target Users

| Role | Responsibility | Access Level |
|------|-----------------|--------------|
| **EMPLOYEE** | Submit leave requests, view balance, see team calendar | Basic |
| **MANAGER** | Approve/reject team requests, view team calendar/reports | Standard |
| **HR/ADMIN** | User management, balance adjustments, org structure, system config | Full |
| **SYSTEM ADMIN** | Configuration, security, backup/restore | Full |

---

## Core Features

### 1. Authentication & Authorization
- **Feature ID:** AUTH-001
- **Status:** Complete
- **Requirements:**
  - Email-based registration and login
  - JWT token-based authentication with refresh mechanism
  - Role-based access control (EMPLOYEE/MANAGER/HR/ADMIN)
  - Password change on first login (security)
  - Approver-relationship-based permissions (non-role-based)
  - Token blacklist on logout

### 2. Organizational Structure
- **Feature ID:** ORG-001
- **Status:** Complete
- **Requirements:**
  - Multi-tenant support via Entity → Location → Department hierarchy
  - 33 timezone options per location
  - Manager assignment to departments
  - Support for multiple managers per department
  - Department-based permission scoping

### 3. Leave Request Submission
- **Feature ID:** LEAVE-001
- **Status:** Complete
- **Requirements:**
  - Submit leave requests with category and date range
  - Support for partial days (0.5h, 1.0h, 1.5h increments)
  - Automatic working day calculation (Mon-Fri, 8h/day)
  - Holiday exclusion from calculations
  - Attachment support (documents/notes)
  - Automatic validation against available balance
  - Overlap detection with existing requests
  - Request status: PENDING → APPROVED/REJECTED/CANCELLED

### 4. Leave Balance Management
- **Feature ID:** LEAVE-002
- **Status:** Complete (with dynamic allocation)
- **Requirements:**
  - Four leave types: EXEMPT_VACATION, NON_EXEMPT_VACATION, EXEMPT_SICK, NON_EXEMPT_SICK
  - Annual balance allocation per leave type
  - Dynamic EXEMPT_VACATION allocation by years of service:
    - Year 1: Prorated by month (8h/month × months worked)
    - Years 2-5: 80 hours
    - Years 6-10: 120 hours
    - Years 11-15: 160 hours
    - Years 16+: 200 hours
  - YoS calculated as floor((ref_date - join_date).days / 365.25) + 1
  - Reference date = Jan 1 of balance year
  - Manual balance adjustments by HR
  - Balance history tracking
  - Support for carryover policies (future)

### 5. Approval Workflow
- **Feature ID:** LEAVE-003
- **Status:** Complete
- **Requirements:**
  - Approver assignment via self-referential relationship
  - Manager approval/rejection of team member requests
  - Approval requires approver-employee relationship (no role bypass)
  - 24-hour rejection rule for approved leaves
  - Atomic approval/rejection with automatic balance deduction/restoration
  - Rejection reason capture
  - Automatic notifications on approval/rejection

### 6. Public Holidays Management
- **Feature ID:** LEAVE-004
- **Status:** Complete
- **Requirements:**
  - Multi-scope holiday support: Global → Entity → Location (priority order)
  - Automatic exclusion from leave calculations
  - Holiday management by HR/Admin
  - Support for yearly holiday configuration

### 7. Team Calendar & Visibility
- **Feature ID:** CALENDAR-001
- **Status:** Complete
- **Requirements:**
  - Entity-level calendar visibility (all employees in same entity)
  - Bidirectional approver-subordinate visibility
  - Color-coded visualization of leave types
  - Drag-to-create leave requests
  - Team member availability overview
  - Manager-level team calendar access
  - Holiday scoping: Global → Entity → Location (cascading priority)

### 8. Notifications
- **Feature ID:** NOTIFY-001
- **Status:** Complete (In-app polling)
- **Requirements:**
  - In-app notifications for leave requests
  - Notifications for approvals/rejections
  - Unread count tracking
  - Mark as read functionality
  - 30-second polling (future: WebSocket)

### 9. Business Trips
- **Feature ID:** BUSINESS-001
- **Status:** Complete
- **Requirements:**
  - Business trip request submission
  - Trip dates and notes
  - Overlap detection with leaves
  - Trip cancellation capability
  - Audit trail

### 10. Reporting & Analytics
- **Feature ID:** REPORT-001
- **Status:** In Progress
- **Requirements:**
  - Department-level leave reports for managers
  - Entity-wide analytics for HR
  - Approved leave export (CSV)
  - Leave utilization dashboards
  - Trend analysis

### 11. Audit & Compliance
- **Feature ID:** AUDIT-001
- **Status:** Complete
- **Requirements:**
  - Complete audit trail of all actions
  - User attribution for each action
  - Timestamp recording
  - Action type tracking
  - Reason/notes capture

---

## Non-Functional Requirements

| Requirement | Specification |
|-------------|--------------|
| **Performance** | API response < 500ms for 99th percentile, support 10k concurrent users |
| **Availability** | 99.5% uptime, automated backups daily |
| **Security** | HTTPS only, HSTS, secure cookies, rate limiting, input validation |
| **Scalability** | Horizontal scaling via Docker, support multiple backend instances |
| **Data Integrity** | PostgreSQL transactions, Decimal precision for financial data |
| **Compliance** | GDPR-compatible audit trails, data retention policies |
| **Accessibility** | WCAG 2.1 AA standard, keyboard navigation support |
| **Browser Support** | Chrome, Firefox, Safari (latest 2 versions), Edge |

---

## User Stories

### Story 1: Employee Submits Leave Request
**As an** employee
**I want to** submit a leave request for specific dates
**So that** my manager can approve my time off

**Acceptance Criteria:**
- [ ] Form accepts date range and leave category
- [ ] System validates against available balance
- [ ] Request shows in pending status
- [ ] Manager receives notification
- [ ] Employee sees confirmation message

### Story 2: Manager Approves Leave Request
**As a** manager
**I want to** approve or reject team member leave requests
**So that** I can control team availability

**Acceptance Criteria:**
- [ ] Managers see only their team's requests
- [ ] Approval/rejection forms are clear and simple
- [ ] Balance is automatically deducted on approval
- [ ] Employee is notified of decision
- [ ] Request can't be rejected within 24 hours of approval

### Story 3: HR Adjusts Leave Balance
**As an** HR administrator
**I want to** adjust employee leave balances
**So that** I can correct errors or grant special leaves

**Acceptance Criteria:**
- [ ] HR can manually adjust any employee's balance
- [ ] Changes are logged in audit trail
- [ ] Employee is notified of adjustments
- [ ] Previous balance is preserved in history

### Story 4: Employee Views Team Calendar
**As an** employee
**I want to** see my team's leave on a calendar
**So that** I know when colleagues are unavailable

**Acceptance Criteria:**
- [ ] Calendar shows approved leaves only
- [ ] Leaves are color-coded by type
- [ ] Shows all employees in same entity
- [ ] Shows user's assigned approver (bidirectional visibility)
- [ ] Shows user's direct subordinates (for managers)
- [ ] Filter options available (team, type)
- [ ] Drag-to-create new leave requests
- [ ] Holidays scoped by location (with global fallback)

---

## Technical Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 + TypeScript, Vite, Ant Design, Axios |
| **Backend** | Django 6.0 + DRF, SimpleJWT, PostgreSQL 16 |
| **Infrastructure** | Docker, Docker Compose, Gunicorn |
| **Testing** | pytest (backend), Jest/Vitest (frontend - future) |
| **Deployment** | Docker containers, automated CI/CD (planned) |

### Architecture Pattern

```
User (Browser)
    ↓
React Frontend (Vite)
    ↓
Axios + JWT Auth
    ↓
Django REST API (Port 8000)
    ↓
PostgreSQL 16 (Port 5432)
    ↓
Redis (Future - caching, sessions)
```

### Database Design

- **Entity Model:** Custom User with roles, approver FK, join_date
- **Organizational:** Entity → Location → Department + DepartmentManager M2M
- **Leaves:** LeaveCategory, LeaveBalance (Decimal), LeaveRequest, PublicHoliday
- **Core:** Notification, AuditLog
- **Transactions:** Atomic operations for approval/rejection

---

## Acceptance Criteria & Success Metrics

### Functional Criteria
- All core features (AUTH, ORG, LEAVE, APPROVAL, CALENDAR) fully functional
- Zero critical bugs in production
- All API endpoints tested and documented
- 80%+ code coverage (backend)

### Performance Criteria
- API response time < 500ms (99th percentile)
- Page load time < 3 seconds
- Support 100+ concurrent users without degradation
- Database query optimization (no N+1 queries)

### User Experience Criteria
- Onboarding completion > 95% for new users
- Leave request submission < 2 minutes
- Approval workflow < 30 seconds
- Zero confusion on balance calculations

### Operational Criteria
- Automated backup and restore procedures
- Database migration scripts for version upgrades
- Monitoring and alerting for system health
- Documentation for deployment and troubleshooting

---

## Project Phases

### Phase 1: Core Platform (COMPLETE - 100%)
- Authentication & Authorization
- User & Organizational Management
- Leave Request Submission
- Leave Balance Management
- Approval Workflow
- Public Holidays
- Basic Team Calendar

**Deliverables:**
- Working frontend and backend
- Basic API endpoints
- Database schema
- Demo data generation

### Phase 2: Features & Polish (IN PROGRESS - 70%)
- Advanced Reporting & Analytics
- Business Trip Management
- Enhanced Notifications (WebSocket)
- Export Functionality
- Mobile Responsiveness
- Performance Optimization
- Comprehensive Testing

**Current Progress:**
- Business trips: Complete
- Notifications: In-app polling (WebSocket pending)
- Export: CSV for approved leaves
- Testing: Core features tested, frontend tests needed
- Mobile: Basic responsive design

### Phase 3: Enterprise Features (PLANNED)
- Role-based reporting dashboards
- Advanced analytics (ML-based insights)
- Integration APIs for HRIS/ERP
- Single Sign-On (SAML/OAuth)
- Bulk operations (import/export users, balance adjustments)
- Custom leave types per entity
- Carryover policy management
- Email notifications integration
- SMS alerts
- Calendar export (ICS/iCal)

**Timeline:** Q2-Q3 2026

### Phase 4: Scale & Optimization (FUTURE)
- Redis caching layer
- Elasticsearch for leave history search
- WebSocket real-time updates
- GraphQL API alternative
- Mobile app (iOS/Android)
- AI-based approval recommendations

**Timeline:** Q4 2026+

---

## Dependencies & Constraints

### Technical Constraints
- PostgreSQL 16 requirement (not compatible with earlier versions)
- Python 3.12+ for backend (F-strings, pattern matching)
- React 19+ for frontend hooks
- Docker for all environments

### Business Constraints
- Multi-tenant support mandatory (Entity hierarchy)
- Decimal precision required for leave hours
- Approver-based permissions (not role-based approval)
- Years of service dynamic allocation (no hardcoded values)

### External Dependencies
- PostgreSQL database server
- SMTP server (future email notifications)
- S3 or file storage (attachment uploads)

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Database scaling with large orgs | High | Medium | Partition by entity, optimize queries |
| Concurrent approval race conditions | High | Low | Atomic transactions, pessimistic locking |
| Data loss | High | Very Low | Daily backups, replication |
| Authentication bypass | High | Very Low | Regular security audits, JWT best practices |
| Performance degradation | Medium | Medium | Caching layer, query optimization |
| Integration complexity | Medium | Medium | Clear API contracts, versioning |

---

## Roadmap Timeline

```
2026-01-27: Phase 1 Complete (Auth, Core Leave, Approval)
2026-02-07: Phase 2 Milestone 1 (Business Trips, Export)
2026-03-15: Phase 2 Complete (Full Testing, Polish)
2026-04-30: Phase 3 Start (Enterprise Features)
2026-06-30: Phase 3 Mid-Check
2026-09-30: Phase 3 Complete / Phase 4 Planning
```

---

## Success Definition

The project is successful when:

1. **Functionality:** All Phase 1 & 2 features working without critical bugs
2. **Adoption:** 90%+ of employees submit leave through the system within 30 days
3. **Performance:** 99th percentile API response < 500ms, zero database locks
4. **Reliability:** 99.5% uptime over 3-month period
5. **Satisfaction:** NPS > 40 from user surveys
6. **Compliance:** 100% audit trail accuracy, GDPR-ready data handling
7. **Maintenance:** < 5 bugs per month reported by users

---

## Next Steps

1. **Immediate (Week 1):** Finalize Phase 2 testing, fix critical bugs
2. **Short Term (Month 1):** Deploy to production, monitor performance, gather user feedback
3. **Medium Term (Month 2-3):** Plan Phase 3 features based on feedback, staff hiring if needed
4. **Long Term (Month 4+):** Execute Phase 3 roadmap, plan enterprise features

---

*For detailed implementation guidance, see [code-standards.md](./code-standards/index.md) and [system-architecture.md](./system-architecture.md).*
