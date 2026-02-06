# Phase 03: Frontend - UI Changes

**Priority**: P2
**Status**: pending
**Effort**: 2.5h

## Context Links
- Parent: [plan.md](./plan.md)
- Component: `/home/silver/test-leave/frontend/src/pages/ManagerTicket.jsx`
- API: `/home/silver/test-leave/frontend/src/api/dashboardApi.js`

## Overview
Update ManagerTicket component to:
1. Show Deny button for Approved requests (when > 24h before start)
2. Add reason textarea to Approve confirmation modal
3. Display time remaining for approved requests
4. Show approve comment in detail view

## Key Insights

### Current State
- Line 34: `isPending = selectedTicket?.status === "Pending"`
- Lines 293, 308: Buttons disabled when `!isPending`
- Lines 331-358: Confirm modal - only deny has TextArea
- API already supports comment parameter (dashboardApi.js line 203)

### Required Changes
1. Enable Deny button for Approved status with time check
2. Add TextArea to approve modal
3. Calculate time remaining for cutoff
4. Pass comment to approve API
5. Display approve comment in detail view
6. Extend getPendingRequests to include approved requests

## Requirements

### Functional
- Deny button enabled for Approved tickets if > 24h before start
- Deny button disabled with tooltip if < 24h before start
- Approve modal includes optional reason textarea
- Approve reason sent to API
- Approve reason displayed in ticket detail
- Show time remaining info for approved tickets

### Non-Functional
- Clear visual feedback for disabled states
- User-friendly time display (e.g., "2 days 5 hours remaining")

## Architecture

```
ManagerTicket Component
        ↓
State Changes:
  - approveReason state
  - canDenyApproved computed value
        ↓
UI Changes:
  - Approve modal: Add TextArea
  - Deny button: Enable for Approved with time check
  - Detail view: Show approver_comment
  - Time display: Show cutoff info
        ↓
API Calls:
  - approveLeaveRequest(id, comment)
  - rejectLeaveRequest(id, reason) [already handles approved]
```

## Related Code Files

### Files to Modify

**`/home/silver/test-leave/frontend/src/pages/ManagerTicket.jsx`**

**`/home/silver/test-leave/frontend/src/api/dashboardApi.js`**
- Already supports comment in approveLeaveRequest (line 203)

## Implementation Steps

1. **Add state for approve reason** (after line 33):
   ```jsx
   const [approveReason, setApproveReason] = useState("");
   ```

2. **Create helper for time check** (after typeColor object):
   ```jsx
   const canDenyApproved = (ticket) => {
     if (!ticket || ticket.status !== "Approved") return false;
     const cutoff = new Date(ticket.from);
     cutoff.setHours(cutoff.getHours() - 24);
     return new Date() < cutoff;
   };

   const getTimeRemaining = (ticket) => {
     if (!ticket || ticket.status !== "Approved") return null;
     const cutoff = new Date(ticket.from);
     cutoff.setHours(cutoff.getHours() - 24);
     const diff = cutoff - new Date();
     if (diff <= 0) return null;
     // Format as "X days Y hours"
   };
   ```

3. **Update button enable logic** (lines 290-323):
   ```jsx
   // Deny button
   disabled={!isPending && !canDenyApproved(selectedTicket)}
   // Add tooltip when disabled due to time
   ```

4. **Add TextArea to approve modal** (lines 342-344):
   ```jsx
   {confirmType === "approve" && (
     <>
       <Text>Approve reason (optional):</Text>
       <TextArea
         rows={3}
         value={approveReason}
         onChange={(e) => setApproveReason(e.target.value)}
         placeholder="Enter approve reason..."
         style={{ marginTop: 8 }}
       />
     </>
   )}
   ```

5. **Update handleApprove** (line 111):
   ```jsx
   await approveLeaveRequest(selectedTicket.id, approveReason);
   ```

6. **Reset approve reason** (line 120):
   ```jsx
   setApproveReason("");
   ```

7. **Display approve comment** in detail view (after line 242):
   ```jsx
   {selectedTicket.approverComment && (
     <Descriptions.Item label="Approver Comment">
       <Text type="success">{selectedTicket.approverComment}</Text>
     </Descriptions.Item>
   )}
   ```

8. **Update API mapping** in dashboardApi.js (line 195):
   ```jsx
   approverComment: item.approver_comment,
   ```

9. **Extend fetch to include approved** (line 44):
   - Change from pending-only to pending + approved
   - Or add separate fetch for approved requests

## Todo List

- [ ] Add approveReason state variable
- [ ] Create canDenyApproved helper function
- [ ] Create getTimeRemaining helper function
- [ ] Update Deny button enable/disable logic
- [ ] Add tooltip for disabled Deny button
- [ ] Add TextArea to approve confirmation modal
- [ ] Update handleApprove to pass reason
- [ ] Reset approveReason after action
- [ ] Display approverComment in detail view
- [ ] Update API mapping to include approver_comment
- [ ] Add time remaining display for approved tickets
- [ ] Test all scenarios (pending, approved-with-time, approved-no-time)

## Success Criteria

- Deny button enabled for Approved tickets when > 24h before start
- Deny button disabled with helpful message when < 24h
- Approve modal includes reason textarea
- Approve reason stored and displayed
- Time remaining shown for approved tickets
- All existing functionality unchanged

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Date/time calculation bugs | Medium | Test with various timezones |
| API response doesn't include approver_comment | Low | Verify backend returns it |
| Confusion about when deny is allowed | Low | Clear tooltips and messaging |

## Security Considerations

- None (UI changes only)

## Next Steps

- Proceed to [Phase 04](./phase-04-testing.md)
