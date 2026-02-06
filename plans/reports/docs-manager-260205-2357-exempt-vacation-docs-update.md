# Documentation Update Report: Dynamic EXEMPT_VACATION Allocation

**Date:** 2026-02-05
**Feature:** Dynamic EXEMPT_VACATION allocation by years of service

---

## Summary

The new dynamic EXEMPT_VACATION feature replaces the flat 96-hour annual allocation with tier-based allocation based on employee tenure. Documentation has been reviewed and updated accordingly.

---

## Changes Made

### Files Updated

**1. /home/silver/test-leave/README.md (Line 176)**

- **OLD:** "Hours-based tracking (8 hours/day default, 96 hours/year allocation)"
- **NEW:** "Hours-based tracking (8 hours/day default, dynamic EXEMPT_VACATION by years of service)"
- **Reason:** The hardcoded 96-hour figure is now inaccurate; allocation is dynamic based on years of service

---

## New Functionality Reference

### Implementation Details

**Code Location:** `/home/silver/test-leave/leaves/services.py`

- `calculate_exempt_vacation_hours()` - Main allocation function
- `EXEMPT_VACATION_TIERS` - Tier mapping (Years 2-5: 80h, 6-10: 120h, 11-15: 160h, 16+: 200h)
- `FIRST_YEAR_PRORATE` - First-year proration table by join month

**Integration Points:**
- `users/signals.py` - Onboarding signal uses dynamic allocation instead of flat 96h
- `leaves/views/balances.py` - Balance view applies dynamic calculation
- `leaves/management/commands/recalculate_exempt_vacation.py` - Management command for recalculation

---

## Documentation Status

**Current State:**
- No dedicated `/docs` directory exists yet (referenced in README but not created)
- Only README.md contains relevant allocation documentation
- Update applied successfully to prevent outdated info

**What Was NOT Created:**
- No new documentation files (following "minimal, don't create new docs" instruction)
- No additional docs beyond the README update

---

## Notes

- The feature includes a management command `recalculate_exempt_vacation` (--year, --dry-run) for batch recalculation, but no documentation updates were needed since this is an admin tool
- First-year proration by join month is complex but not mentioned in user-facing docs (appropriate for current README scope)
- Default fallback is 80h when join_date is None

---

## Unresolved Questions

None. Documentation review complete.
