---
title: "Dynamic EXEMPT_VACATION allocation by years of service"
description: "Allocate exempt vacation days based on employee tenure with 1st-year prorate"
status: complete
priority: P1
effort: 2h
branch: main
tags: [leaves, balance, allocation, years-of-service]
created: 2026-02-05
---

# Dynamic EXEMPT_VACATION Allocation by Years of Service

## Summary

Replace the fixed 80h EXEMPT_VACATION allocation with a dynamic calculation based on employee tenure (join_date). 1st-year employees get prorated days by join month. Subsequent years follow a tiered table capped at 25 days (200h) for 20+ years.

## Current State

- `users/signals.py` creates all 4 balance types with flat `Decimal('96.00')` on onboarding
- `leaves/views/balances.py` uses `DEFAULT_BALANCE_ALLOCATION` dict (EXEMPT_VACATION=80h) for get_or_create fallback
- `leaves/constants.py` has `DEFAULT_YEARLY_ALLOCATION = 96`
- User model has `join_date = DateField(null=True, blank=True)`

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Add allocation calculation service | Complete | [phase-01](phase-01-allocation-calculation-service.md) |
| 2 | Update balance creation signal | Complete | [phase-02](phase-02-update-balance-creation-signal.md) |
| 3 | Add yearly recalculation mgmt command | Complete | [phase-03](phase-03-yearly-recalculation-command.md) |

## Key Dependencies

- `User.join_date` must be populated; null/future dates handled gracefully
- Only EXEMPT_VACATION uses dynamic calc; other 3 types keep fixed allocations
- No DB migration needed (allocation table stored as Python constant)

## Constraints

- Cap at 25 days / 200h for 20+ years
- YEARFRAC-equivalent: `floor((ref_date - join_date).days / 365.25)`, year_of_service = completed_years + 1
- **Reference date = January 1st of the balance year** (NOT current date) for consistency across all employees
- Prorate only applies to 1st year of service
