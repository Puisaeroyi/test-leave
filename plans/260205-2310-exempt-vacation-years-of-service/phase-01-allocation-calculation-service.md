# Phase 1: Add Allocation Calculation Service

## Context Links

- [Plan overview](plan.md)
- [leaves/services.py](/home/silver/test-leave/leaves/services.py) - existing service layer
- [leaves/constants.py](/home/silver/test-leave/leaves/constants.py) - constants
- [users/models.py](/home/silver/test-leave/users/models.py) - User model with join_date

## Overview

- **Priority:** P1
- **Status:** Complete
- **Description:** Add `calculate_exempt_vacation_hours()` function to `leaves/services.py` containing the years-of-service lookup table, prorate logic, and edge case handling.

## Key Insights

- `User.join_date` is `DateField(null=True, blank=True)` -- must handle None gracefully
- Current codebase uses `Decimal` for all hour values (see LeaveBalance model)
- The service layer already exists in `leaves/services.py` with `LeaveApprovalService`
- Allocation table is pure Python constant -- no migration needed

## Requirements

### Functional
1. Years-of-service calculation: `floor((reference_date - join_date).days / 365.25)`, year_of_service = completed + 1
2. Tier table lookup returning hours as `Decimal`:
   - Year 1 (prorate): see month-based table
   - Years 2-5: 80h
   - Years 6-10: 120h
   - Years 11-15: 160h
   - Years 16-20+: 200h (cap)
3. 1st-year prorate by join month:
   - Jan:72h, Feb:64h, Mar:56h, Apr:48h, May:40h, Jun:32h, Jul:24h, Aug:16h, Sep:8h, Oct/Nov/Dec:0h
4. Edge cases: null join_date -> return default 80h; future join_date -> return 0h

### Non-Functional
- Pure function, no DB queries (takes `join_date` and `reference_date` as args)
- **`reference_date` should always be Jan 1st of the balance year** (callers pass `date(year, 1, 1)`)
- Returns `Decimal` for consistency with `LeaveBalance.allocated_hours`

## Architecture

```
leaves/services.py
  +-- EXEMPT_VACATION_TIERS (constant dict)
  +-- FIRST_YEAR_PRORATE (constant dict)
  +-- calculate_exempt_vacation_hours(join_date: date, reference_date: date) -> Decimal
  +-- get_year_of_service(join_date: date, reference_date: date) -> int
```

- `get_year_of_service()` computes `floor(delta_days / 365.25) + 1`
- `calculate_exempt_vacation_hours()` calls `get_year_of_service()`, looks up tier or prorate

## Related Code Files

| Action | File |
|--------|------|
| Modify | `leaves/services.py` -- add functions + constants at module level |
| Modify | `leaves/constants.py` -- optionally move constants here for consistency |

## Implementation Steps

1. Add `EXEMPT_VACATION_TIERS` constant dict at top of `leaves/services.py`:
   ```python
   EXEMPT_VACATION_TIERS = {
       (2, 5): Decimal('80.00'),    # 10 days
       (6, 10): Decimal('120.00'),  # 15 days
       (11, 15): Decimal('160.00'), # 20 days
       (16, None): Decimal('200.00'), # 25 days (cap)
   }
   ```
2. Add `FIRST_YEAR_PRORATE` constant dict mapping month int -> Decimal hours:
   ```python
   FIRST_YEAR_PRORATE = {
       1: Decimal('72.00'), 2: Decimal('64.00'), 3: Decimal('56.00'),
       4: Decimal('48.00'), 5: Decimal('40.00'), 6: Decimal('32.00'),
       7: Decimal('24.00'), 8: Decimal('16.00'), 9: Decimal('8.00'),
       10: Decimal('0.00'), 11: Decimal('0.00'), 12: Decimal('0.00'),
   }
   ```
3. Add `get_year_of_service(join_date, reference_date)`:
   - Compute `completed_years = floor((reference_date - join_date).days / 365.25)`
   - Return `completed_years + 1`
4. Add `calculate_exempt_vacation_hours(join_date, reference_date)`:
   - If `join_date` is None, return `Decimal('80.00')` (safe default)
   - If `join_date > reference_date`, return `Decimal('0.00')`
   - Get `year_of_service` via helper
   - If `year_of_service == 1`, return `FIRST_YEAR_PRORATE[join_date.month]`
   - Else iterate `EXEMPT_VACATION_TIERS`, find matching range, return hours
   - If somehow no match (shouldn't happen), return cap `Decimal('200.00')`

## Todo List

- [x] Add `EXEMPT_VACATION_TIERS` constant
- [x] Add `FIRST_YEAR_PRORATE` constant
- [x] Implement `get_year_of_service()`
- [x] Implement `calculate_exempt_vacation_hours()`
- [x] Handle edge cases: null join_date, future join_date

## Success Criteria

- `calculate_exempt_vacation_hours(date(2025,3,15), date(2026,1,1))` returns `Decimal('80.00')` (year 2, in 2-5 tier)
- `calculate_exempt_vacation_hours(date(2026,4,10), date(2026,4,10))` returns `Decimal('48.00')` (1st year, April join)
- `calculate_exempt_vacation_hours(None, date(2026,1,1))` returns `Decimal('80.00')` (null fallback)
- `calculate_exempt_vacation_hours(date(2027,1,1), date(2026,1,1))` returns `Decimal('0.00')` (future join)
- `calculate_exempt_vacation_hours(date(2006,6,1), date(2026,1,1))` returns `Decimal('200.00')` (20+ years, cap)

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| join_date is None for many users | Medium | Default to 80h (current-like behavior) |
| Leap year edge cases in YEARFRAC | Low | Using 365.25 divisor handles this |

## Security Considerations

- No user input; function takes validated Python date objects
- No DB writes in this phase

## Next Steps

- Phase 2 consumes `calculate_exempt_vacation_hours()` in the signal
- Phase 3 consumes it in the management command
