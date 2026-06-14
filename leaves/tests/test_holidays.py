"""Regression tests for employee-facing published holiday listing."""
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from leaves.models import HolidayCalendar, PublicHoliday
from leaves.utils import get_holidays_for_user
from organizations.models import Department, Entity, Location, WorkShift


User = get_user_model()


@pytest.fixture
def holiday_scope():
    entity = Entity.objects.create(entity_name="Holiday Entity", code="HOL")
    location = Location.objects.create(
        entity=entity,
        location_name="Vietnam Office",
        city="Ho Chi Minh City",
        country="Vietnam",
        timezone="Asia/Ho_Chi_Minh",
    )
    user = User.objects.create_user(
        email="holiday-user@example.com",
        password="TestPass123!",
        entity=entity,
        location=location,
    )
    published = HolidayCalendar.objects.create(
        name="Published VN 2026",
        country_code="VN",
        year=2026,
        entity=entity,
        status=HolidayCalendar.Status.PUBLISHED,
    )
    draft = HolidayCalendar.objects.create(
        name="Draft VN 2027",
        country_code="VN",
        year=2027,
        entity=entity,
        status=HolidayCalendar.Status.DRAFT,
    )
    PublicHoliday.objects.create(
        calendar=published,
        entity=entity,
        holiday_name="Published Holiday",
        start_date=date(2026, 4, 30),
        end_date=date(2026, 5, 1),
        year=2026,
        status=PublicHoliday.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        calendar=draft,
        entity=entity,
        holiday_name="Draft Holiday",
        start_date=date(2027, 1, 1),
        end_date=date(2027, 1, 1),
        year=2027,
        status=PublicHoliday.Status.DRAFT,
    )
    return user


@pytest.mark.django_db
def test_list_returns_only_published_applicable_holidays(holiday_scope):
    client = APIClient()
    client.force_authenticate(holiday_scope)

    response = client.get("/api/v1/leaves/holidays/")

    assert response.status_code == 200
    assert [holiday["name"] for holiday in response.data] == ["Published Holiday"]
    assert response.data[0]["start_date"] == "2026-04-30"
    assert response.data[0]["end_date"] == "2026-05-01"


@pytest.mark.django_db
def test_list_filters_by_year(holiday_scope):
    client = APIClient()
    client.force_authenticate(holiday_scope)

    response = client.get("/api/v1/leaves/holidays/?year=2027")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_list_filters_entity_wide_holidays_by_user_location_country():
    entity = Entity.objects.create(entity_name="Global Holiday Entity", code="GHOL")
    vn_location = Location.objects.create(
        entity=entity,
        location_name="Vietnam Office",
        city="Ho Chi Minh City",
        country="Vietnam",
        timezone="Asia/Ho_Chi_Minh",
    )
    user = User.objects.create_user(
        email="vn-holiday-user@example.com",
        password="TestPass123!",
        entity=entity,
        location=vn_location,
    )
    vn_calendar = HolidayCalendar.objects.create(
        name="Entity VN 2027",
        country_code="VN",
        year=2027,
        entity=entity,
        status=HolidayCalendar.Status.PUBLISHED,
    )
    us_calendar = HolidayCalendar.objects.create(
        name="Entity US 2027",
        country_code="US",
        year=2027,
        entity=entity,
        status=HolidayCalendar.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        calendar=vn_calendar,
        entity=entity,
        holiday_name="Vietnam Holiday",
        start_date=date(2027, 4, 30),
        end_date=date(2027, 4, 30),
        year=2027,
        status=PublicHoliday.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        calendar=us_calendar,
        entity=entity,
        holiday_name="US Holiday",
        start_date=date(2027, 7, 5),
        end_date=date(2027, 7, 5),
        year=2027,
        status=PublicHoliday.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        holiday_name="Legacy Global US Holiday",
        start_date=date(2027, 11, 25),
        end_date=date(2027, 11, 25),
        year=2027,
        status=PublicHoliday.Status.PUBLISHED,
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/v1/leaves/holidays/?year=2027")
    applicable = get_holidays_for_user(user, date(2027, 1, 1), date(2027, 12, 31))

    assert response.status_code == 200
    assert [holiday["name"] for holiday in response.data] == ["Vietnam Holiday"]
    assert [holiday.holiday_name for holiday in applicable] == ["Vietnam Holiday"]


@pytest.mark.django_db
def test_team_calendar_filters_holidays_by_user_location_country():
    entity = Entity.objects.create(entity_name="Calendar Country Entity", code="CCAL")
    vn_location = Location.objects.create(
        entity=entity,
        location_name="Vietnam Office",
        city="Ho Chi Minh City",
        country="VN",
        timezone="Asia/Ho_Chi_Minh",
    )
    user = User.objects.create_user(
        email="vn-calendar-user@example.com",
        password="TestPass123!",
        entity=entity,
        location=vn_location,
    )
    vn_calendar = HolidayCalendar.objects.create(
        name="Entity VN 2027",
        country_code="VN",
        year=2027,
        entity=entity,
        status=HolidayCalendar.Status.PUBLISHED,
    )
    us_calendar = HolidayCalendar.objects.create(
        name="Entity US 2027",
        country_code="US",
        year=2027,
        entity=entity,
        status=HolidayCalendar.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        calendar=vn_calendar,
        entity=entity,
        holiday_name="Vietnam Calendar Holiday",
        start_date=date(2027, 4, 30),
        end_date=date(2027, 4, 30),
        year=2027,
        status=PublicHoliday.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        calendar=us_calendar,
        entity=entity,
        holiday_name="US Calendar Holiday",
        start_date=date(2027, 4, 30),
        end_date=date(2027, 4, 30),
        year=2027,
        status=PublicHoliday.Status.PUBLISHED,
    )
    PublicHoliday.objects.create(
        holiday_name="Legacy Global US Holiday",
        start_date=date(2027, 4, 30),
        end_date=date(2027, 4, 30),
        year=2027,
        status=PublicHoliday.Status.PUBLISHED,
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/v1/leaves/calendar/?month=4&year=2027")

    assert response.status_code == 200
    assert [holiday["name"] for holiday in response.data["holidays"]] == ["Vietnam Calendar Holiday"]


@pytest.mark.django_db
def test_team_calendar_returns_current_user_work_schedule_for_rotating_shift():
    entity = Entity.objects.create(entity_name="Schedule Entity", code="SCH")
    location = Location.objects.create(
        entity=entity,
        location_name="Vietnam Office",
        city="Ho Chi Minh City",
        country="VN",
        timezone="Asia/Ho_Chi_Minh",
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name="SOC",
        code="SOC",
    )
    shift = WorkShift.objects.create(
        department=department,
        name="SOC",
        pattern_type=WorkShift.PatternType.ROTATING_CYCLE,
        start_time="06:00",
        end_time="14:00",
        includes_weekends=True,
        cycle_days=[
            {"name": "Morning", "start_time": "06:00", "end_time": "14:00", "is_working": True},
            {"name": "Evening", "start_time": "14:00", "end_time": "22:00", "is_working": True},
            {"name": "Night", "start_time": "22:00", "end_time": "06:00", "is_working": True},
            {"name": "Off", "is_working": False},
        ],
    )
    user = User.objects.create_user(
        email="soc-calendar-user@example.com",
        password="TestPass123!",
        entity=entity,
        location=location,
        department=department,
        work_shift=shift,
        shift_cycle_start_date=date(2027, 7, 11),
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/v1/leaves/calendar/?month=7&year=2027")

    assert response.status_code == 200
    days = {item["date"]: item for item in response.data["work_schedule"]}
    assert days["2027-07-11"]["shift_name"] == "Morning"
    assert days["2027-07-11"]["start_time"] == "06:00"
    assert days["2027-07-12"]["shift_name"] == "Evening"
    assert days["2027-07-13"]["shift_name"] == "Night"
    assert days["2027-07-14"]["shift_name"] == "Off"
    assert days["2027-07-14"]["is_working"] is False
    assert days["2027-07-14"]["start_time"] is None
