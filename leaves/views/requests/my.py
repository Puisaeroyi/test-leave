"""My leave requests view."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...serializers import LeaveRequestSerializer
from .list_create import LEAVE_REQUEST_RELATED_FIELDS


class LeaveRequestMyView(generics.ListAPIView):
    """List current user's leave requests."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/requests/my/"""
        user = request.user
        status_filter = request.query_params.get('status')
        year_filter = request.query_params.get('year')

        queryset = LeaveRequest.objects.filter(user=user)

        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        if year_filter:
            try:
                year = int(year_filter)
                if 1900 <= year <= 2100:
                    queryset = queryset.filter(start_date__year=year)
            except (TypeError, ValueError):
                pass

        queryset = queryset.select_related(*LEAVE_REQUEST_RELATED_FIELDS).order_by('-created_at')

        serializer = LeaveRequestSerializer(
            queryset, many=True, context={'request': request, 'actor': user}
        )
        return Response(serializer.data)
