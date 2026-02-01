"""Public holiday views."""

from datetime import datetime
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from ..models import PublicHoliday


class PublicHolidayListView(generics.ListCreateAPIView):
    """List and create public holidays."""

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

        holidays = holidays.order_by('date')

        data = [
            {
                'id': str(h.id),
                'name': h.holiday_name,
                'date': h.date.isoformat(),
                'year': h.year,
                'is_recurring': h.is_recurring,
                'entity_id': str(h.entity_id) if h.entity_id else None,
                'location_id': str(h.location_id) if h.location_id else None,
            }
            for h in holidays
        ]
        return Response(data)

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/holidays/ - Create holiday (HR/Admin only)"""
        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can create holidays'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data

        # Parse date
        try:
            date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        holiday = PublicHoliday.objects.create(
            holiday_name=data.get('name'),
            date=date,
            year=data.get('year', date.year),
            is_recurring=data.get('is_recurring', False),
            entity_id=data.get('entity_id'),
            location_id=data.get('location_id'),
            is_active=True
        )

        return Response({
            'id': str(holiday.id),
            'name': holiday.holiday_name,
            'date': holiday.date.isoformat(),
            'year': holiday.year,
            'is_recurring': holiday.is_recurring,
        }, status=status.HTTP_201_CREATED)


class PublicHolidayDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Public holiday detail view."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/holidays/{id}/"""
        holiday_id = kwargs.get('pk')
        try:
            holiday = PublicHoliday.objects.get(id=holiday_id)
        except PublicHoliday.DoesNotExist:
            return Response(
                {'error': 'Holiday not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'id': str(holiday.id),
            'name': holiday.holiday_name,
            'date': holiday.date.isoformat(),
            'year': holiday.year,
            'is_recurring': holiday.is_recurring,
            'entity_id': str(holiday.entity_id) if holiday.entity_id else None,
            'location_id': str(holiday.location_id) if holiday.location_id else None,
            'is_active': holiday.is_active,
        })

    def put(self, request, *args, **kwargs):
        """PUT /api/v1/leaves/holidays/{id}/ - Update holiday (HR/Admin only)"""
        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can update holidays'},
                status=status.HTTP_403_FORBIDDEN
            )

        holiday_id = kwargs.get('pk')
        try:
            holiday = PublicHoliday.objects.get(id=holiday_id)
        except PublicHoliday.DoesNotExist:
            return Response(
                {'error': 'Holiday not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data

        # Update fields
        if 'name' in data:
            holiday.holiday_name = data['name']
        if 'date' in data:
            try:
                holiday.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if 'year' in data:
            holiday.year = data['year']
        if 'is_recurring' in data:
            holiday.is_recurring = data['is_recurring']
        if 'is_active' in data:
            holiday.is_active = data['is_active']

        holiday.save()

        return Response({
            'id': str(holiday.id),
            'name': holiday.holiday_name,
            'date': holiday.date.isoformat(),
            'year': holiday.year,
            'is_recurring': holiday.is_recurring,
            'is_active': holiday.is_active,
        })

    def delete(self, request, *args, **kwargs):
        """DELETE /api/v1/leaves/holidays/{id}/ - Delete holiday (HR/Admin only)"""
        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can delete holidays'},
                status=status.HTTP_403_FORBIDDEN
            )

        holiday_id = kwargs.get('pk')
        try:
            holiday = PublicHoliday.objects.get(id=holiday_id)
            holiday.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PublicHoliday.DoesNotExist:
            return Response(
                {'error': 'Holiday not found'},
                status=status.HTTP_404_NOT_FOUND
            )
