# Phase 2: Update Balance Creation Signal

## Context Links

- [Plan overview](plan.md)
- [Phase 1](phase-01-allocation-calculation-service.md) -- prerequisite
- [users/signals.py](/home/silver/test-leave/users/signals.py) -- signal to modify
- [leaves/views/balances.py](/home/silver/test-leave/leaves/balances.py) -- balance view fallback

## Overview

- **Priority:** P1
- **Status:** Complete
- **Description:** Update `create_leave_balance_on_onboarding` signal and `LeaveBalanceMeView` to use dynamic EXEMPT_VACATION allocation instead of flat defaults.

## Key Insights

- Signal currently creates all 4 balance types with flat `Decimal('96.00')`
- `LeaveBalanceMeView.get()` uses `DEFAULT_BALANCE_ALLOCATION` dict with EXEMPT_VACATION=80h for get_or_create
- Both paths need updating so balance is correct regardless of entry point
- Only EXEMPT_VACATION changes; other 3 types keep their fixed allocations

## Requirements

### Functional
1. Signal: for EXEMPT_VACATION, call `calculate_exempt_vacation_hours(instance.join_date, date(current_year, 1, 1))` instead of flat value
2. Signal: for other 3 types, use fixed values from `DEFAULT_BALANCE_ALLOCATION`
3. Balance view: for EXEMPT_VACATION get_or_create default, call `calculate_exempt_vacation_hours(user.join_date, date(current_year, 1, 1))`
4. Existing balances with `used_hours > 0` must NOT have `allocated_hours` overwritten by signal (get_or_create already handles this)

### Non-Functional
- Signal must remain fast; `calculate_exempt_vacation_hours()` is pure math, no DB queries
- No breaking changes to API response shape

## Architecture

```
users/signals.py
  create_leave_balance_on_onboarding()
    ├── EXEMPT_VACATION → calculate_exempt_vacation_hours(join_date, today)
    ├── NON_EXEMPT_VACATION → Decimal('40.00')
    ├── EXEMPT_SICK → Decimal('40.00')
    └── NON_EXEMPT_SICK → Decimal('40.00')

leaves/views/balances.py
  LeaveBalanceMeView.get()
    ├── EXEMPT_VACATION → calculate_exempt_vacation_hours(user.join_date, today)
    └── Others → fixed defaults from DEFAULT_BALANCE_ALLOCATION
```

## Related Code Files

| Action | File |
|--------|------|
| Modify | `users/signals.py` -- use dynamic calc for EXEMPT_VACATION |
| Modify | `leaves/views/balances.py` -- update DEFAULT_BALANCE_ALLOCATION lookup for EXEMPT_VACATION |

## Implementation Steps

1. **Update `users/signals.py`:**
   - Import `calculate_exempt_vacation_hours` from `leaves.services`
   - Import `date` from `datetime`
   - **Use `date(year, 1, 1)` as reference date** (where `year` is the balance year, i.e., current year)
   - Define per-type default allocation dict (same as views/balances.py but EXEMPT_VACATION excluded):
     ```python
     FIXED_BALANCE_DEFAULTS = {
         'NON_EXEMPT_VACATION': Decimal('40.00'),
         'EXEMPT_SICK': Decimal('40.00'),
         'NON_EXEMPT_SICK': Decimal('40.00'),
     }
     ```
   - In the for-loop over balance types:
     - If `balance_type == 'EXEMPT_VACATION'`: compute hours via `calculate_exempt_vacation_hours(instance.join_date, date(current_year, 1, 1))`
     - Else: use `FIXED_BALANCE_DEFAULTS[balance_type]`
   - Pass computed hours as `defaults={'allocated_hours': hours}` in get_or_create

2. **Update `leaves/views/balances.py`:**
   - Import `calculate_exempt_vacation_hours` from `leaves.services`
   - Import `date` from `datetime`
   - **Use `date(year, 1, 1)` as reference date** (where `year` is the queried balance year)
   - In `LeaveBalanceMeView.get()`, change the for-loop:
     - If `balance_type == LeaveBalance.BalanceType.EXEMPT_VACATION`:
       - `default_hours = calculate_exempt_vacation_hours(user.join_date, date(year, 1, 1))`
     - Else: use existing `DEFAULT_BALANCE_ALLOCATION[balance_type]`
   - Remove or keep `DEFAULT_BALANCE_ALLOCATION` for non-EXEMPT_VACATION types (keep it, just skip EXEMPT_VACATION key)

## Todo List

- [x] Update signal to use dynamic calc for EXEMPT_VACATION
- [x] Keep fixed defaults for other 3 balance types in signal
- [x] Update LeaveBalanceMeView to use dynamic calc for EXEMPT_VACATION
- [x] Verify get_or_create won't overwrite existing balances
- [x] Test signal fires correctly on user save

## Success Criteria

- New user with join_date=2026-04-15 gets EXEMPT_VACATION balance of 48h (Apr prorate)
- New user with join_date=2020-06-01 gets EXEMPT_VACATION balance of 120h (year 6-10 tier)
- Existing balances are NOT overwritten (get_or_create behavior)
- Other 3 balance types unaffected (40h each)
- API response shape unchanged

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Signal import circular dependency | Low | `leaves.services` doesn't import `users` |
| User without join_date gets wrong balance | Medium | Fallback to 80h in calculator |
| Existing balances overwritten | None | get_or_create only sets defaults on create |

## Security Considerations

- No new endpoints exposed
- No user-controlled input affects allocation (join_date set by HR/Admin)

## Next Steps

- Phase 3 adds management command for yearly batch recalculation
