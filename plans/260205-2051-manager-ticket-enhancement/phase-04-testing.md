# Phase 04: Testing & Validation

**Priority**: P2
**Status**: pending
**Effort**: 1h

## Context Links
- Parent: [plan.md](./plan.md)
- Tests: `/home/silver/test-leave/leaves/tests/`

## Overview
Comprehensive testing of both features:
1. Denying approved requests with time constraint
2. Approve reason functionality

## Key Insights

### Existing Tests
- `leaves/tests/test_requests.py` has approval/rejection tests
- Need to add new test cases for both features

### Test Scenarios Needed
1. Approve with comment (optional and required)
2. Reject approved request (> 24h before start)
3. Reject approved request (< 24h before start - should fail)
4. Balance restoration when rejecting approved
5. UI behavior with different ticket statuses

## Requirements

### Backend Tests
- Test approve with and without comment
- Test reject approved request success case
- Test reject approved request time constraint failure
- Test balance restoration
- Verify audit log entries

### Frontend Tests
- Test approve modal renders textarea
- Test deny button enable/disable logic
- Test time calculation accuracy
- Test API calls with new parameters

### Manual Testing
- End-to-end user flows
- Timezone edge cases
- Error message clarity

## Architecture

```
Test Pyramid:
        Manual (E2E)
           ↓
    Frontend Component Tests
           ↓
    Backend API Tests
           ↓
    Backend Service Unit Tests
```

## Related Code Files

### Files to Modify

**`/home/silver/test-leave/leaves/tests/test_requests.py`**
- Add new test methods for both features

### Files to Create
- None (extend existing test files)

## Implementation Steps

### Backend Tests

1. **Add approve comment tests**:
   ```python
   def test_approve_with_comment(self):
       # Test comment is stored

   def test_approve_without_comment(self):
       # Test backward compatibility

   def test_approve_comment_too_long(self):
       # Test validation error
   ```

2. **Add reject approved tests**:
   ```python
   def test_reject_approved_request_success(self):
       # Setup: create and approve request > 24h ago
       # Test: reject should succeed
       # Verify: balance restored

   def test_reject_approved_request_time_constraint(self):
       # Setup: create and approve request < 24h before start
       # Test: reject should fail
       # Verify: error message

   def test_reject_approved_balance_restoration(self):
       # Verify exact balance change
   ```

3. **Run tests**:
   ```bash
   python manage.py test leaves.tests.test_requests
   ```

### Frontend Tests

1. **Component tests** (if testing framework exists):
   - Render ManagerTicket with different states
   - Test button enable/disable logic
   - Test modal rendering

2. **Manual testing checklist**:
   - [ ] Create pending request, approve with reason
   - [ ] Verify reason displayed in detail
   - [ ] Create and approve request for next week
   - [ ] Verify Deny button enabled
   - [ ] Deny the approved request
   - [ ] Verify balance restored
   - [ ] Create and approve request for tomorrow
   - [ ] Verify Deny button disabled with message
   - [ ] Check audit logs for all actions

### Edge Cases

1. **Timezone scenarios**:
   - User in different timezone than server
   - Request spanning midnight

2. **Boundary cases**:
   - Exactly 24 hours before start
   - Leap seconds (unlikely)

3. **Error cases**:
   - Network timeout during approve/deny
   - Concurrent approval attempts

## Todo List

### Backend
- [ ] Write test_approve_with_comment
- [ ] Write test_approve_without_comment
- [ ] Write test_reject_approved_request_success
- [ ] Write test_reject_approved_request_time_constraint
- [ ] Write test_reject_approved_balance_restoration
- [ ] Run all leave tests
- [ ] Verify audit logs in all scenarios

### Frontend
- [ ] Manual test: approve with reason
- [ ] Manual test: deny approved (> 24h)
- [ ] Manual test: deny approved (< 24h)
- [ ] Manual test: verify balance restoration
- [ ] Manual test: check time display accuracy
- [ ] Test in different browsers (Chrome, Firefox, Safari)

### Integration
- [ ] End-to-end: full approval workflow with comments
- [ ] End-to-end: approve then deny workflow
- [ ] Test with real user accounts (manager, employee)

## Success Criteria

- All new tests pass
- All existing tests still pass
- Manual testing checklist complete
- Balance always correct after actions
- Time constraints enforced correctly
- Comments displayed properly
- No console errors in browser

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Time calculation edge cases | Medium | Test multiple timezones |
| Race conditions in balance | Low | Transaction tests |
| Frontend state bugs | Low | Manual testing checklist |

## Security Considerations

- Verify unauthorized users cannot deny approved requests
- Verify time constraint cannot be bypassed
- Verify balance cannot be manipulated

## Next Steps

- All phases complete - ready for deployment
