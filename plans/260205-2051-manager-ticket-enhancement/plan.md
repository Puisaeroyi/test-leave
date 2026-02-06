---
title: "ManagerTicket Enhancement - Deny Approved Requests & Approve Reason"
description: "Enable denying approved leave requests within 24h window and add approve reason functionality"
status: pending
priority: P2
effort: 8h
branch: main
tags: [frontend, backend, leave-approval, ui-enhancement]
created: 2025-02-05
---

## Overview

Enhancement to ManagerTicket page allowing:
1. **Deny Approved Requests**: Approvers can deny previously approved leave requests if at least 24 hours before leave starts
2. **Approve Reason**: Add optional comment field when approving requests (currently only deny has reason)

## Current State Analysis

**Backend (`leaves/models.py`)**:
- `LeaveRequest` model has `approver_comment` field (line 99) - already exists!
- `rejection_reason` field exists for denials (line 98)
- Status transitions: PENDING → APPROVED/REJECTED

**Backend (`leaves/services.py`)**:
- `approve_leave_request()` accepts `comment` param (line 75) - already stored!
- `reject_leave_request()` only works for PENDING status (line 140)
- `LeaveApprovalService.can_manager_approve_request()` checks approver relationship

**Backend API (`leaves/views/requests/approve.py`)**:
- Approve endpoint does NOT accept comment parameter (line 37-39)
- Uses `LeaveRequestApproveSerializer` but doesn't validate it

**Backend API (`leaves/views/requests/reject.py`)**:
- Reject endpoint requires `reason` (min 10 chars)
- Only works for PENDING status (validated in service layer)

**Frontend (`frontend/src/pages/ManagerTicket.jsx`)**:
- Line 34: `isPending = selectedTicket?.status === "Pending"`
- Lines 290-323: Approve/Deny buttons disabled when `!isPending`
- Lines 331-358: Confirm modal - only deny has TextArea
- `dashboardApi.js`: `approveLeaveRequest()` accepts `comment` param but not used

## Phases

| Phase | Description | Status | Effort |
|-------|-------------|--------|--------|
| [Phase 01](./phase-01-backend-deny-approved-requests.md) | Backend: Deny approved requests with 24h validation | pending | 3h |
| [Phase 02](./phase-02-backend-approve-reason.md) | Backend: Accept and store approve reason | pending | 1.5h |
| [Phase 03](./phase-03-frontend-ui-changes.md) | Frontend: UI enhancements for both features | pending | 2.5h |
| [Phase 04](./phase-04-testing.md) | Testing and validation | pending | 1h |

## Key Dependencies

- None - standalone feature enhancement

## Technical Decisions

### 1. Time Constraint Logic
- **Cutoff Time**: `leave_start_date - 24 hours` (using Django timezone)
- **Validation**: Both frontend (disable button) and backend (enforce)
- **User Feedback**: Show time remaining in UI

### 2. API Changes
- **Approve endpoint**: Add `comment` to request body, use existing serializer
- **Reject endpoint**: Extend to handle APPROVED status with time check

### 3. Status Flow
- Existing: PENDING → APPROVED
- New: APPROVED → REJECTED (with 24h constraint)

### 4. Balance Restoration
- When denying approved request, restore balance (reverse of approve)

## Related Code Files

### Files to Modify
**Backend:**
- `/home/silver/test-leave/leaves/services.py` - Add `deny_approved_request()` method
- `/home/silver/test-leave/leaves/views/requests/approve.py` - Accept comment parameter
- `/home/silver/test-leave/leaves/views/requests/reject.py` - Handle APPROVED status
- `/home/silver/test-leave/leaves/serializers.py` - Ensure approve serializer used

**Frontend:**
- `/home/silver/test-leave/frontend/src/pages/ManagerTicket.jsx` - Major UI changes
- `/home/silver/test-leave/frontend/src/api/dashboardApi.js` - Already supports comment

### Files to Create
- None

### Files to Delete
- None

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Balance not restored on deny | High | Use transaction, test rollback |
| Timezone issues with 24h check | Medium | Use Django timezone utilities |
| UI confusion about when deny is allowed | Low | Clear messaging and disabled state |
| Approve comment not stored | Low | Verify serializer validation |

## Security Considerations

- Only assigned approver can deny (existing permission check)
- 24h cutoff enforced server-side
- Balance restoration atomic with status change
- Audit trail maintained via existing `AuditLog`

## Success Criteria

1. Approved requests show "Deny" button when > 24h before start
2. Deny button disabled with tooltip when < 24h before start
3. Denying approved request restores balance correctly
4. Approve action accepts optional comment
5. Approve comment displayed in ticket detail
6. All actions create proper audit logs
7. Tests pass for new functionality

## Next Steps

1. Execute Phase 01: Backend deny approved requests
2. Execute Phase 02: Backend approve reason
3. Execute Phase 03: Frontend UI changes
4. Execute Phase 04: Testing
