# Multi-Entity WorkShift Creation

## Goal

Allow an administrator to create the same WorkShift across multiple entities, automatically assigning each new department shift only to users who do not already have a WorkShift.

## Confirmed Design

- The create form accepts one or more entities for Admin users; HR remains restricted to their own entity.
- With one entity selected, the existing apply-all or location/department flow remains unchanged.
- With multiple entities selected, apply-all is implicit and location/department controls are hidden.
- The existing create endpoint accepts `entity_ids` for the multi-entity operation while retaining the existing payloads.
- One WorkShift is created per active department. Duplicate names are skipped per department.
- Users in a successfully created department are assigned the new shift only when `work_shift` is null.
- Rotating shifts are auto-assigned only when the user already has a cycle start date, preserving the existing user-model invariant.
- Creation and user assignment run in one database transaction.

## Assumptions and Risks

- Inactive departments are excluded; user status does not affect assignment.
- Existing user WorkShift assignments are never overwritten.
- A skipped department receives no assignment changes.
- Bulk database operations are required to avoid per-user writes.
- Group editing and deletion must remain transaction-safe and entity-scoped.
- Historical rows with identical names and complete schedule configuration are treated as one management group.

## Decision Log

- Extend the existing endpoint instead of adding a second bulk endpoint, preserving one validation and transaction boundary.
- Do not make repeated frontend requests because partial cross-entity success would be difficult to recover safely.
- Preserve the one-WorkShift-per-user model; alternative shifts remain selectable from the existing Edit User form.
- Add `management_group_id` instead of grouping only in React, so group identity survives edits and supports atomic group actions.
- Backfill historical rows by the confirmed signature: name, pattern, working/break times, cycle days, and weekend behavior.
- Keep department-specific WorkShift IDs for user assignment while rendering human-readable labels in Edit User.
- Extend group PATCH with desired `entity_ids`; retained entities update, added entities receive department copies, and removed entities are soft-deactivated.
- Clear user assignments that point to removed entity copies; auto-assign added copies only to users without a WorkShift.
- Remove break controls from Add/Edit and clear stored break values when a group is edited.

## Tasks

- [x] Add failing API tests for multi-entity creation, null-only user assignment, duplicate handling, and entity authorization.
- [x] Extend WorkShift creation to support `entity_ids` and bulk-assign unassigned users.
- [x] Update the React form for multi-select behavior while preserving the single-entity flow.
- [x] Run targeted backend tests, Django checks, frontend lint/build, and diff validation.
- [x] Add failing tests for management group creation and group-wide edit/delete.
- [x] Add and backfill `management_group_id`, then expose it through the API.
- [x] Group management cards and make card actions operate on the full group.
- [x] Force Edit User WorkShift selection to render the shift name instead of its UUID.
- [x] Re-run backend, migration, lint, build, and diff validation.
- [x] Add a failing test for atomic entity add/remove and user assignment synchronization.
- [x] Extend group PATCH to synchronize the desired entity set.
- [x] Add entity selection to multi-entity Edit Shift and remove break controls.
- [x] Re-run backend, migration, frontend, and diff validation after entity synchronization.

## Done When

- [x] Multi-entity creation covers every active department in the selected entities.
- [x] Users without a WorkShift are assigned; existing assignments are unchanged.
- [x] Existing single-entity behavior and HR scoping remain covered and passing.
- [x] One logical WorkShift renders as one management card and group actions update every member.
- [x] Edit User displays a readable WorkShift label while submitting the department-specific ID.
- [x] Multi-entity Edit Shift can add/remove entities and synchronizes affected users atomically.
