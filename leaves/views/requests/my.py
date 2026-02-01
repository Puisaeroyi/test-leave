"""My leave requests view."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...serializers import LeaveRequestSerializer


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
            queryset = queryset.filter(start_date__year=int(year_filter))

        queryset = queryset.select_related('leave_category', 'approved_by').order_by('-created_at')

        serializer = LeaveRequestSerializer(queryset, many=True)
        return Response(serializer.data)
