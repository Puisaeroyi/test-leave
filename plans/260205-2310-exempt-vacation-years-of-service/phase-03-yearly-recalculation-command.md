# Phase 3: Add Yearly Recalculation Management Command

## Context Links

- [Plan overview](plan.md)
- [Phase 1](phase-01-allocation-calculation-service.md) -- prerequisite (calculator)
- [Phase 2](phase-02-update-balance-creation-signal.md) -- prerequisite (signal update)
- [leaves/management/commands/seed_data.py](/home/silver/test-leave/leaves/management/commands/seed_data.py) -- existing command pattern
- [users/models.py](/home/silver/test-leave/users/models.py) -- User queryset

## Overview

- **Priority:** P1
- **Status:** Complete
- **Description:** Create Django management command `recalculate_exempt_vacation` that recalculates EXEMPT_VACATION allocated_hours for ALL active employees. Intended for yearly cron (Jan 1st).

## Key Insights

- Existing `leaves/management/commands/` already has `__init__.py` and `seed_data.py` -- pattern established
- LeaveBalance unique_together is `(user, year, balance_type)` -- use `update_or_create` for upsert
- The command must create new-year balances if they don't exist AND update existing ones with new allocation
- `used_hours` and `adjusted_hours` must NOT be reset -- only `allocated_hours` changes
- For new year balances, `used_hours` starts at 0 and `adjusted_hours` starts at 0

## Requirements

### Functional
1. Query all active users with `has_completed_onboarding` (entity+location+department set)
2. For each user, calculate EXEMPT_VACATION hours via `calculate_exempt_vacation_hours(user.join_date, reference_date)`
3. `reference_date` defaults to Jan 1 of `--year` arg (or current year)
4. Use `update_or_create`:
   - Match on `user`, `year`, `balance_type=EXEMPT_VACATION`
   - Set `allocated_hours` to calculated value
   - Do NOT touch `used_hours` or `adjusted_hours`
5. `--year` optional CLI arg (default: current year)
6. `--dry-run` flag to preview changes without writing
7. Print summary: total users processed, balances created, balances updated, skipped (no join_date)

### Non-Functional
- Batch-friendly: use `select_related` to minimize queries
- Transaction-safe: wrap in `transaction.atomic()`
- Idempotent: safe to run multiple times

## Architecture

```
leaves/management/commands/recalculate_exempt_vacation.py
  class Command(BaseCommand)
    add_arguments(parser)
      --year (int, default=current year)
      --dry-run (flag)
    handle(*args, **options)
      1. Get year + reference_date (Jan 1 of year)
      2. Query active onboarded users
      3. For each user:
         a. calculate_exempt_vacation_hours(join_date, reference_date)
         b. update_or_create LeaveBalance
      4. Print summary
```

## Related Code Files

| Action | File |
|--------|------|
| Create | `leaves/management/commands/recalculate_exempt_vacation.py` |
| Read | `leaves/services.py` (import calculator) |
| Read | `users/models.py` (User queryset) |

## Implementation Steps

1. Create `leaves/management/commands/recalculate_exempt_vacation.py`
2. Import:
   - `BaseCommand` from `django.core.management.base`
   - `transaction` from `django.db`
   - `timezone` from `django.utils`
   - `date` from `datetime`
   - `Decimal` from `decimal`
   - `User` from `django.contrib.auth` (get_user_model)
   - `LeaveBalance` from `leaves.models`
   - `calculate_exempt_vacation_hours` from `leaves.services`
3. Add `--year` argument (type=int, default=current year)
4. Add `--dry-run` boolean flag
5. In `handle()`:
   ```python
   year = options['year']
   dry_run = options['dry_run']
   reference_date = date(year, 1, 1)

   users = User.objects.filter(
       is_active=True,
       entity__isnull=False,
       location__isnull=False,
       department__isnull=False,
   ).select_related('entity', 'location', 'department')

   created_count = 0
   updated_count = 0
   skipped_count = 0

   with transaction.atomic():
       for user in users:
           hours = calculate_exempt_vacation_hours(user.join_date, reference_date)

           if dry_run:
               self.stdout.write(f"  [DRY RUN] {user.email}: {hours}h")
               continue

           obj, created = LeaveBalance.objects.update_or_create(
               user=user,
               year=year,
               balance_type=LeaveBalance.BalanceType.EXEMPT_VACATION,
               defaults={'allocated_hours': hours},
           )
           if created:
               created_count += 1
           else:
               updated_count += 1
   ```
6. Print summary with counts
7. Add note in docstring about cron setup: `0 0 1 1 * python manage.py recalculate_exempt_vacation`

## Todo List

- [x] Create command file with proper Django management command structure
- [x] Add `--year` argument
- [x] Add `--dry-run` flag
- [x] Implement user queryset (active + onboarded)
- [x] Loop with `update_or_create` for EXEMPT_VACATION
- [x] Print summary (created, updated, skipped counts)
- [x] Wrap in `transaction.atomic()`

## Success Criteria

- `python manage.py recalculate_exempt_vacation` processes all active onboarded users
- `python manage.py recalculate_exempt_vacation --year 2027` targets specific year
- `python manage.py recalculate_exempt_vacation --dry-run` previews without DB writes
- Existing `used_hours` and `adjusted_hours` are NOT reset
- Command is idempotent (running twice produces same result)

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Overwriting manually adjusted `allocated_hours` | Medium | This is intentional -- yearly recalc is authoritative for EXEMPT_VACATION. Manual adjustments go in `adjusted_hours` field |
| Large user base causes slow execution | Low | Use select_related, batch if needed |
| Command run mid-year overwrites prorate | Low | Default to Jan 1 reference_date; document that mid-year runs should use caution |

## Security Considerations

- Management command requires shell access (no API exposure)
- No user-facing input
- transaction.atomic() ensures all-or-nothing

## Next Steps

- Set up cron job: `0 0 1 1 * cd /app && python manage.py recalculate_exempt_vacation`
- Consider adding logging output to file for audit trail
- Future: add `--user-email` flag for single-user recalculation
