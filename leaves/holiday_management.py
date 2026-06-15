"""Holiday template generation and publication services."""
from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone
from lunardate import LunarDate

from core.models import AuditLog
from organizations.models import Entity

from .models import (
    HolidayCalendar,
    HolidayTemplate,
    HolidayTemplateDate,
    PublicHoliday,
)
from .utils import normalize_country_code


OPM_URL = "https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/"
VN_SOURCE = "Vietnam Labor Code 2019, Article 112"


def _vn_template_rows(year):
    lunar_new_year = LunarDate(year, 1, 1).toSolarDate()
    hung_kings_day = LunarDate(year, 3, 10).toSolarDate()
    return [
        ("New Year's Day", f"{year}-01-01", "STATUTORY"),
        (
            "Lunar New Year",
            f"{lunar_new_year - timedelta(days=1)}/{lunar_new_year + timedelta(days=3)}",
            "STATUTORY",
        ),
        ("Hung Kings Commemoration Day", str(hung_kings_day), "STATUTORY"),
        ("Reunification Day", f"{year}-04-30", "STATUTORY"),
        ("International Labor Day", f"{year}-05-01", "STATUTORY"),
        ("National Day", f"{year}-09-01/{year}-09-02", "STATUTORY"),
    ]

TEMPLATE_DATA = {
    ("US", 2026): [
        ("New Year's Day", "2026-01-01", "STATUTORY"),
        ("Birthday of Martin Luther King, Jr.", "2026-01-19", "STATUTORY"),
        ("Washington's Birthday", "2026-02-16", "STATUTORY"),
        ("Memorial Day", "2026-05-25", "STATUTORY"),
        ("Juneteenth National Independence Day", "2026-06-19", "STATUTORY"),
        ("Independence Day, observed", "2026-07-03", "OBSERVED"),
        ("Labor Day", "2026-09-07", "STATUTORY"),
        ("Columbus Day", "2026-10-12", "STATUTORY"),
        ("Veterans Day", "2026-11-11", "STATUTORY"),
        ("Thanksgiving Day", "2026-11-26", "STATUTORY"),
        ("Christmas Day", "2026-12-25", "STATUTORY"),
    ],
    ("US", 2027): [
        ("New Year's Day", "2027-01-01", "STATUTORY"),
        ("Birthday of Martin Luther King, Jr.", "2027-01-18", "STATUTORY"),
        ("Washington's Birthday", "2027-02-15", "STATUTORY"),
        ("Memorial Day", "2027-05-31", "STATUTORY"),
        ("Juneteenth National Independence Day, observed", "2027-06-18", "OBSERVED"),
        ("Independence Day, observed", "2027-07-05", "OBSERVED"),
        ("Labor Day", "2027-09-06", "STATUTORY"),
        ("Columbus Day", "2027-10-11", "STATUTORY"),
        ("Veterans Day", "2027-11-11", "STATUTORY"),
        ("Thanksgiving Day", "2027-11-25", "STATUTORY"),
        ("Christmas Day, observed", "2027-12-24", "OBSERVED"),
    ],
    ("VN", 2026): [
        ("New Year's Day", "2026-01-01", "STATUTORY"),
        ("Lunar New Year", "2026-02-16/2026-02-20", "STATUTORY"),
        ("Hung Kings Commemoration Day", "2026-04-26", "STATUTORY"),
        ("Hung Kings Commemoration Day, compensatory day", "2026-04-27", "COMPENSATORY"),
        ("Reunification Day", "2026-04-30", "STATUTORY"),
        ("International Labor Day", "2026-05-01", "STATUTORY"),
        ("National Day", "2026-09-01/2026-09-02", "STATUTORY"),
    ],
}

for template_year in range(2027, 2036):
    TEMPLATE_DATA[("VN", template_year)] = _vn_template_rows(template_year)


def validate_holiday_dates(calendar, start_date, end_date, exclude_holiday_id=None):
    """Validate a Draft holiday date range and prevent overlapping holidays."""
    if end_date < start_date:
        raise ValueError("End date must be on or after start date")
    if start_date.year != calendar.year or end_date.year != calendar.year:
        raise ValueError(f"Holiday dates must remain within calendar year {calendar.year}")
    overlaps = calendar.holidays.exclude(status=PublicHoliday.Status.ARCHIVED).filter(
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_holiday_id:
        overlaps = overlaps.exclude(id=exclude_holiday_id)
    if overlaps.exists():
        raise ValueError("Holiday date range overlaps an existing holiday in this calendar")


def validate_publish_conflicts(calendar):
    """Prevent Published calendars in the same scope from covering the same date."""
    for holiday in calendar.holidays.exclude(status=PublicHoliday.Status.ARCHIVED):
        conflict = PublicHoliday.objects.filter(
            status=PublicHoliday.Status.PUBLISHED,
            entity_id=calendar.entity_id,
            location_id=calendar.location_id,
            start_date__lte=holiday.end_date,
            end_date__gte=holiday.start_date,
        ).exclude(calendar_id=calendar.id).first()
        if conflict:
            scope = calendar.location.location_name if calendar.location_id else calendar.entity.entity_name
            raise ValueError(
                f"{holiday.holiday_name} overlaps Published holiday "
                f"{conflict.holiday_name} for {scope}"
            )


def publish_impact(calendar):
    """Publishing holidays does not change leave requests or balances."""
    if calendar.status != HolidayCalendar.Status.DRAFT:
        raise ValueError("Only Draft calendars can be published")
    validate_publish_conflicts(calendar)
    return {"affected_requests": 0, "changes": []}


@transaction.atomic
def seed_holiday_templates():
    """Idempotently create reviewed reference templates."""
    templates = []
    for (country_code, year), rows in TEMPLATE_DATA.items():
        source_name = "U.S. Office of Personnel Management" if country_code == "US" else VN_SOURCE
        template, _ = HolidayTemplate.objects.update_or_create(
            country_code=country_code,
            year=year,
            version=1,
            defaults={
                "name": f"{country_code} {year} official holidays",
                "source_name": source_name,
                "source_url": OPM_URL if country_code == "US" else "",
            },
        )
        for holiday_name, date_value, holiday_type in rows:
            parts = date_value.split("/")
            start_date = date.fromisoformat(parts[0])
            end_date = date.fromisoformat(parts[-1])
            HolidayTemplateDate.objects.update_or_create(
                template=template,
                start_date=start_date,
                holiday_name=holiday_name,
                defaults={
                    "end_date": end_date,
                    "holiday_type": holiday_type,
                    "source_note": source_name,
                },
            )
        templates.append(template)
    return templates


def _target_scopes(entity, country_overrides=None):
    country_overrides = country_overrides or {}
    locations = list(entity.locations.filter(is_active=True))
    mapped = [
        (
            country_overrides.get(str(location.id))
            or normalize_country_code(location.country),
            location,
        )
        for location in locations
    ]
    country_codes = {country_code for country_code, _ in mapped}
    country_codes.discard(None)
    if locations and len(country_codes) == 1 and all(country_code for country_code, _ in mapped):
        return [(country_codes.pop(), None)]
    return [
        (country_code, location)
        for country_code, location in mapped
        if country_code
    ]


@transaction.atomic
def generate_draft_calendars(year, entities=None, country_overrides=None):
    """Copy supported templates into entity/location-scoped Draft calendars."""
    seed_holiday_templates()
    entities = entities if entities is not None else Entity.objects.filter(is_active=True)
    created = []
    for entity in entities:
        for country_code, location in _target_scopes(entity, country_overrides):
            template = HolidayTemplate.objects.filter(
                country_code=country_code, year=year
            ).order_by("-version").first()
            calendar, was_created = HolidayCalendar.objects.get_or_create(
                year=year,
                entity=entity,
                location=location,
                country_code=country_code,
                defaults={
                    "name": f"{entity.entity_name} - {location.location_name + ' - ' if location else ''}{country_code} {year}",
                    "source_template": template,
                    "status": HolidayCalendar.Status.DRAFT,
                },
            )
            if not was_created:
                continue
            if template:
                PublicHoliday.objects.bulk_create(
                    [
                        PublicHoliday(
                            calendar=calendar,
                            entity=entity,
                            location=location,
                            holiday_name=row.holiday_name,
                            start_date=row.start_date,
                            end_date=row.end_date,
                            year=year,
                            holiday_type=row.holiday_type,
                            status=PublicHoliday.Status.DRAFT,
                            source_note=row.source_note,
                        )
                        for row in template.dates.all()
                    ]
                )
            created.append(calendar)
    return created


def generation_preview(year, entities, country_overrides=None):
    """Describe normalized location mappings and proposed generation scopes."""
    seed_holiday_templates()
    country_overrides = country_overrides or {}
    results = []
    for entity in entities:
        locations = [
            {
                "id": str(location.id),
                "name": location.location_name,
                "country": location.country,
                "country_code": country_overrides.get(str(location.id))
                or normalize_country_code(location.country),
            }
            for location in entity.locations.filter(is_active=True)
        ]
        scopes = [
            {
                "country_code": country_code,
                "scope": "LOCATION" if location else "ENTITY",
                "location_id": str(location.id) if location else None,
                "location_name": location.location_name if location else None,
                "template_available": HolidayTemplate.objects.filter(
                    country_code=country_code, year=year
                ).exists(),
            }
            for country_code, location in _target_scopes(entity, country_overrides)
        ]
        results.append(
            {
                "entity_id": str(entity.id),
                "entity_name": entity.entity_name,
                "locations": locations,
                "proposed_scopes": scopes,
                "has_unknown_country": any(not row["country_code"] for row in locations),
            }
        )
    return results


@transaction.atomic
def split_future_entity_calendars(entity, today=None, actor=None):
    """Move future entity holidays to matching old-country locations after scope becomes mixed."""
    today = today or timezone.localdate()
    locations = list(entity.locations.filter(is_active=True))
    country_codes = {normalize_country_code(location.country) for location in locations}
    country_codes.discard(None)
    if len(country_codes) <= 1:
        return []

    created = []
    entity_calendars = HolidayCalendar.objects.select_for_update().filter(
        entity=entity,
        location__isnull=True,
    )
    for calendar in entity_calendars:
        future_holidays = list(
            calendar.holidays.select_for_update().filter(
                start_date__gt=today,
            ).exclude(status=PublicHoliday.Status.ARCHIVED)
        )
        if not future_holidays:
            continue
        target_locations = [
            location
            for location in locations
            if normalize_country_code(location.country) == calendar.country_code
        ]
        for location in target_locations:
            target, _ = HolidayCalendar.objects.get_or_create(
                year=calendar.year,
                entity=entity,
                location=location,
                country_code=calendar.country_code,
                defaults={
                    "name": f"{entity.entity_name} - {location.location_name} - {calendar.country_code} {calendar.year}",
                    "source_template": calendar.source_template,
                    "status": calendar.status,
                    "published_by": calendar.published_by,
                    "published_at": calendar.published_at,
                },
            )
            for holiday in future_holidays:
                PublicHoliday.objects.create(
                    calendar=target,
                    entity=entity,
                    location=location,
                    holiday_name=holiday.holiday_name,
                    start_date=holiday.start_date,
                    end_date=holiday.end_date,
                    year=holiday.year,
                    holiday_type=holiday.holiday_type,
                    status=holiday.status,
                    source_note=holiday.source_note,
                    published_by=holiday.published_by,
                    published_at=holiday.published_at,
                )
            created.append(target)
        calendar.holidays.filter(id__in=[holiday.id for holiday in future_holidays]).update(
            status=PublicHoliday.Status.ARCHIVED
        )
    if actor and created:
        AuditLog.objects.create(
            user=actor,
            action="SPLIT_SCOPE",
            entity_type="HolidayCalendar",
            entity_id=created[0].id,
            old_values={"holiday_scope": "ENTITY"},
            new_values={"holiday_scope": "LOCATION", "calendar_ids": [str(row.id) for row in created]},
        )
    return created


@transaction.atomic
def publish_calendar(calendar, actor):
    """Publish a Draft calendar without changing leave requests or balances."""
    calendar = HolidayCalendar.objects.select_for_update().get(pk=calendar.pk)
    if calendar.status != HolidayCalendar.Status.DRAFT:
        raise ValueError("Only Draft calendars can be published")
    holidays = list(calendar.holidays.exclude(status=PublicHoliday.Status.ARCHIVED))
    if not holidays:
        raise ValueError("Cannot publish an empty holiday calendar")
    for holiday in holidays:
        validate_holiday_dates(
            calendar,
            holiday.start_date,
            holiday.end_date,
            exclude_holiday_id=holiday.id,
        )
    validate_publish_conflicts(calendar)

    preview = publish_impact(calendar)
    now = timezone.now()
    calendar.holidays.filter(status=PublicHoliday.Status.DRAFT).update(
        status=PublicHoliday.Status.PUBLISHED,
        published_by=actor,
        published_at=now,
    )
    calendar.status = HolidayCalendar.Status.PUBLISHED
    calendar.published_by = actor
    calendar.published_at = now
    calendar.save(update_fields=["status", "published_by", "published_at", "updated_at"])
    AuditLog.objects.create(
        user=actor,
        action="PUBLISH",
        entity_type="HolidayCalendar",
        entity_id=calendar.id,
        old_values={"holiday_calendar_status": "DRAFT"},
        new_values={"holiday_calendar_status": "PUBLISHED", "affected_requests": []},
    )
    return preview


def _preview_token(calendar):
    return f"{calendar.id}:{calendar.updated_at.isoformat()}:{calendar.holidays.count()}"


def unpublish_impact(calendar):
    """Unpublishing holidays does not change leave requests or balances."""
    if calendar.status != HolidayCalendar.Status.PUBLISHED:
        raise ValueError("Only Published calendars can be unpublished")
    return {
        "preview_token": _preview_token(calendar),
        "affected_requests": 0,
        "blocked": False,
        "insufficient_balances": [],
        "changes": [],
    }


@transaction.atomic
def unpublish_calendar(calendar, actor, preview_token):
    """Return a Published calendar to Draft without changing leave or balances."""
    calendar = HolidayCalendar.objects.select_for_update().get(pk=calendar.pk)
    if preview_token != _preview_token(calendar):
        raise ValueError("Holiday calendar changed; generate a new unpublish preview")
    preview = unpublish_impact(calendar)
    if preview["blocked"]:
        raise ValueError("One or more employees have insufficient leave balance")

    calendar.holidays.filter(status=PublicHoliday.Status.PUBLISHED).update(
        status=PublicHoliday.Status.DRAFT,
        published_by=None,
        published_at=None,
    )
    calendar.status = HolidayCalendar.Status.DRAFT
    calendar.published_by = None
    calendar.published_at = None
    calendar.save(update_fields=["status", "published_by", "published_at", "updated_at"])
    AuditLog.objects.create(
        user=actor,
        action="UNPUBLISH",
        entity_type="HolidayCalendar",
        entity_id=calendar.id,
        old_values={"holiday_calendar_status": "PUBLISHED"},
        new_values={"holiday_calendar_status": "DRAFT", "affected_requests": preview["changes"]},
    )
    return preview
