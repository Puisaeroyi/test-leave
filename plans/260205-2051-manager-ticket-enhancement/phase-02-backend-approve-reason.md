# Phase 02: Backend - Approve Reason

**Priority**: P2
**Status**: pending
**Effort**: 1.5h

## Context Links
- Parent: [plan.md](./plan.md)
- Approve View: `/home/silver/test-leave/leaves/views/requests/approve.py`
- Serializer: `/home/silver/test-leave/leaves/serializers.py`
- Service: `/home/silver/test-leave/leaves/services.py`

## Overview
The backend already has infrastructure for approve comments (`approver_comment` field exists, service accepts comment), but the approve endpoint doesn't actually accept or validate the comment parameter. This phase connects the existing pieces.

## Key Insights

### Current State
- `LeaveRequest.approver_comment` field exists (models.py line 99)
- `LeaveApprovalService.approve_leave_request()` accepts `comment` param (services.py line 75)
- `LeaveRequestApproveSerializer` has `comment` field (serializers.py line 177)
- BUT: `LeaveRequestApproveView.post()` does NOT validate serializer or use comment

### Gap Analysis
The approve view at line 37-39 calls the service directly without validating the serializer:

```python
# Current (broken):
approved_request = LeaveApprovalService.approve_leave_request(
    leave_request,
    request.user  # comment parameter not passed!
)
```

## Requirements

### Functional
- Approve endpoint accepts optional `comment` field
- Comment validated (max length 1000)
- Comment stored in `approver_comment` field
- Comment included in audit log

### Non-Functional
- Backward compatible (comment optional)
- Minimal changes required

## Architecture

```
POST /api/v1/leaves/requests/{id}/approve/
{ "comment": "Approved - team coverage confirmed" }
        ↓
LeaveRequestApproveView.post()
        ↓
Validate serializer (comment optional, max 1000)
        ↓
LeaveApprovalService.approve_leave_request(
    leave_request,
    approver=request.user,
    comment=validated_data['comment']  # Now passed!
)
        ↓
Stored in approver_comment field
        ↓
Audit log includes comment
```

## Related Code Files

### Files to Modify

**`/home/silver/test-leave/leaves/views/requests/approve.py`**

Current code (lines 36-40):
```python
# Approve the request (no comment needed)
approved_request = LeaveApprovalService.approve_leave_request(
    leave_request,
    request.user
)
```

Change to:
```python
# Validate request
serializer = LeaveRequestApproveSerializer(data=request.data)
serializer.is_valid(raise_exception=True)

# Approve the request with optional comment
approved_request = LeaveApprovalService.approve_leave_request(
    leave_request,
    request.user,
    comment=serializer.validated_data.get('comment', '')
)
```

## Implementation Steps

1. **Import serializer** in approve.py (if not already imported):
   - `LeaveRequestApproveSerializer` should be available

2. **Add serializer validation** in `post()` method:
   - Validate request data with `LeaveRequestApproveSerializer`
   - Extract validated comment

3. **Pass comment to service**:
   - Get comment from validated data (default to empty string)
   - Pass to `approve_leave_request()`

4. **Verify audit log** includes comment:
   - Service already does this (line 118)

5. **Test**:
   - Approve without comment (should work)
   - Approve with comment (should store)
   - Approve with comment > 1000 chars (should fail validation)

## Todo List

- [ ] Verify LeaveRequestApproveSerializer imported in approve.py
- [ ] Add serializer validation in post() method
- [ ] Pass comment parameter to service method
- [ ] Test approve without comment (backward compatibility)
- [ ] Test approve with comment (stores correctly)
- [ ] Test approve with long comment (validation error)

## Success Criteria

- Can approve without comment (backward compatible)
- Can approve with comment (stored in approver_comment)
- Comment over 1000 chars rejected with validation error
- Comment appears in audit log
- Existing approve tests still pass

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing approve calls | Low | Comment is optional in serializer |
| Frontend not sending comment | None | Comment optional, defaults to empty |

## Security Considerations

- Comment length validated (max 1000 chars)
- No security changes (existing permissions maintained)

## Next Steps

- Proceed to [Phase 03](./phase-03-frontend-ui-changes.md)
