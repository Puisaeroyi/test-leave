# Code Review: Dynamic EXEMPT_VACATION Allocation by Years of Service

**Reviewer:** code-reviewer | **Date:** 2026-02-05 | **Score: 7/10**

## Scope

- **Files reviewed:** 4
  - `/home/silver/test-leave/leaves/services.py` (new functions + constants)
  - `/home/silver/test-leave/users/signals.py` (onboarding signal update)
  - `/home/silver/test-leave/leaves/views/balances.py` (balance view update)
  - `/home/silver/test-leave/leaves/management/commands/recalculate_exempt_vacation.py` (new command)
- **LOC changed:** ~130 added/modified
- **Focus:** correctness, edge cases, security, performance, DRY/KISS

## Overall Assessment

Solid feature implementation with clean separation of concerns. The core calculation logic is centralized in `services.py` and reused across signal, view, and management command. However, there are two bugs (one critical, one medium) and several minor issues.

## Critical Issues

### 1. [BUG] Signal KeyError if new BalanceType added

**File:** `/home/silver/test-leave/users/signals.py`, line 45

```python
for balance_type in LeaveBalance.BalanceType.values:
    if balance_type == 'EXEMPT_VACATION':
        hours = calculate_exempt_vacation_hours(...)
    else:
        hours = FIXED_BALANCE_DEFAULTS[balance_type]  # KeyError if new type added
```

`FIXED_BALANCE_DEFAULTS` has exactly 3 keys. If a new `BalanceType` is added to the model (e.g., `COMP_TIME`), the signal will raise `KeyError` at runtime. This is a **production crash** on every user save.

**Fix:** Use `.get()` with a sensible default, or restructure to use a single dict like the view does.

```python
hours = FIXED_BALANCE_DEFAULTS.get(balance_type, Decimal('0.00'))
```

### 2. [BUG] Management command: `skipped_count` never incremented

**File:** `/home/silver/test-leave/leaves/management/commands/recalculate_exempt_vacation.py`, line 88

`skipped_count` is initialized to 0 (line 54) and printed in output (line 88) but is never incremented. Since `update_or_create` always creates or updates, no path sets `skipped_count`. Either remove it from the output or add skip logic (e.g., skip if hours unchanged).

## High Priority

### 3. [EDGE CASE] Year-of-service calculation: employee in "year 1" on their anniversary

**File:** `/home/silver/test-leave/leaves/services.py`, line 46-54

An employee who joined **Jan 1, 2025** with reference date **Jan 1, 2026** (365 days) gets `yos = floor(365 / 365.25) + 1 = 1`. This means they are treated as first-year and get `FIRST_YEAR_PRORATE[1] = 72h` instead of the tier 2-5 value of `80h`.

This is arguably correct (they have not yet completed a full "calendar year" per 365.25-day reckoning), but it is a subtle business logic decision that should be documented explicitly. Stakeholders may expect that on the anniversary year, the employee gets the full allocation. Confirm with product owner.

### 4. [MISSING] No input validation on `year` query param

**File:** `/home/silver/test-leave/leaves/views/balances.py`, line 30

```python
year = int(request.query_params.get('year', timezone.now().year))
```

If a user passes `year=abc`, this raises an unhandled `ValueError` -> 500 error. If they pass `year=99999`, `date(99999, 1, 1)` will succeed but is nonsensical. Add validation:

```python
try:
    year = int(request.query_params.get('year', timezone.now().year))
except (ValueError, TypeError):
    return Response({'error': 'Invalid year parameter'}, status=400)
```

### 5. [MISSING] No unit tests

No tests found for `get_year_of_service`, `calculate_exempt_vacation_hours`, the signal behavior, or the management command. These are business-critical calculations. At minimum, test:
- Tier boundaries (yos=1, 2, 5, 6, 10, 11, 15, 16, 20)
- First-year prorate for each month
- `join_date=None` fallback
- `join_date > reference_date` case
- Signal creates correct hours
- Management command dry-run vs real run

## Medium Priority

### 6. [DRY] Duplicate allocation dictionaries

The default hours for non-dynamic types are defined in two places:
- `users/signals.py` line 20-24: `FIXED_BALANCE_DEFAULTS` (string keys)
- `leaves/views/balances.py` line 15-20: `DEFAULT_BALANCE_ALLOCATION` (enum keys)

These can drift independently. Consider a single source of truth in `leaves/services.py` or `leaves/constants.py`.

### 7. [STYLE] `EXEMPT_VACATION` still in `DEFAULT_BALANCE_ALLOCATION`

**File:** `/home/silver/test-leave/leaves/views/balances.py`, line 16

```python
LeaveBalance.BalanceType.EXEMPT_VACATION: Decimal('80.00'),  # fallback only
```

This value is never used (immediately overridden on line 38). Including it in the dict is confusing. Consider removing it and handling EXEMPT_VACATION outside the loop, or use a comment that is clearer about why it is present (to drive iteration).

### 8. [PERFORMANCE] Management command loads all users into memory

**File:** `/home/silver/test-leave/leaves/management/commands/recalculate_exempt_vacation.py`, line 57

```python
for user in users:
```

For large orgs (10k+ employees), this loads all User objects into memory. Use `.iterator()`:

```python
for user in users.iterator():
```

Also, `users.count()` on line 79 triggers a second query after the loop. Store count before the loop or use a counter.

### 9. [ROBUSTNESS] Management command: `transaction.atomic` wraps dry_run

**File:** `/home/silver/test-leave/leaves/management/commands/recalculate_exempt_vacation.py`, line 56

The `transaction.atomic()` block wraps the entire loop including dry-run iterations. For dry-run, no DB writes happen, so the transaction is unnecessary overhead. Minor, but cleaner to skip it:

```python
if not dry_run:
    with transaction.atomic():
        ...
```

## Low Priority

### 10. [STYLE] `select_related` in management command fetches unused relations

**File:** Line 50: `.select_related('entity', 'location', 'department')` -- these related objects are never accessed in the loop. The filter uses `__isnull` lookups which don't need select_related. Remove to reduce query size.

### 11. [INCONSISTENCY] Old `DEFAULT_YEARLY_ALLOCATION = 96` in `leaves/constants.py`

**File:** `/home/silver/test-leave/leaves/constants.py`, line 18

The old constant `DEFAULT_YEARLY_ALLOCATION = 96` is still used by `users/views/balance.py` (HR balance adjust view). This is out of scope but creates an inconsistency: onboarding creates balances with dynamic hours (40-200), but HR adjustments default to 96h. Consider updating or deprecating this constant.

## Positive Observations

- **Centralized calculation logic** in `services.py` -- single function used by all 3 consumers. Good DRY.
- **None-safe** handling for `join_date is None` with sensible default.
- **Future-date guard** (`join_date > reference_date` returns 0).
- **Management command** has `--dry-run` flag and clear output -- good operational practice.
- **`update_or_create`** in management command correctly handles both new and existing balances.
- **`get_or_create`** in view/signal prevents duplicate balance creation.
- **Clean import ordering** and consistent Decimal usage.

## Recommended Actions (Priority Order)

1. **Fix** `FIXED_BALANCE_DEFAULTS` KeyError risk in signal (use `.get()` with default)
2. **Remove** unused `skipped_count` from management command output
3. **Add** input validation for `year` query param in balance view
4. **Confirm** year-of-service boundary behavior with product owner (yos=1 on anniversary)
5. **Add** unit tests for `get_year_of_service` and `calculate_exempt_vacation_hours`
6. **Consolidate** default balance allocation dicts into single source of truth
7. **Add** `.iterator()` to management command user loop

## Metrics

- Type Coverage: N/A (Python, no type annotations on most params)
- Test Coverage: 0% for new code (no tests found)
- Linting Issues: 0 syntax errors detected

## Unresolved Questions

1. Is the "year 1 on anniversary" behavior (72h instead of 80h for Jan joiners at exactly 365 days) intentional? Needs product owner confirmation.
2. Should `FIRST_YEAR_PRORATE` month 1 = 72h (9 remaining months * 8h) or 80h (full year allocation for a Jan joiner)? The prorate logic implies partial year, but a Jan 1 joiner works essentially the full year.
3. Should the `UserBalanceAdjustView` (HR adjustment) also be updated to use dynamic allocation instead of the old `DEFAULT_YEARLY_ALLOCATION = 96`?
4. Should the management command also recalculate/create the non-dynamic balance types (SICK, NON_EXEMPT_VACATION) for completeness, or is that intentionally out of scope?
