"""Administrative holiday calendar API."""
from datetime import date

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Entity
from users.models import User
from users.permissions import IsHRAdmin

from ..holiday_management import (
    generation_preview,
    generate_draft_calendars,
    publish_impact,
    publish_calendar,
    unpublish_calendar,
    unpublish_impact,
    validate_holiday_dates,
)
from ..models import HolidayCalendar, PublicHoliday


def _calendar_data(calendar, include_holidays=False):
    data = {
        "id": str(calendar.id),
        "name": calendar.name,
        "country_code": calendar.country_code,
        "year": calendar.year,
        "status": calendar.status,
        "entity_id": str(calendar.entity_id),
        "entity_name": calendar.entity.entity_name,
        "location_id": str(calendar.location_id) if calendar.location_id else None,
        "location_name": calendar.location.location_name if calendar.location else None,
        "holiday_count": calendar.holidays.exclude(status=PublicHoliday.Status.ARCHIVED).count(),
        "published_at": calendar.published_at,
    }
    if include_holidays:
        data["holidays"] = [
            {
                "id": str(holiday.id),
                "holiday_name": holiday.holiday_name,
                "start_date": holiday.start_date,
                "end_date": holiday.end_date,
                "holiday_type": holiday.holiday_type,
                "status": holiday.status,
                "source_note": holiday.source_note,
            }
            for holiday in calendar.holidays.exclude(status=PublicHoliday.Status.ARCHIVED).order_by("start_date")
        ]
    return data


def _calendar_queryset(user):
    queryset = HolidayCalendar.objects.select_related("entity", "location")
    if user.role == User.Role.HR:
        return queryset.filter(entity=user.entity)
    return queryset


def _parse_date(value, field_name):
    try:
        return value if isinstance(value, date) else date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must use YYYY-MM-DD format")


def _generation_entities(request):
    entity_ids = request.data.get("entity_ids")
    if request.user.role == User.Role.HR:
        if not request.user.entity_id:
            return None, Response({"error": "HR user has no entity"}, status=status.HTTP_403_FORBIDDEN)
        if entity_ids and set(map(str, entity_ids)) != {str(request.user.entity_id)}:
            return None, Response(
                {"error": "HR can only generate calendars for their own entity"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Entity.objects.filter(id=request.user.entity_id, is_active=True), None
    entities = Entity.objects.filter(is_active=True)
    if entity_ids:
        entities = entities.filter(id__in=entity_ids)
    return entities, None


class HolidayCalendarListView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def get(self, request):
        queryset = _calendar_queryset(request.user)
        for field in ("year", "country_code", "status", "entity_id", "location_id"):
            value = request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        return Response({"results": [_calendar_data(calendar) for calendar in queryset]})


class HolidayCalendarGenerateView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def post(self, request):
        try:
            year = int(request.data["year"])
        except (KeyError, TypeError, ValueError):
            return Response({"error": "A valid year is required"}, status=status.HTTP_400_BAD_REQUEST)

        entities, error = _generation_entities(request)
        if error:
            return error
        calendars = generate_draft_calendars(
            year,
            entities,
            country_overrides=request.data.get("country_overrides") or {},
        )
        return Response(
            {"results": [_calendar_data(calendar, include_holidays=True) for calendar in calendars]},
            status=status.HTTP_201_CREATED,
        )


class HolidayCalendarGenerationPreviewView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def post(self, request):
        try:
            year = int(request.data["year"])
        except (KeyError, TypeError, ValueError):
            return Response({"error": "A valid year is required"}, status=status.HTTP_400_BAD_REQUEST)
        entities, error = _generation_entities(request)
        if error:
            return error
        return Response(
            {
                "results": generation_preview(
                    year,
                    entities,
                    country_overrides=request.data.get("country_overrides") or {},
                )
            }
        )


class HolidayCalendarDetailView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def get_object(self, request, pk):
        return _calendar_queryset(request.user).filter(pk=pk).first()

    def get(self, request, pk):
        calendar = self.get_object(request, pk)
        if not calendar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(_calendar_data(calendar, include_holidays=True))

    def patch(self, request, pk):
        calendar = self.get_object(request, pk)
        if not calendar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if calendar.status != HolidayCalendar.Status.DRAFT:
            return Response(
                {"error": "Published calendars must be unpublished before editing"},
                status=status.HTTP_409_CONFLICT,
            )
        calendar.name = request.data.get("name", calendar.name)
        calendar.save(update_fields=["name", "updated_at"])
        return Response(_calendar_data(calendar, include_holidays=True))


class HolidayCalendarPublishView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def post(self, request, pk):
        calendar = _calendar_queryset(request.user).filter(pk=pk).first()
        if not calendar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            result = publish_calendar(calendar, request.user)
        except (ValueError, PublicHoliday.DoesNotExist) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(result)


class HolidayCalendarPublishPreviewView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def post(self, request, pk):
        calendar = _calendar_queryset(request.user).filter(pk=pk).first()
        if not calendar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(publish_impact(calendar))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)


class HolidayCalendarUnpublishPreviewView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def post(self, request, pk):
        calendar = _calendar_queryset(request.user).filter(pk=pk).first()
        if not calendar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(unpublish_impact(calendar))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)


class HolidayCalendarUnpublishView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def post(self, request, pk):
        calendar = _calendar_queryset(request.user).filter(pk=pk).first()
        if not calendar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            result = unpublish_calendar(calendar, request.user, request.data.get("preview_token"))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(result)


class HolidayCalendarHolidayCreateView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def post(self, request, pk):
        calendar = _calendar_queryset(request.user).filter(pk=pk).first()
        if not calendar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if calendar.status != HolidayCalendar.Status.DRAFT:
            return Response({"error": "Only Draft calendars can be edited"}, status=status.HTTP_409_CONFLICT)
        try:
            holiday_name = request.data["holiday_name"].strip()
            if not holiday_name:
                raise ValueError("Holiday name is required")
            start_date = _parse_date(request.data["start_date"], "start_date")
            end_date = _parse_date(request.data.get("end_date", request.data["start_date"]), "end_date")
            validate_holiday_dates(calendar, start_date, end_date)
            holiday = PublicHoliday.objects.create(
                calendar=calendar,
                entity=calendar.entity,
                location=calendar.location,
                holiday_name=holiday_name,
                start_date=start_date,
                end_date=end_date,
                year=calendar.year,
                holiday_type=request.data.get("holiday_type", PublicHoliday.HolidayType.COMPANY),
                status=PublicHoliday.Status.DRAFT,
                source_note=request.data.get("source_note", ""),
            )
        except (KeyError, ValueError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"id": str(holiday.id)}, status=status.HTTP_201_CREATED)


class HolidayDetailView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def get_object(self, request, pk):
        queryset = PublicHoliday.objects.select_related("calendar")
        if request.user.role == User.Role.HR:
            queryset = queryset.filter(entity=request.user.entity)
        return queryset.filter(pk=pk).first()

    def patch(self, request, pk):
        holiday = self.get_object(request, pk)
        if not holiday:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if holiday.status != PublicHoliday.Status.DRAFT:
            return Response({"error": "Only Draft holidays can be edited"}, status=status.HTTP_409_CONFLICT)
        try:
            start_date = _parse_date(request.data.get("start_date", holiday.start_date), "start_date")
            end_date = _parse_date(request.data.get("end_date", holiday.end_date), "end_date")
            validate_holiday_dates(
                holiday.calendar,
                start_date,
                end_date,
                exclude_holiday_id=holiday.id,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        for field in ("holiday_name", "holiday_type", "source_note"):
            if field in request.data:
                setattr(holiday, field, request.data[field])
        holiday.start_date = start_date
        holiday.end_date = end_date
        holiday.save()
        return Response({"id": str(holiday.id)})

    def delete(self, request, pk):
        holiday = self.get_object(request, pk)
        if not holiday:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if holiday.status != PublicHoliday.Status.DRAFT:
            return Response({"error": "Only Draft holidays can be deleted"}, status=status.HTTP_409_CONFLICT)
        holiday.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
