# Phase 01: Backend - Deny Approved Requests

**Priority**: P2
**Status**: pending
**Effort**: 3h

## Context Links
- Parent: [plan.md](./plan.md)
- Model: `/home/silver/test-leave/leaves/models.py`
- Service: `/home/silver/test-leave/leaves/services.py`
- Reject View: `/home/silver/test-leave/leaves/views/requests/reject.py`

## Overview
Enable approvers to deny/reject previously approved leave requests, with a 24-hour cutoff constraint before leave start date. When denying an approved request, the deducted balance must be restored.

## Key Insights

### Current Behavior
- `reject_leave_request()` in services.py only accepts PENDING status (line 140)
- Approving deducts balance (line 104)
- No mechanism to restore balance when approved request is rejected

### Required Changes
1. Extend `reject_leave_request()` to handle APPROVED status
2. Add 24-hour time constraint validation
3. Restore balance when rejecting approved request
4. Update audit log for new action type
5. Update reject view to handle approved requests

## Requirements

### Functional
- Approver can reject APPROVED requests if > 24h before start_date
- Balance is restored (used_hours decreased by request total_hours)
- Audit log tracks rejection of approved request
- Proper error messages for time constraint violations

### Non-Functional
- Transaction atomicity for balance restoration
- Timezone-aware date/time calculations
- Existing notification flow for rejections

## Architecture

```
User Action: Reject Approved Request
        ↓
LeaveRequestRejectView (POST)
        ↓
Validate: approver permission
        ↓
Validate: time constraint (> 24h before start)
        ↓
LeaveApprovalService.reject_approved_request()
        ↓
Transaction:
  - Update status: APPROVED → REJECTED
  - Restore balance: used_hours -= total_hours
  - Set rejection_reason, approved_by, approved_at
  - Create audit log
        ↓
Notification: create_leave_rejected_notification()
        ↓
Response: { id, status }
```

## Related Code Files

### Files to Modify

**`/home/silver/test-leave/leaves/services.py`**
- Add new method `reject_approved_request(leave_request, approver, reason)`
- Add helper method `can_deny_approved_request(leave_request)` for time check
- Or extend existing `reject_leave_request()` to handle both statuses

**`/home/silver/test-leave/leaves/views/requests/reject.py`**
- Remove status restriction or handle both PENDING and APPROVED
- Add time constraint error handling

## Implementation Steps

1. **Add time constraint validation helper** in `services.py`:
   ```python
   @staticmethod
   def can_deny_approved_request(leave_request):
       """Check if approved request can be denied (> 24h before start)"""
       from django.utils import timezone
       cutoff = leave_request.start_date - timezone.timedelta(hours=24)
       return timezone.now() < cutoff
   ```

2. **Extend `reject_leave_request()`** or create new method:
   - Check if status is PENDING or APPROVED
   - If APPROVED, validate time constraint
   - If APPROVED, restore balance within transaction
   - Update audit log with appropriate action type

3. **Update reject view** in `views/requests/reject.py`:
   - Remove PENDING-only validation
   - Add time constraint check
   - Return appropriate error messages

4. **Update audit log creation**:
   - Use 'REJECT_APPROVED' action for approved→rejected
   - Include balance restoration in new_values

5. **Test manually**:
   - Create request, approve it
   - Try to reject when > 24h before start (should succeed)
   - Try to reject when < 24h before start (should fail)
   - Verify balance restored

## Todo List

- [ ] Add time constraint helper method to services.py
- [ ] Extend reject method to handle APPROVED status with balance restoration
- [ ] Update reject view to allow APPROVED status
- [ ] Add time constraint validation in view
- [ ] Update audit logging for reject approved action
- [ ] Manual testing with different time scenarios
- [ ] Verify notification still sent for approved rejections

## Success Criteria

- Can reject approved request when > 24h before start
- Cannot reject approved request when < 24h before start (clear error)
- Balance correctly restored after rejecting approved request
- Audit log captures rejection of approved request
- Existing PENDING→REJECTED flow unchanged
- Notification sent to employee

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Balance not restored | High | Use transaction, test with explicit balance queries |
| Timezone mismatch | Medium | Use Django timezone, test with different timezones |
| Race condition on balance | Low | select_for_update() on balance query |
| Notification not sent | Low | Verify notification service call |

## Security Considerations

- Only assigned approver can reject (existing check maintained)
- Time constraint enforced server-side (cannot bypass)
- Balance restoration atomic with status change
- Audit trail complete

## Next Steps

- Proceed to [Phase 02](./phase-02-backend-approve-reason.md)
