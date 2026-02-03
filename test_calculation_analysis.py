#!/usr/bin/env python3
"""Analyze the hours calculation logic without database."""

from datetime import datetime, date, timedelta
from decimal import Decimal

def calculate_leave_hours_mock(start_date, end_date):
    """
    Mock calculation based on utils.py logic (FULL_DAY, no holidays)
    """
    working_days = 0
    current = start_date

    while current <= end_date:
        # Skip weekends (5=Saturday, 6=Sunday)
        if current.weekday() < 5:
            working_days += 1
        current += timedelta(days=1)

    # 8 hours per working day
    return Decimal(str(working_days * 8))


# Test case: Feb 7-10, 2026
start = date(2026, 2, 7)
end = date(2026, 2, 10)

print("="*70)
print("HOURS CALCULATION ANALYSIS")
print("="*70)
print(f"Start date: {start} ({start.strftime('%A')})")
print(f"End date:   {end} ({end.strftime('%A')})")
print()

# Day-by-day breakdown
current = start
print("Day-by-day breakdown:")
working_days = 0
while current <= end:
    day_name = current.strftime('%A')
    weekday = current.weekday()
    is_working = weekday < 5

    if is_working:
        working_days += 1
        print(f"  {current} ({day_name}) - weekday={weekday} - WORKING DAY")
    else:
        print(f"  {current} ({day_name}) - weekday={weekday} - WEEKEND (skipped)")

    current += timedelta(days=1)

print()
print(f"Working days: {working_days}")
print(f"Total hours: {working_days * 8}h")
print()

# Calculate using mock function
result = calculate_leave_hours_mock(start, end)
print(f"Calculated hours: {result}h")
print()

# Expected vs actual
print("="*70)
print("ANALYSIS:")
print("="*70)
print(f"Expected (4 days × 8h):  32h")
print(f"Calculated (actual):     {result}h")
print()

if result == 16:
    print("⚠️  BUG CONFIRMED: Only counting 2 working days instead of 4")
    print()
    print("Possible causes:")
    print("  1. Weekend logic error (wrong weekday check)")
    print("  2. Public holiday incorrectly applied")
    print("  3. Date range calculation error")
    print("  4. Serializer/view overwriting total_hours")
elif result == 32:
    print("✅ Calculation logic is CORRECT")
    print()
    print("Possible causes of 16h in database:")
    print("  1. Different dates were actually saved")
    print("  2. Public holidays are being applied")
    print("  3. Issue in serializer or view logic")
