# Development Roadmap

**Last Updated:** 2026-02-08 | **Version:** 1.1.2

---

## Project Timeline Overview

```
Phase 1: Core Platform         Jan 2026    100% Complete
Phase 2: Features & Polish     Jan-Mar     75% In Progress
Phase 3: Enterprise Features   Apr-Sep     0% Planned
Phase 4: Scale & Optimization  Q4 2026+    0% Future
```

---

## Phase 1: Core Platform (COMPLETE - 100%)

**Timeline:** January 2026 | **Status:** COMPLETE

### Features Delivered

#### 1.1 Authentication & Authorization (100% ✓)
- [x] Email-based registration with validation
- [x] Login with JWT token generation
- [x] Token refresh mechanism (1hr access, 7d refresh)
- [x] Logout with token blacklisting
- [x] Role-based access control (EMPLOYEE, MANAGER, HR, ADMIN)
- [x] Approver-based permissions (self-referential relationship)
- [x] Password change on first login (forced)
- [x] Onboarding wizard (entity/location/department assignment)

**Completion Date:** 2026-01-10
**Test Coverage:** 85%

#### 1.2 User & Organizational Management (100% ✓)
- [x] Custom User model with email authentication
- [x] Entity → Location → Department hierarchy
- [x] 33 timezone options per location
- [x] Department manager assignment (many-to-many)
- [x] User creation/edit by HR/Admin (via Settings modal)
- [x] User import/export functionality
- [x] Role and department assignments
- [x] Onboarding status tracking
- [x] Auto-create all 4 leave balance types on user creation

**Completion Date:** 2026-01-12
**Test Coverage:** 80%

#### 1.3 Leave Request Submission (100% ✓)
- [x] Create leave requests with category and dates
- [x] Support for partial days (0.5, 1.0, 1.5 hour increments)
- [x] Automatic working day calculation (Mon-Fri, 8h/day)
- [x] Holiday exclusion from calculations
- [x] Overlap detection with existing requests
- [x] Request validation against available balance
- [x] Attachment support (document upload)
- [x] Request status tracking (PENDING → APPROVED/REJECTED/CANCELLED)
- [x] User can view own requests
- [x] Cancel pending or approved requests

**Completion Date:** 2026-01-15
**Test Coverage:** 88%

#### 1.4 Leave Balance Management (100% ✓)
- [x] Four leave types (EXEMPT_VACATION, NON_EXEMPT_VACATION, EXEMPT_SICK, NON_EXEMPT_SICK)
- [x] Annual balance allocation per type
- [x] Balance tracking with hour precision (Decimal)
- [x] Manual balance adjustments by HR
- [x] Balance history preservation
- [x] Default balance creation on user registration
- [x] Dynamic EXEMPT_VACATION allocation by years of service:
  - [x] Year 1: Prorated (8h/month)
  - [x] Years 2-5: 80 hours
  - [x] Years 6-10: 120 hours
  - [x] Years 11-15: 160 hours
  - [x] Years 16+: 200 hours

**Completion Date:** 2026-02-05
**Test Coverage:** 82%

#### 1.5 Approval Workflow (100% ✓)
- [x] Approver assignment via self-referential FK
- [x] Manager approval/rejection of team requests
- [x] Approver-based permission validation (no role bypass)
- [x] Atomic approval with balance deduction
- [x] Atomic rejection with balance restoration
- [x] 24-hour rejection rule for approved leaves
- [x] Rejection reason capture
- [x] Automatic notifications on approval/rejection
- [x] Audit trail of all approval actions
- [x] Manager can view only team's requests (scoped by department)

**Completion Date:** 2026-01-18
**Test Coverage:** 90%

#### 1.6 Public Holidays Management (100% ✓)
- [x] Create/edit public holidays
- [x] Multi-scope support: Global → Entity → Location
- [x] Automatic exclusion from working day calculations
- [x] HR/Admin can manage holidays
- [x] Holiday list visible to all users
- [x] Support for recurring holidays (e.g., yearly)

**Completion Date:** 2026-01-16
**Test Coverage:** 75%

#### 1.7 Team Calendar (100% ✓)
- [x] View team's approved leaves on calendar
- [x] Color-coded by leave type
- [x] Filter by team member
- [x] Drag-to-create leave requests
- [x] Department-level scoping
- [x] Month/week view switching
- [x] Mobile-responsive design

**Completion Date:** 2026-01-20
**Test Coverage:** 70%

#### 1.8 Notifications (100% ✓)
- [x] In-app notifications for leave requests
- [x] Notifications for approvals/rejections
- [x] Notification list with pagination
- [x] Mark as read functionality
- [x] Unread count tracking
- [x] 30-second polling mechanism
- [x] Notification badge on header

**Completion Date:** 2026-01-22
**Test Coverage:** 78%

#### 1.9 Audit Logging (100% ✓)
- [x] AuditLog model for all actions
- [x] User, action type, timestamp recording
- [x] Changes JSON field (before/after states)
- [x] Reason/notes capture
- [x] Admin interface for viewing logs
- [x] Query logs by date, user, action

**Completion Date:** 2026-01-19
**Test Coverage:** 85%

#### 1.10 API Documentation (100% ✓)
- [x] drf-spectacular integration (Swagger + ReDoc)
- [x] All endpoints documented
- [x] Request/response schemas defined
- [x] Authentication examples
- [x] Error response documentation

**Completion Date:** 2026-01-25
**Test Coverage:** N/A (auto-generated)

### Phase 1 Summary

**Metrics:**
- Total Features: 10
- Completed: 10 (100%)
- Test Coverage: 82% (backend)
- LOC Delivered: ~1,900 (backend), ~4,000 (frontend)
- Bugs Found & Fixed: 23
- User Acceptance: Approved

---

## Phase 2: Features & Polish (IN PROGRESS - 75%)

**Timeline:** January - March 2026 | **Status:** 75% Complete

### Completed Milestones

#### 2.1 Business Trip Management (100% ✓)
- [x] Create business trip requests
- [x] Specify trip dates and destination
- [x] Trip notes and itinerary
- [x] Overlap detection with leave requests
- [x] Trip status tracking (ACTIVE, CANCELLED)
- [x] Cancel trip functionality
- [x] View trip history
- [x] Audit trail for business trips

**Completion Date:** 2026-01-27
**Status:** Complete
**Test Coverage:** 80%

#### 2.2 Leave Export (100% ✓)
- [x] Export approved leaves as CSV
- [x] Filter by date range, category, user
- [x] Include balance information
- [x] Download functionality in frontend
- [x] Admin interface for batch exports
- [x] Audit log for all exports

**Completion Date:** 2026-02-03
**Status:** Complete
**Test Coverage:** 75%

#### 2.3 Mobile Responsiveness (100% ✓)
- [x] Responsive design for all pages
- [x] Mobile-optimized forms
- [x] Touch-friendly buttons and inputs
- [x] Sidebar collapse on mobile
- [x] Calendar mobile view
- [x] Modal forms responsive

**Completion Date:** 2026-02-01
**Status:** Complete
**Test Coverage:** N/A (manual testing)

### In-Progress Milestones

#### 2.5 Testing & Code Coverage (60% ⚙️)
- [x] Backend unit tests for core services
- [x] API endpoint tests
- [x] Database transaction tests
- [x] Security vulnerability tests
- [ ] Frontend component tests (30% done)
- [ ] E2E tests with Cypress (0% done)
- [ ] Performance load testing (0% done)

**Target Completion:** 2026-02-20
**Current Coverage:** Backend 85%, Frontend 45%

#### 2.6 Performance Optimization (50% ⚙️)
- [x] Database query optimization (select_related, prefetch_related)
- [x] Added necessary database indexes
- [x] API response optimization
- [ ] Frontend bundle size optimization (in progress)
- [ ] Frontend code splitting (planned)
- [ ] Caching strategy (planned)

**Target Completion:** 2026-02-25

#### 2.7 Advanced Reporting (40% ⚙️)
- [x] Approved leave export CSV
- [x] Department-level leave reports
- [ ] Dashboard analytics (in progress)
- [ ] Leave utilization charts (planned)
- [ ] Trend analysis (planned)
- [ ] Custom report builder (planned)

**Target Completion:** 2026-03-10

### Completed Milestones

#### 2.4 Security Hardening - Batch 1 (100% ✓)
- [x] Fix race condition on leave creation (transaction.atomic + select_for_update)
- [x] Fix double-approve/reject race condition (select_for_update on LeaveRequest)
- [x] Replace hardcoded 80h with dynamic YoS calculation for EXEMPT_VACATION
- [x] Implement IDOR protection on leave request detail endpoint
- [x] Add entity-level filtering on HR leave list
- [x] Fix change-password auth (first_login vs normal flow)
- [x] Add negative used_hours floor check on rejection
- [x] Implement safe null handling in balance type detection
- [x] Handle LeaveBalance.DoesNotExist gracefully

**Completion Date:** 2026-02-08
**Status:** Complete
**Test Coverage:** 90%

#### 2.4b Security Hardening - Batch 2 (100% ✓)
- [x] Validate attachment URLs with regex pattern enforcement
- [x] Block cross-year leave requests
- [x] Check entity active status on leave submission
- [x] Fix export OOM vulnerability (10K row cap)
- [x] Harden notification pagination (page_size cap at 100)
- [x] Fix WebP magic bytes validation (full RIFF+WEBP signature)
- [x] Narrow DetailView to RetrieveAPIView (prevent PUT/DELETE)
- [x] Require refresh token on logout endpoint
- [x] Deactivate users on entity soft-delete cascade
- [x] Restrict EntityDeleteImpactView to HR/Admin
- [x] Include user count in deletion impact calculation

**Completion Date:** 2026-02-08
**Status:** Complete
**Test Coverage:** 88%

### Planned Milestones

#### 2.7 WebSocket Notifications (0% 📅)
- [ ] Replace polling with real-time WebSocket
- [ ] Django Channels integration
- [ ] Use Redis as channel layer
- [ ] Frontend Socket.IO client
- [ ] Fallback to polling if WebSocket unavailable

**Target Start:** 2026-02-20
**Target Completion:** 2026-03-05
**Estimated LOC:** 200

#### 2.8 Additional Security Enhancements (0% 📅)
- [ ] CORS security audit
- [ ] Advanced rate limiting per user
- [ ] Input validation tightening
- [ ] SQL injection prevention verification
- [ ] XSS prevention audit
- [ ] CSRF token verification

**Target Start:** 2026-03-01
**Target Completion:** 2026-03-20
**Estimated LOC:** 150

#### 2.9 Documentation Completion (0% 📅)
- [ ] API documentation review
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Code examples and walkthroughs
- [ ] Video tutorials (optional)

**Target Start:** 2026-03-01
**Target Completion:** 2026-03-20

### Phase 2 Blockers & Risks

| Risk | Impact | Status | Mitigation |
|------|--------|--------|-----------|
| Database performance degradation | High | Under monitoring | Add indexes, optimize queries |
| Frontend test coverage lag | Medium | In progress | Allocate dev time to testing |
| Email notification delay | Medium | Blocked | Requires SMTP setup (Phase 3) |
| Concurrent approval race conditions | High | Resolved (v1.1.1) | Used atomic transactions + select_for_update |
| IDOR vulnerabilities | High | Resolved (v1.1.1) | Implemented permission checks |
| Cross-entity access | High | Resolved (v1.1.1) | Added entity-level filtering |
| Input validation gaps | High | Resolved (v1.1.2) | Regex validation + type checking |
| Resource exhaustion (OOM) | High | Resolved (v1.1.2) | Row caps + pagination limits |
| File format validation bypass | Medium | Resolved (v1.1.2) | Magic bytes signature checking |

---

## Phase 3: Enterprise Features (PLANNED - 0%)

**Timeline:** April - September 2026 | **Estimated LOC:** 2,000

### Planned Features

#### 3.1 Email Notifications (Q2 2026)
- [ ] SMTP server integration
- [ ] HTML email templates
- [ ] Leave request emails to approvers
- [ ] Approval/rejection confirmation emails
- [ ] Daily digest of pending requests
- [ ] Notification preferences (opt-in/out)

**Estimated Effort:** 80 hours
**Estimated LOC:** 200

#### 3.2 Role-Based Reporting Dashboards (Q2 2026)
- [ ] Employee dashboard (own balance, requests, approvals)
- [ ] Manager dashboard (team requests, approvals, metrics)
- [ ] HR dashboard (entity-wide analytics, user management)
- [ ] Admin dashboard (system health, audit logs, config)
- [ ] Real-time data refresh
- [ ] Custom date range selection

**Estimated Effort:** 120 hours
**Estimated LOC:** 400

#### 3.3 Advanced Analytics (Q2-Q3 2026)
- [ ] Leave utilization trends
- [ ] Department-level analytics
- [ ] Year-over-year comparison
- [ ] Forecasting (capacity planning)
- [ ] ML-based leave patterns (optional)
- [ ] Export analytics as PDF reports

**Estimated Effort:** 100 hours
**Estimated LOC:** 300

#### 3.4 HRIS/ERP Integration APIs (Q2 2026)
- [ ] REST API for external systems
- [ ] User sync endpoint (create/update from external HR systems)
- [ ] Entity/location/department sync
- [ ] Balance sync
- [ ] OAuth 2.0 authentication for integrations
- [ ] Webhook support for real-time updates

**Estimated Effort:** 110 hours
**Estimated LOC:** 350

#### 3.5 Single Sign-On (Q3 2026)
- [ ] SAML 2.0 support
- [ ] OAuth 2.0 support (Google, Microsoft)
- [ ] LDAP integration (optional)
- [ ] Auto-user provisioning on first login
- [ ] SAML attribute mapping
- [ ] Service provider metadata

**Estimated Effort:** 90 hours
**Estimated LOC:** 250

#### 3.6 Calendar Integrations (Q3 2026)
- [ ] Google Calendar integration
- [ ] Outlook Calendar integration
- [ ] Export leaves as calendar events (ICS/iCal)
- [ ] Two-way sync (optional)
- [ ] Calendar invitation support
- [ ] Availability API for other systems

**Estimated Effort:** 100 hours
**Estimated LOC:** 280

#### 3.7 Bulk Operations (Q3 2026)
- [ ] Bulk user import from CSV
- [ ] Bulk balance adjustments
- [ ] Bulk leave request approval
- [ ] Bulk holiday creation
- [ ] Undo capability for bulk operations
- [ ] Progress tracking and reporting

**Estimated Effort:** 80 hours
**Estimated LOC:** 220

#### 3.8 Custom Leave Types (Q3 2026)
- [ ] Create custom leave types per entity
- [ ] Carryover policies (e.g., 10 hours rollover max)
- [ ] Usage restrictions (e.g., max 5 days per month)
- [ ] Approval workflows per type
- [ ] Template library for common types

**Estimated Effort:** 70 hours
**Estimated LOC:** 200

---

## Phase 4: Scale & Optimization (FUTURE)

**Timeline:** Q4 2026+ | **Status:** Not Started

### Strategic Initiatives

#### 4.1 Infrastructure Scaling
- [ ] Kubernetes deployment (from Docker Compose)
- [ ] Horizontal pod autoscaling
- [ ] Database read replicas
- [ ] CDN for static assets
- [ ] Redis caching layer
- [ ] Elasticsearch for full-text search

#### 4.2 Performance Enhancement
- [ ] Query result caching
- [ ] Background job processing (Celery)
- [ ] Async export generation
- [ ] GraphQL API (alternative to REST)
- [ ] API rate limiting per user
- [ ] Database connection pooling

#### 4.3 Mobile Applications
- [ ] iOS native app (Swift)
- [ ] Android native app (Kotlin)
- [ ] Offline support
- [ ] Push notifications
- [ ] Biometric authentication

#### 4.4 Advanced Features
- [ ] Machine learning for leave predictions
- [ ] Chatbot for leave requests (Slack integration)
- [ ] VR/AR team presence visualization (experimental)
- [ ] Blockchain audit trail (if regulatory required)
- [ ] IoT integration for office occupancy

---

## Milestones & Key Dates

| Milestone | Date | Status |
|-----------|------|--------|
| Phase 1 Complete | 2026-01-27 | ✓ DONE |
| Business Trip Feature | 2026-01-27 | ✓ DONE |
| Export Functionality | 2026-02-03 | ✓ DONE |
| Phase 2 Milestone 1 | 2026-02-07 | ✓ DONE |
| Security Hardening Batch 1 (v1.1.1) | 2026-02-08 | ✓ DONE |
| Security Hardening Batch 2 (v1.1.2) | 2026-02-08 | ✓ DONE |
| Phase 2 Testing Complete | 2026-02-20 | ⚙️ IN PROGRESS |
| Phase 2 Complete | 2026-03-15 | 📅 TARGET |
| Phase 3 Planning | 2026-03-20 | 📅 PLANNED |
| Phase 3 Start | 2026-04-01 | 📅 PLANNED |
| Phase 3 Mid-Check | 2026-06-30 | 📅 PLANNED |
| Phase 3 Complete | 2026-09-30 | 📅 PLANNED |
| Phase 4 Planning | 2026-10-01 | 📅 PLANNED |

---

## Success Criteria

### Phase 2 Success (by 2026-03-15)
- [ ] 95%+ backend test coverage
- [ ] 70%+ frontend test coverage
- [ ] All bugs from Phase 1 fixed
- [ ] Zero critical security issues
- [ ] API response time < 500ms (p99)
- [ ] Page load time < 3 seconds
- [ ] User satisfaction > 4.0/5.0
- [ ] 100% of Phase 1 features stable in production

### Phase 3 Success (by 2026-09-30)
- [ ] Email notifications working
- [ ] Reporting dashboards live
- [ ] HRIS integration in use by 3+ customers
- [ ] SSO supporting 5+ providers
- [ ] 2,000+ daily active users
- [ ] System uptime 99.5%
- [ ] Customer NPS > 45

### Phase 4 Success (by 2026-12-31)
- [ ] Kubernetes deployment active
- [ ] Mobile apps available on App Store / Play Store
- [ ] Support 100k+ daily active users
- [ ] Machine learning models in production
- [ ] Enterprise SLA compliance (99.95% uptime)

---

## Resource Allocation

### Phase 2 (Current)
- Backend Developers: 2 FTE
- Frontend Developers: 1.5 FTE
- QA/Testing: 1 FTE
- DevOps: 0.5 FTE
- **Total:** 5 FTE

### Phase 3 (Planned)
- Backend Developers: 3 FTE
- Frontend Developers: 2 FTE
- Mobile Developers: 2 FTE (iOS/Android)
- QA/Testing: 1.5 FTE
- DevOps: 1 FTE
- **Total:** 9.5 FTE

---

## Dependency Management

### External Dependencies
- PostgreSQL 16 (database)
- Redis (future caching)
- SMTP server (email)
- OAuth providers (Google, Microsoft)
- Kubernetes cluster (future)

### Internal Dependencies
- All Phase 1 features must be stable before Phase 2 starts
- API v1 must be frozen before Phase 3 integration features
- Mobile app development requires stable Phase 2 APIs

---

## Known Issues & Debt

### Technical Debt
| Item | Priority | Effort | Status |
|------|----------|--------|--------|
| Refactor leaves/views.py (922 LOC) | Medium | 40 hours | Backlog |
| Add frontend type definitions | High | 30 hours | Backlog |
| Implement request/response validation | High | 50 hours | In Progress |
| Database connection pooling | Low | 20 hours | Backlog |
| Upgrade Django to 7.0 (future) | Low | 60 hours | Backlog |

### Known Bugs
- 32 pre-existing test failures (unrelated to new code)
- Entity model field mismatch (`name` vs `entity_name`)
- Some frontend components not fully type-checked

---

## Communication & Status

### Status Reports
- Weekly: Development team standup (Monday 10am)
- Bi-weekly: Stakeholder demo (Friday 2pm)
- Monthly: Roadmap review and adjustments

### Feedback Channels
- GitHub Issues for bug reports
- GitHub Discussions for feature requests
- Slack #product-feedback for general feedback

---

*For implementation details, see [code-standards.md](./code-standards/index.md). For current codebase status, see [codebase-summary.md](./codebase-summary.md).*
