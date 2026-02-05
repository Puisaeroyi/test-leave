"""Team calendar views."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model

from ..models import LeaveRequest, PublicHoliday, BusinessTrip
from ..constants import DEFAULT_MONTH, DEFAULT_YEAR

User = get_user_model()


class TeamCalendarView(generics.GenericAPIView):
    """Get team calendar data for a specific month."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Return team members, their approved leaves, and holidays for the month."""
        # Get query parameters
        month = int(request.query_params.get('month', DEFAULT_MONTH))
        year = int(request.query_params.get('year', DEFAULT_YEAR))
        member_ids = request.query_params.getlist('member_ids', [])

        # Get current user
        user = request.user

        # Get team members (same entity+location+department) + direct subordinates (cross-entity)
        team_filters = Q(entity_id=user.entity_id)
        if user.location_id:
            team_filters &= Q(location_id=user.location_id)
        if user.department_id:
            team_filters &= Q(department_id=user.department_id)

        subordinate_filter = Q(approver=user)
        team_members = User.objects.filter(team_filters | subordinate_filter).filter(is_active=True).distinct()

        # Filter by specific member IDs if provided
        if member_ids:
            team_members = team_members.filter(id__in=member_ids)

        # Generate colors for team members
        team_colors = [
            {'bg': '#3B82F6', 'dot': '#60A5FA', 'text': '#60A5FA'},  # blue
            {'bg': '#10B981', 'dot': '#34D399', 'text': '#34D399'},  # green
            {'bg': '#8B5CF6', 'dot': '#A78BFA', 'text': '#A78BFA'},  # purple
            {'bg': '#F97316', 'dot': '#FB923C', 'text': '#FB923C'},  # orange
            {'bg': '#EC4899', 'dot': '#F472B6', 'text': '#F472B6'},  # pink
            {'bg': '#14B8A6', 'dot': '#2DD4BF', 'text': '#2DD4BF'},  # teal
        ]

        # Prepare team members data
        team_data = []
        for idx, member in enumerate(team_members):
            color = team_colors[idx % len(team_colors)]
            team_data.append({
                'id': str(member.id),
                'name': member.get_full_name() or member.email,
                'color': color['bg'],
                'is_current_user': member.id == user.id
            })

        # Get approved leaves for team members in the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        member_id_list = [m['id'] for m in team_data]

        # Get approved leaves (business trips are now separate)
        leaves_query = LeaveRequest.objects.filter(
            user_id__in=member_id_list,
            status='APPROVED'
        ).filter(
            Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
        ).select_related('leave_category', 'user')

        leaves_data = []
        for leave in leaves_query:
            leaves_data.append({
                'id': str(leave.id),
                'member_id': str(leave.user_id),
                'member_name': leave.user.get_full_name() or leave.user.email,
                'start_date': leave.start_date.isoformat(),
                'end_date': leave.end_date.isoformat(),
                'is_full_day': leave.shift_type == 'FULL_DAY',
                'start_time': leave.start_time.strftime('%H:%M') if leave.start_time else None,
                'end_time': leave.end_time.strftime('%H:%M') if leave.end_time else None,
                'category': leave.leave_category.category_name if leave.leave_category else 'Leave',
                'total_hours': float(leave.total_hours)
            })

        # Get approved business trips for team members in the month
        trips_query = BusinessTrip.objects.filter(
            user_id__in=member_id_list
        ).filter(
            Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
        ).select_related('user')

        business_trips_data = []
        for trip in trips_query:
            business_trips_data.append({
                'id': str(trip.id),
                'member_id': str(trip.user_id),
                'member_name': trip.user.get_full_name() or trip.user.email,
                'start_date': trip.start_date.isoformat(),
                'end_date': trip.end_date.isoformat(),
                'city': trip.city,
                'country': trip.country,
                'note': trip.note or 'Business Trip'
            })

        # Get holidays for the month (supports multi-day holidays)
        holidays_query = PublicHoliday.objects.filter(
            is_active=True
        ).filter(
            Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
        ).filter(
            Q(entity_id=user.entity_id) | Q(entity_id__isnull=True)
        )

        # Filter by location if applicable
        if user.location_id:
            holidays_query = holidays_query.filter(
                Q(location_id=user.location_id) | Q(location_id__isnull=True)
            )

        holidays_data = [
            {
                'start_date': holiday.start_date.isoformat(),
                'end_date': holiday.end_date.isoformat(),
                'name': holiday.holiday_name
            }
            for holiday in holidays_query
        ]

        return Response({
            'month': month,
            'year': year,
            'team_members': team_data,
            'leaves': leaves_data,
            'business_trips': business_trips_data,
            'holidays': holidays_data
        }, status=status.HTTP_200_OK)
