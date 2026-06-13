from datetime import date
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from leaves.holiday_management import publish_impact
from leaves.models import HolidayCalendar, LeaveBalance, LeaveCategory, LeaveRequest, PublicHoliday
from leaves.utils import calculate_leave_hours
from organizations.models import Department, Entity, Location, WorkShift
from users.models import User


def make_user(email="weekend@example.com", includes_weekends=False):
    entity = Entity.objects.create(entity_name=f"{email} Co", code=email[:5].upper())
    location = Location.objects.create(
        entity=entity,
        location_name="Main",
        city="Ho Chi Minh City",
        country="Vietnam",
        timezone="Asia/Ho_Chi_Minh",
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name="Operations",
        code=email[:3].upper(),
    )
    shift = WorkShift.objects.create(
        department=department,
        name="Rotating",
        start_time="09:00",
        end_time="17:00",
        includes_weekends=includes_weekends,
    )
    user = User.objects.create_user(
        email=email,
        password="Password123!",
        entity=entity,
        location=location,
        department=department,
        work_shift=shift,
    )
    return user


def make_vacation_category():
    category, _ = LeaveCategory.objects.update_or_create(
        code="VACATION",
        defaults={
            "category_name": "Vacation",
            "balance_bucket": LeaveCategory.BalanceBucket.VACATION,
        },
    )
    return category


@pytest.mark.django_db
def test_weekend_full_day_hours_depend_on_work_shift_flag():
    flagged = make_user("flagged@example.com", includes_weekends=True)
    unflagged = make_user("unflagged@example.com", includes_weekends=False)
    no_shift = make_user("noshift@example.com", includes_weekends=False)
    no_shift.work_shift = None
    no_shift.save(update_fields=["work_shift"])

    assert calculate_leave_hours(
        flagged, date(2026, 6, 13), date(2026, 6, 14), LeaveRequest.ShiftType.FULL_DAY
    ) == Decimal("16")
    assert calculate_leave_hours(
        unflagged, date(2026, 6, 13), date(2026, 6, 14), LeaveRequest.ShiftType.FULL_DAY
    ) == Decimal("0")
    assert calculate_leave_hours(
        no_shift, date(2026, 6, 13), date(2026, 6, 14), LeaveRequest.ShiftType.FULL_DAY
    ) == Decimal("0")


@pytest.mark.django_db
def test_weekend_flag_counts_full_week_and_holiday_still_excludes_day():
    user = make_user("holiday-weekend@example.com", includes_weekends=True)
    calendar = HolidayCalendar.objects.create(
        name="Weekend holiday",
        country_code="VN",
        year=2026,
        entity=user.entity,
        status=HolidayCalendar.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        calendar=calendar,
        entity=user.entity,
        holiday_name="Saturday holiday",
        start_date=date(2026, 6, 13),
        end_date=date(2026, 6, 13),
        year=2026,
        status=PublicHoliday.Status.PUBLISHED,
    )

    assert calculate_leave_hours(
        user, date(2026, 6, 8), date(2026, 6, 14), LeaveRequest.ShiftType.FULL_DAY
    ) == Decimal("48")


@pytest.mark.django_db
def test_publish_impact_uses_weekend_shift_working_day_logic():
    user = make_user("publish-weekend@example.com", includes_weekends=True)
    category = make_vacation_category()
    LeaveRequest.objects.create(
        user=user,
        leave_category=category,
        start_date=date(2026, 6, 13),
        end_date=date(2026, 6, 14),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal("16.00"),
        status=LeaveRequest.Status.PENDING,
    )
    calendar = HolidayCalendar.objects.create(
        name="Draft weekend holiday",
        country_code="VN",
        year=2026,
        entity=user.entity,
        status=HolidayCalendar.Status.DRAFT,
    )
    PublicHoliday.objects.create(
        calendar=calendar,
        entity=user.entity,
        holiday_name="Saturday holiday",
        start_date=date(2026, 6, 13),
        end_date=date(2026, 6, 13),
        year=2026,
        status=PublicHoliday.Status.DRAFT,
    )

    preview = publish_impact(calendar)

    assert preview["affected_requests"] == 1
    assert preview["changes"][0]["new_hours"] == "8"


@pytest.mark.django_db
def test_recalculate_weekend_leave_hours_dry_run_execute_and_idempotent():
    user = make_user("command-weekend@example.com", includes_weekends=True)
    category = make_vacation_category()
    balance, _ = LeaveBalance.objects.update_or_create(
        user=user,
        year=2026,
        balance_type=LeaveBalance.BalanceType.VACATION,
        defaults={
            "allocated_hours": Decimal("8.00"),
            "used_hours": Decimal("0.00"),
            "adjusted_hours": Decimal("0.00"),
        },
    )
    leave = LeaveRequest.objects.create(
        user=user,
        leave_category=category,
        start_date=date(2026, 6, 13),
        end_date=date(2026, 6, 14),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal("0.00"),
        status=LeaveRequest.Status.APPROVED,
    )

    dry_run_out = StringIO()
    call_command("recalculate_weekend_leave_hours", "--year=2026", stdout=dry_run_out)
    leave.refresh_from_db()
    balance.refresh_from_db()
    assert leave.total_hours == Decimal("0.00")
    assert balance.used_hours == Decimal("0.00")
    assert "WENT NEGATIVE" in dry_run_out.getvalue()

    execute_out = StringIO()
    call_command("recalculate_weekend_leave_hours", "--year=2026", "--execute", stdout=execute_out)
    leave.refresh_from_db()
    balance.refresh_from_db()
    assert leave.total_hours == Decimal("16.00")
    assert balance.used_hours == Decimal("16.00")
    assert balance.remaining_hours == Decimal("-8.00")

    second_out = StringIO()
    call_command("recalculate_weekend_leave_hours", "--year=2026", "--execute", stdout=second_out)
    assert "Summary: 0 request(s) recalculated" in second_out.getvalue()


@pytest.mark.django_db
def test_recalculate_weekend_leave_hours_skips_approved_request_missing_balance():
    user = make_user("missing-balance@example.com", includes_weekends=True)
    category = make_vacation_category()
    LeaveBalance.objects.filter(user=user, year=2026).delete()
    leave = LeaveRequest.objects.create(
        user=user,
        leave_category=category,
        start_date=date(2026, 6, 13),
        end_date=date(2026, 6, 14),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal("0.00"),
        status=LeaveRequest.Status.APPROVED,
    )

    out = StringIO()
    call_command("recalculate_weekend_leave_hours", "--year=2026", "--execute", stdout=out)
    leave.refresh_from_db()

    assert leave.total_hours == Decimal("0.00")
    assert "MISSING BALANCE" in out.getvalue()
