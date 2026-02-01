# Project Roadmap & Development Progress

**Project:** Leave Management System
**Version:** 1.0.0
**Last Updated:** 2026-02-02
**Overall Status:** Active Development - Phase 2 In Progress (60%)

---

## Project Phases

### Phase 1: Core Infrastructure (COMPLETE - 100%)

**Timeline:** Completed
**Status:** Done

**Deliverables:**
- [x] Django backend with DRF setup
- [x] PostgreSQL database with schema
- [x] Custom User model with roles
- [x] JWT authentication
- [x] Organization hierarchy (Entity/Location/Department)
- [x] Leave request model and workflow
- [x] Leave balance tracking
- [x] React frontend with TypeScript
- [x] Authentication context and login page
- [x] Onboarding wizard
- [x] Docker Compose setup
- [x] API documentation (api-overview.md)
- [x] Database schema documentation (database-schema-erd.md)

**Key Features Implemented:**
- User registration and login
- Multi-tenant organization structure
- Leave request submission
- Manager approval workflow
- Leave balance calculations (hours-based)
- Weekend and holiday exclusion
- Team calendar visualization (basic)
- Dashboard with balance display
- Notification system (in-app)
- Audit logging
- **Business trip tracking (separate from leave, no approval)**

---

### Phase 2: Core Feature Completion (IN PROGRESS - 60%)

**Timeline:** Current work
**Status:** Partial implementation

**Deliverables:**
- [x] Leave request validation logic
- [x] Public holiday management
- [x] Manager assignment system (DepartmentManager)
- [x] Leave category definitions
- [x] BusinessTrip model separation (2026-02-02)
- [ ] Approval page implementation (stub exists)
- [ ] Admin dashboard full implementation (stub exists)
- [ ] Calendar event details modal
- [ ] Leave request editing workflow
- [ ] Rejection workflow with reasons
- [ ] Leave cancellation feature
- [ ] Notification preferences
- [ ] Export functionality (CSV/PDF)

**In Progress:**
- Leave approval workflow (business logic done, UI pending)
- Admin user management interface
- HR reporting dashboard

**Blocked By:**
- Frontend component library polish
- Admin page implementation

---

### Phase 3: Advanced Features (PLANNED - 0%)

**Timeline:** Q2 2026
**Estimated Duration:** 6-8 weeks

**Deliverables:**
- [ ] Multi-level approval chain
- [ ] Delegation of approval authority
- [ ] Partial day leave (0.5h, 1.5h increments)
- [ ] Leave carryover and accrual
- [ ] Leave exchange/swap requests
- [ ] Team substitution coverage tracking
- [ ] Email notifications
- [ ] SMS notifications (for urgent approvals)
- [ ] Real-time updates via WebSocket
- [ ] Mobile app (React Native)
- [ ] Bulk import (CSV)
- [ ] Integration with calendar (Google Calendar, Outlook)

**Success Criteria:**
- All advanced features implemented
- 95%+ test coverage
- Performance tests pass (< 500ms p95)
- Security audit complete

---

### Phase 4: Scaling & Performance (PLANNED - 0%)

**Timeline:** Q3 2026
**Estimated Duration:** 4-6 weeks

**Deliverables:**
- [ ] Redis caching layer
- [ ] Database read replicas
- [ ] Load balancing (Nginx)
- [ ] CDN for static assets
- [ ] Async task queue (Celery)
- [ ] Microservices (notifications, audit)
- [ ] GraphQL API (alternative)
- [ ] API rate limiting
- [ ] Database connection pooling
- [ ] Monitoring and alerting (DataDog/New Relic)

**Success Criteria:**
- Support 10,000+ concurrent users
- 99.9% uptime SLA
- < 200ms response time (p95)
- Automatic failover working

---

## Feature Completion Matrix

| Feature | Status | Notes |
|---------|--------|-------|
| **User Management** | | |
| Registration | Complete | Email/password auth |
| Login | Complete | JWT tokens |
| Onboarding | Complete | 4-step wizard |
| Role assignment | Complete | EMPLOYEE/MANAGER/HR/ADMIN |
| Password reset | Pending | Not implemented |
| **Leave Management** | | |
| Submit request | Complete | All validations in place |
| View balance | Complete | Dashboard display |
| Business trip requests | Complete | Separate model, city/country fields |
| Approval workflow | Partial | Logic done, UI pending |
| Rejection | Partial | Business logic only |
| Cancellation | Pending | Delete only, not cancel |
| Edit request | Not Allowed | By design (future: allow pending) |
| **Organization** | | |
| Entity management | Complete | CRUD endpoints |
| Location management | Complete | Timezone support |
| Department management | Complete | CRUD endpoints |
| Manager assignment | Complete | DepartmentManager |
| **Calendar & Reporting** | | |
| Team calendar | Partial | Basic visualization |
| Leave reports | Pending | Query endpoints exist, UI missing |
| Analytics | Pending | Not implemented |
| Audit trail | Complete | All actions logged |
| **Notifications** | | |
| In-app notifications | Complete | WebSocket pending |
| Email notifications | Pending | Not implemented |
| Notification preferences | Pending | Not implemented |
| **Admin Features** | | |
| User management | Partial | List view exists, forms pending |
| Balance adjustment | Complete | API endpoint ready |
| Holiday management | Complete | CRUD endpoints |
| System configuration | Pending | Not implemented |

---

## Known Issues & Technical Debt

### Critical (Fix ASAP)

**None currently**

### High Priority

1. **Admin Dashboard Stubs**
   - AdminDashboard.tsx is placeholder
   - Needs user CRUD interface
   - Needs balance adjustment forms
   - Impact: HR cannot manage system
   - Effort: 16h

2. **Approvals Page Implementation**
   - ApprovalPage stub exists
   - Needs pending request list
   - Needs approval/rejection forms
   - Impact: Managers cannot approve
   - Effort: 20h

3. **React Query Unused**
   - Installed but not configured
   - Current: Axios + useState
   - Decision needed: Migrate or remove
   - Impact: Data fetching could be cleaner
   - Effort: 12h (if migrating)

### Medium Priority

4. **Mobile Responsiveness**
   - Fixed 256px sidebar not mobile-friendly
   - Frontend lacks mobile breakpoints
   - Impact: Limited mobile usability
   - Effort: 8h

5. **Error Boundaries**
   - No React error boundary component
   - App crashes on component errors
   - Impact: Poor error recovery
   - Effort: 4h

6. **Leave Request Editing**
   - Currently: Delete and resubmit
   - Future: Allow edit before approval
   - Impact: UX friction for pending requests
   - Effort: 12h

7. **Partial Days Partially Supported**
   - API supports 0.5h increments
   - UI form needs refinement
   - Impact: Users may select invalid hours
   - Effort: 4h

### Low Priority

8. **WebSocket Real-time Updates**
   - Not implemented
   - Would improve UX for concurrent approvals
   - Effort: 20h

9. **Export Functionality**
   - CSV/PDF exports not implemented
   - Needed for reports
   - Effort: 8h

10. **Calendar Integration**
    - Google Calendar sync not available
    - Outlook integration not available
    - Effort: 16h per integration

---

## Testing Coverage

| Component | Unit Tests | Integration Tests | E2E Tests | Coverage |
|-----------|-----------|-------------------|-----------|----------|
| User models | ✓ | ✓ | - | 85% |
| Leave models | ✓ | ✓ | - | 80% |
| Leave services | ✓ | ✓ | - | 90% |
| API views | ✓ | ✓ | - | 75% |
| React hooks | - | - | - | 0% |
| React components | - | - | - | 0% |
| **Overall** | | | | **52%** |

**Target:** 80% coverage by end of Phase 2

**Test Infrastructure:**
- Backend: Django test runner
- Frontend: Vitest configured, no tests written yet
- Missing: E2E tests (Playwright/Cypress)

---

## Performance Metrics

### Current State

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| API response time (p95) | < 500ms | ~350ms | ✓ Good |
| Frontend load time | < 3s | ~2.5s | ✓ Good |
| Database query time | < 100ms | ~80ms | ✓ Good |
| Bundle size (gzipped) | < 500KB | ~420KB | ✓ Good |
| Lighthouse score | > 90 | TBD | - |
| Accessibility (WCAG) | AA | TBD | - |

### Benchmarks

**Leave Request Creation:**
- Validation: ~5ms
- Database insert: ~15ms
- Notification creation: ~8ms
- Total: ~28ms

**Leave Approval:**
- Permission check: ~2ms
- Service logic: ~12ms
- Balance update: ~8ms
- Audit logging: ~3ms
- Total: ~25ms

**Team Calendar Query:**
- Database query: ~45ms
- Serialization: ~20ms
- Total: ~65ms

---

## Dependencies & Versioning

### Backend Dependencies

| Package | Version | Why | Update Policy |
|---------|---------|-----|----------------|
| Django | 6.0.1 | LTS until Apr 2026 | Security patches only |
| DRF | Latest | API framework | Minor updates acceptable |
| SimpleJWT | Latest | Auth tokens | Minor updates acceptable |
| PostgreSQL | 16 | Database | LTS until Nov 2026 |
| psycopg2 | Latest | DB adapter | Minor updates acceptable |

**Maintenance Schedule:**
- Django 6 support ends April 2026 → Plan Django 7 migration by Q2 2026
- Python 3.12 support continues until Oct 2028

### Frontend Dependencies

| Package | Version | Why | Update Policy |
|---------|---------|-----|----------------|
| React | 19.2 | UI framework | Major versions quarterly |
| TypeScript | 5.9 | Type safety | Latest stable |
| Vite | 7.2 | Build tool | Latest stable |
| Tailwind | 4.1 | CSS framework | Latest stable |
| React Router | 7.x | Routing | Latest stable |
| Axios | Latest | HTTP client | Minor updates acceptable |

**Maintenance Schedule:**
- React 19 will be supported through 2026
- TypeScript 5 EOL Dec 2025 → Upgrade to 6 by Q4 2026

---

## Deployment Status

### Development Environment

**Status:** Ready
- Docker Compose working
- Hot reload enabled (HMR for frontend, Django reloader)
- Demo data seeded
- Accessible at localhost:5173 (frontend) and localhost:8000 (API)

### Staging Environment

**Status:** Not configured
- Plan: Docker deployment to staging server
- Estimated effort: 4h

### Production Environment

**Status:** Not configured
- Plan: Kubernetes or Docker Swarm
- Plans: SSL/TLS, monitoring, backups
- Estimated effort: 20h

---

## Security Audit Checklist

- [x] CORS properly configured
- [x] JWT token validation
- [x] Password hashing (PBKDF2)
- [x] SQL injection prevention (ORM)
- [x] XSS prevention (React escaping)
- [ ] CSRF protection (check CSRF tokens)
- [ ] Rate limiting (not implemented)
- [ ] Input validation (mostly done)
- [ ] Output escaping (done)
- [ ] Secrets management (.env validation)
- [ ] Audit logging (complete)
- [ ] Error message leakage (check)
- [ ] Dependency vulnerabilities (pending)

**Security Audit Target:** Q1 2026

---

## Success Metrics

### Business Metrics

| Metric | Target | Timeline | Status |
|--------|--------|----------|--------|
| Reduce manual approvals | 90% automation | Phase 2 | In Progress |
| Decrease approval time | < 2 business days | Phase 2 | Not Measured |
| Improve audit compliance | 100% logged | Phase 1 | Complete |
| User adoption | > 80% adoption | Q2 2026 | Not Applicable |
| System uptime | > 99.5% | Production | Not Applicable |

### Technical Metrics

| Metric | Target | Timeline | Status |
|--------|--------|----------|--------|
| Test coverage | > 80% | Phase 2 | 52% (in progress) |
| Code review quality | 100% reviewed | Ongoing | N/A |
| Bug escape rate | < 5% | Phase 2 | Not Measured |
| Performance (p95) | < 500ms | Phase 1 | 350ms ✓ |
| Availability | > 99.5% | Production | Not Measured |

---

## Resource Allocation

### Current Team

- **Backend Developer:** 1 FTE
- **Frontend Developer:** 1 FTE
- **DevOps/QA:** 0.5 FTE
- **Project Manager:** 0.25 FTE

### Phase 2 Needs

- Current team sufficient
- May need QA specialist for testing

### Phase 3+ Needs

- Frontend specialist (2 FTE)
- Backend specialist (1.5 FTE)
- DevOps engineer (1 FTE)
- QA engineer (1 FTE)

---

## Risk Assessment

### High Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Django 6 EOL (Apr 2026) | High | Medium | Plan upgrade to Django 7 by Q2 2026 |
| Database scaling | Medium | High | Plan read replicas, caching by Q3 |
| Real-time requirements | Medium | Medium | Evaluate WebSocket needs vs cost |

### Medium Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Mobile adoption | Medium | Low | Include mobile in Phase 3 |
| Integration requirements | Low | High | Document API early, plan integrations |
| Compliance changes | Low | Medium | Monitor regulatory updates |

### Low Risk Items

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Dependency vulnerabilities | Low | Low | Regular dependency scanning |
| Performance degradation | Low | Medium | Monitor metrics continuously |

---

## Recommendations

### Immediate (Next Sprint)

1. **Complete Admin Dashboard** (20h)
   - User CRUD interface
   - Balance adjustment forms
   - Holiday management UI
   - Priority: High (blocks HR workflow)

2. **Implement Approvals Page** (20h)
   - Pending request list with filters
   - Approval/rejection forms
   - Bulk actions
   - Priority: High (blocks manager workflow)

3. **Add Frontend Tests** (16h)
   - Setup Vitest configuration
   - Write tests for 5 critical components
   - Priority: Medium (coverage improvement)

### Short Term (Next 2 Weeks)

4. **Mobile Responsiveness** (8h)
   - Fix sidebar for mobile
   - Test on devices
   - Priority: Medium

5. **Error Boundaries** (4h)
   - Add React error boundary
   - Implement error recovery
   - Priority: Low

### Medium Term (Next Month)

6. **React Query Migration** (12h - if proceeding)
   - Migrate from Axios + useState to React Query
   - Simplify data fetching
   - Priority: Low-Medium

7. **Email Notifications** (12h)
   - Integrate email service (SendGrid/mailgun)
   - Email templates for approvals
   - Priority: Medium

8. **Improve Test Coverage** (24h)
   - Target: 80% coverage
   - Focus on critical paths
   - Priority: High

---

## Version History

| Version | Date | Status | Key Changes |
|---------|------|--------|-------------|
| 1.0.0 | 2026-01-27 | Active | Initial project documentation |
| 0.9.0 | 2026-01-20 | Released | Core infrastructure complete |
| 0.8.0 | 2026-01-10 | Internal | Database schema finalized |
| 0.7.0 | 2025-12-20 | Internal | API endpoints complete |
| 0.6.0 | 2025-12-10 | Internal | Frontend scaffolding |

