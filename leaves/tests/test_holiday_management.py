from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AuditLog, Notification, NotificationType
from leaves.models import (
    HolidayCalendar,
    HolidayTemplate,
    LeaveBalance,
    LeaveCategory,
    LeaveRequest,
    PublicHoliday,
)
from leaves.holiday_management import (
    generate_draft_calendars,
    normalize_country_code,
    publish_impact,
    publish_calendar,
    seed_holiday_templates,
    split_future_entity_calendars,
    unpublish_calendar,
    unpublish_impact,
    validate_holiday_dates,
)
from organizations.models import Department, Entity, Location


User = get_user_model()


def make_location(entity, name, country):
    return Location.objects.create(
        entity=entity,
        location_name=name,
        city=name,
        country=country,
        timezone="UTC",
    )


@pytest.mark.django_db
def test_seed_templates_contains_complete_supported_calendars():
    seed_holiday_templates()

    us_2026 = HolidayTemplate.objects.get(country_code="US", year=2026)
    us_2027 = HolidayTemplate.objects.get(country_code="US", year=2027)
    vn_2026 = HolidayTemplate.objects.get(country_code="VN", year=2026)

    assert us_2026.dates.count() == 11
    assert us_2027.dates.count() == 11
    assert vn_2026.dates.count() == 7
    assert us_2026.dates.filter(start_date=date(2026, 7, 3)).exists()
    assert vn_2026.dates.filter(
        start_date=date(2026, 2, 16),
        end_date=date(2026, 2, 20),
    ).exists()


@pytest.mark.django_db
def test_country_mapping_and_generation_uses_entity_or_location_scope():
    seed_holiday_templates()
    us_entity = Entity.objects.create(entity_name="US Co", code="USCO")
    make_location(us_entity, "New York", "United States of America")
    make_location(us_entity, "Texas", "USA")
    mixed_entity = Entity.objects.create(entity_name="Global Co", code="GLOBAL")
    us_location = make_location(mixed_entity, "California", "US")
    vn_location = make_location(mixed_entity, "Ho Chi Minh City", "Việt Nam")

    calendars = generate_draft_calendars(year=2026)

    assert normalize_country_code(" Viet Nam ") == "VN"
    assert normalize_country_code("United States") == "US"
    assert HolidayCalendar.objects.filter(
        entity=us_entity, location__isnull=True, country_code="US"
    ).exists()
    assert HolidayCalendar.objects.filter(
        entity=mixed_entity, location=us_location, country_code="US"
    ).exists()
    assert HolidayCalendar.objects.filter(
        entity=mixed_entity, location=vn_location, country_code="VN"
    ).exists()
    assert all(calendar.status == HolidayCalendar.Status.DRAFT for calendar in calendars)


@pytest.mark.django_db
def test_country_override_maps_unknown_location_before_generation():
    seed_holiday_templates()
    entity = Entity.objects.create(entity_name="Override Co", code="OVERRIDE")
    location = make_location(entity, "Unknown Office", "Unknown")

    calendars = generate_draft_calendars(
        year=2026,
        entities=Entity.objects.filter(id=entity.id),
        country_overrides={str(location.id): "VN"},
    )

    assert len(calendars) == 1
    assert calendars[0].location is None
    assert calendars[0].country_code == "VN"


@pytest.mark.django_db
def test_hr_can_only_list_and_generate_holidays_for_own_entity():
    seed_holiday_templates()
    own_entity = Entity.objects.create(entity_name="Own", code="OWN")
    other_entity = Entity.objects.create(entity_name="Other", code="OTHER")
    make_location(own_entity, "Own VN", "Vietnam")
    make_location(other_entity, "Other US", "USA")
    hr = User.objects.create_user(
        email="hr@example.com", password="Password123!", role=User.Role.HR, entity=own_entity
    )
    client = APIClient()
    client.force_authenticate(hr)

    forbidden = client.post(
        "/api/v1/leaves/holiday-calendars/generate/",
        {"year": 2026, "entity_ids": [str(other_entity.id)]},
        format="json",
    )
    allowed = client.post(
        "/api/v1/leaves/holiday-calendars/generate/",
        {"year": 2026},
        format="json",
    )
    listed = client.get("/api/v1/leaves/holiday-calendars/")

    assert forbidden.status_code == 403
    assert allowed.status_code == 201
    assert listed.status_code == 200
    assert {row["entity_id"] for row in listed.data["results"]} == {str(own_entity.id)}


@pytest.mark.django_db
def test_publish_recalculates_approved_leave_and_refunds_balance():
    entity = Entity.objects.create(entity_name="Publish Co", code="PUB")
    location = make_location(entity, "Publish Office", "USA")
    admin = User.objects.create_user(
        email="admin@example.com", password="Password123!", role=User.Role.ADMIN
    )
    employee = User.objects.create_user(
        email="employee@example.com",
        password="Password123!",
        entity=entity,
        location=location,
    )
    category, _ = LeaveCategory.objects.update_or_create(
        category_name="Vacation",
        defaults={
            "code": "VAC",
            "balance_bucket": LeaveCategory.BalanceBucket.VACATION,
        },
    )
    balance = LeaveBalance.objects.create(
        user=employee,
        year=2026,
        balance_type=LeaveBalance.BalanceType.VACATION,
        allocated_hours=Decimal("80.00"),
        used_hours=Decimal("16.00"),
    )
    leave = LeaveRequest.objects.create(
        user=employee,
        leave_category=category,
        start_date=date(2026, 7, 2),
        end_date=date(2026, 7, 3),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal("16.00"),
        status=LeaveRequest.Status.APPROVED,
    )
    calendar = HolidayCalendar.objects.create(
        name="US 2026",
        country_code="US",
        year=2026,
        entity=entity,
        status=HolidayCalendar.Status.DRAFT,
    )
    PublicHoliday.objects.create(
        calendar=calendar,
        entity=entity,
        holiday_name="Independence Day, observed",
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 3),
        year=2026,
        status=PublicHoliday.Status.DRAFT,
    )

    result = publish_calendar(calendar, admin)

    leave.refresh_from_db()
    balance.refresh_from_db()
    calendar.refresh_from_db()
    assert result["affected_requests"] == 1
    assert leave.total_hours == Decimal("8.00")
    assert balance.used_hours == Decimal("8.00")
    assert calendar.status == HolidayCalendar.Status.PUBLISHED


@pytest.mark.django_db
def test_unpublish_requires_current_preview_and_sufficient_balance():
    entity = Entity.objects.create(entity_name="Unpublish Co", code="UNPUB")
    location = make_location(entity, "Unpublish Office", "USA")
    admin = User.objects.create_user(
        email="unpublish-admin@example.com", password="Password123!", role=User.Role.ADMIN
    )
    employee = User.objects.create_user(
        email="unpublish-employee@example.com",
        password="Password123!",
        entity=entity,
        location=location,
    )
    category, _ = LeaveCategory.objects.update_or_create(
        category_name="Vacation",
        defaults={"code": "VAC", "balance_bucket": LeaveCategory.BalanceBucket.VACATION},
    )
    balance = LeaveBalance.objects.create(
        user=employee,
        year=2026,
        balance_type=LeaveBalance.BalanceType.VACATION,
        allocated_hours=Decimal("8.00"),
        used_hours=Decimal("8.00"),
    )
    leave = LeaveRequest.objects.create(
        user=employee,
        leave_category=category,
        start_date=date(2026, 7, 2),
        end_date=date(2026, 7, 3),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal("8.00"),
        status=LeaveRequest.Status.APPROVED,
    )
    calendar = HolidayCalendar.objects.create(
        name="US 2026 published",
        country_code="US",
        year=2026,
        entity=entity,
        status=HolidayCalendar.Status.PUBLISHED,
        published_by=admin,
    )
    PublicHoliday.objects.create(
        calendar=calendar,
        entity=entity,
        holiday_name="Independence Day, observed",
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 3),
        year=2026,
        status=PublicHoliday.Status.PUBLISHED,
    )

    preview = unpublish_impact(calendar)
    assert preview["affected_requests"] == 1
    assert preview["blocked"] is True

    balance.allocated_hours = Decimal("16.00")
    balance.save()
    preview = unpublish_impact(calendar)
    result = unpublish_calendar(calendar, admin, preview["preview_token"])

    leave.refresh_from_db()
    balance.refresh_from_db()
    calendar.refresh_from_db()
    assert result["affected_requests"] == 1
    assert leave.total_hours == Decimal("16.00")
    assert balance.used_hours == Decimal("16.00")
    assert calendar.status == HolidayCalendar.Status.DRAFT


@pytest.mark.django_db
def test_new_country_location_splits_only_future_entity_holidays():
    entity = Entity.objects.create(entity_name="Split Co", code="SPLIT")
    us_location = make_location(entity, "US Office", "USA")
    calendar = HolidayCalendar.objects.create(
        name="Split US 2027",
        country_code="US",
        year=2027,
        entity=entity,
        status=HolidayCalendar.Status.DRAFT,
    )
    past = PublicHoliday.objects.create(
        calendar=calendar,
        entity=entity,
        holiday_name="Past",
        start_date=date(2027, 1, 1),
        end_date=date(2027, 1, 1),
        year=2027,
        status=PublicHoliday.Status.DRAFT,
    )
    future = PublicHoliday.objects.create(
        calendar=calendar,
        entity=entity,
        holiday_name="Future",
        start_date=date(2027, 7, 5),
        end_date=date(2027, 7, 5),
        year=2027,
        status=PublicHoliday.Status.DRAFT,
    )
    make_location(entity, "VN Office", "Vietnam")

    split_future_entity_calendars(entity, today=date(2027, 2, 1))

    past.refresh_from_db()
    future.refresh_from_db()
    assert past.status == PublicHoliday.Status.DRAFT
    assert future.status == PublicHoliday.Status.ARCHIVED
    assert PublicHoliday.objects.filter(
        location=us_location,
        holiday_name="Future",
        status=PublicHoliday.Status.DRAFT,
    ).exists()


@pytest.mark.django_db
def test_holiday_validation_rejects_invalid_year_and_overlap():
    entity = Entity.objects.create(entity_name="Validation Co", code="VALID")
    calendar = HolidayCalendar.objects.create(
        name="Validation 2026",
        country_code="US",
        year=2026,
        entity=entity,
    )
    existing = PublicHoliday.objects.create(
        calendar=calendar,
        entity=entity,
        holiday_name="Existing",
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 4),
        year=2026,
        status=PublicHoliday.Status.DRAFT,
    )

    with pytest.raises(ValueError, match="End date"):
        validate_holiday_dates(calendar, date(2026, 7, 5), date(2026, 7, 4))
    with pytest.raises(ValueError, match="calendar year"):
        validate_holiday_dates(calendar, date(2027, 1, 1), date(2027, 1, 1))
    with pytest.raises(ValueError, match="overlaps"):
        validate_holiday_dates(calendar, date(2026, 7, 4), date(2026, 7, 5))

    validate_holiday_dates(
        calendar,
        date(2026, 7, 3),
        date(2026, 7, 4),
        exclude_holiday_id=existing.id,
    )


@pytest.mark.django_db
def test_publish_preview_does_not_mutate_and_publish_uses_specific_audit_and_notification():
    entity = Entity.objects.create(entity_name="Preview Co", code="PREVIEW")
    location = make_location(entity, "Preview Office", "USA")
    admin = User.objects.create_user(
        email="preview-admin@example.com", password="Password123!", role=User.Role.ADMIN
    )
    employee = User.objects.create_user(
        email="preview-employee@example.com",
        password="Password123!",
        entity=entity,
        location=location,
    )
    category, _ = LeaveCategory.objects.update_or_create(
        category_name="Vacation",
        defaults={"code": "VAC", "balance_bucket": LeaveCategory.BalanceBucket.VACATION},
    )
    LeaveBalance.objects.create(
        user=employee,
        year=2026,
        balance_type=LeaveBalance.BalanceType.VACATION,
        allocated_hours=Decimal("80.00"),
        used_hours=Decimal("16.00"),
    )
    leave = LeaveRequest.objects.create(
        user=employee,
        leave_category=category,
        start_date=date(2026, 7, 2),
        end_date=date(2026, 7, 3),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal("16.00"),
        status=LeaveRequest.Status.APPROVED,
    )
    calendar = HolidayCalendar.objects.create(
        name="Preview 2026",
        country_code="US",
        year=2026,
        entity=entity,
    )
    PublicHoliday.objects.create(
        calendar=calendar,
        entity=entity,
        holiday_name="Observed",
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 3),
        year=2026,
        status=PublicHoliday.Status.DRAFT,
    )

    preview = publish_impact(calendar)
    leave.refresh_from_db()
    calendar.refresh_from_db()
    assert preview["affected_requests"] == 1
    assert preview["changes"][0]["refunded_hours"] == "8.00"
    assert leave.total_hours == Decimal("16.00")
    assert calendar.status == HolidayCalendar.Status.DRAFT

    publish_calendar(calendar, admin)

    assert AuditLog.objects.filter(
        action="PUBLISH", entity_type="HolidayCalendar", entity_id=calendar.id
    ).exists()
    assert Notification.objects.filter(
        user=employee, type=NotificationType.LEAVE_HOURS_RECALCULATED
    ).exists()


@pytest.mark.django_db
def test_publish_rejects_overlap_with_published_calendar_in_same_scope():
    entity = Entity.objects.create(entity_name="Conflict Co", code="CONFLICT")
    admin = User.objects.create_user(
        email="conflict-admin@example.com", password="Password123!", role=User.Role.ADMIN
    )
    published = HolidayCalendar.objects.create(
        name="Published US 2026",
        country_code="US",
        year=2026,
        entity=entity,
        status=HolidayCalendar.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        calendar=published,
        entity=entity,
        holiday_name="Existing holiday",
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 3),
        year=2026,
        status=PublicHoliday.Status.PUBLISHED,
    )
    draft = HolidayCalendar.objects.create(
        name="Draft US 2026",
        country_code="US",
        year=2026,
        entity=entity,
        status=HolidayCalendar.Status.DRAFT,
    )
    PublicHoliday.objects.create(
        calendar=draft,
        entity=entity,
        holiday_name="Conflicting holiday",
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 4),
        year=2026,
        status=PublicHoliday.Status.DRAFT,
    )

    with pytest.raises(ValueError, match="overlaps Published holiday"):
        publish_calendar(draft, admin)


@pytest.mark.django_db
def test_publish_does_not_refund_leave_for_department_requiring_leave_on_holidays():
    entity = Entity.objects.create(entity_name="24/7 Co", code="247")
    location = make_location(entity, "Operations", "USA")
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name="Continuous Operations",
        code="OPS",
        holiday_requires_leave=True,
    )
    admin = User.objects.create_user(
        email="ops-admin@example.com", password="Password123!", role=User.Role.ADMIN
    )
    employee = User.objects.create_user(
        email="ops@example.com",
        password="Password123!",
        entity=entity,
        location=location,
        department=department,
    )
    leave = LeaveRequest.objects.create(
        user=employee,
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 3),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal("8.00"),
        status=LeaveRequest.Status.PENDING,
    )
    calendar = HolidayCalendar.objects.create(
        name="US 2026 Draft",
        country_code="US",
        year=2026,
        entity=entity,
        status=HolidayCalendar.Status.DRAFT,
    )
    PublicHoliday.objects.create(
        calendar=calendar,
        entity=entity,
        holiday_name="Independence Day observed",
        start_date=date(2026, 7, 3),
        end_date=date(2026, 7, 3),
        year=2026,
        status=PublicHoliday.Status.DRAFT,
    )

    preview = publish_impact(calendar)
    publish_calendar(calendar, admin)
    leave.refresh_from_db()

    assert preview["affected_requests"] == 0
    assert leave.total_hours == Decimal("8.00")
