# Planning Report: ManagerTicket Enhancement

**Date**: 2025-02-05
**Planner**: planner agent
**Plan**: `/home/silver/test-leave/plans/260205-2051-manager-ticket-enhancement/`

## Executive Summary

Created comprehensive implementation plan for two ManagerTicket enhancements:
1. **Deny Approved Requests** - Allow approvers to deny previously approved leave requests within 24-hour window
2. **Approve Reason** - Add optional comment field when approving requests

**Total Effort**: 8 hours across 4 phases

## Key Findings

### Existing Infrastructure
- `approver_comment` field already exists in `LeaveRequest` model
- `approve_leave_request()` service already accepts `comment` parameter
- `LeaveRequestApproveSerializer` has `comment` field
- **Gap**: Approve view doesn't validate serializer or use comment

### Implementation Strategy
1. **Minimal backend changes** - mostly connecting existing pieces
2. **Focus on time constraint logic** - 24-hour cutoff validation
3. **Balance restoration** - critical when denying approved requests
4. **UI enhancement** - enable buttons, add textareas, show time remaining

## Technical Approach

### Phase 01: Backend - Deny Approved (3h)
- Extend `reject_leave_request()` to handle APPROVED status
- Add `can_deny_approved_request()` helper for 24h check
- Restore balance atomically when rejecting approved
- Update audit log with new action type

### Phase 02: Backend - Approve Reason (1.5h)
- Add serializer validation to approve view
- Pass comment to service method
- Already stored in `approver_comment` field

### Phase 03: Frontend UI (2.5h)
- Add `approveReason` state
- Create `canDenyApproved()` and `getTimeRemaining()` helpers
- Update button enable/disable logic
- Add TextArea to approve modal
- Display approver comment in detail view

### Phase 04: Testing (1h)
- Unit tests for new backend methods
- Integration tests for balance restoration
- Manual E2E testing checklist

## Files to Modify

**Backend:**
- `/home/silver/test-leave/leaves/services.py`
- `/home/silver/test-leave/leaves/views/requests/approve.py`
- `/home/silver/test-leave/leaves/views/requests/reject.py`

**Frontend:**
- `/home/silver/test-leave/frontend/src/pages/ManagerTicket.jsx`
- `/home/silver/test-leave/frontend/src/api/dashboardApi.js`

**Tests:**
- `/home/silver/test-leave/leaves/tests/test_requests.py`

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Balance not restored | High | Transaction + select_for_update() |
| Timezone issues | Medium | Django timezone utilities |
| API breaking changes | Low | Comment optional, backward compatible |

## Success Criteria

- [ ] Can deny approved requests when > 24h before start
- [ ] Cannot deny when < 24h (clear error message)
- [ ] Balance restored correctly after denying approved
- [ ] Can approve with optional comment
- [ ] Comment displayed in ticket detail
- [ ] All tests pass
- [ ] No regressions in existing functionality

## Next Steps

1. Review and approve plan
2. Delegate to implementation agent
3. Execute phases sequentially
4. Update documentation upon completion

## Unresolved Questions

None - all requirements clear from user specification.

## Plan Files

- `plan.md` - Overview and summary
- `phase-01-backend-deny-approved-requests.md` - Detailed backend implementation
- `phase-02-backend-approve-reason.md` - Approve comment integration
- `phase-03-frontend-ui-changes.md` - Frontend component updates
- `phase-04-testing.md` - Testing strategy and checklist
