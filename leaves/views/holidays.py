"""Public holiday views."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from ..models import PublicHoliday


class PublicHolidayListView(generics.ListAPIView):
    """List public holidays (read-only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/holidays/?year=2026"""
        user = request.user
        year = request.query_params.get('year')

        # Build query for holidays applicable to user's entity/location
        query = Q(entity__isnull=True) | Q(entity=user.entity_id)
        if user.location_id:
            query &= Q(location__isnull=True) | Q(location=user.location_id)

        holidays = PublicHoliday.objects.filter(query, is_active=True)

        if year:
            holidays = holidays.filter(year=int(year))

        holidays = holidays.order_by('start_date')

        data = [
            {
                'id': str(h.id),
                'name': h.holiday_name,
                'start_date': h.start_date.isoformat(),
                'end_date': h.end_date.isoformat(),
                'year': h.year,
                'is_recurring': h.is_recurring,
                'entity_id': str(h.entity_id) if h.entity_id else None,
                'location_id': str(h.location_id) if h.location_id else None,
            }
            for h in holidays
        ]
        return Response(data)
