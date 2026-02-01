"""Leave request list and create views."""

from datetime import datetime
from decimal import Decimal
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from ...models import LeaveRequest, LeaveBalance
from ...serializers import LeaveRequestSerializer
from ...services import LeaveApprovalService
from ...constants import DEFAULT_PAGE_SIZE, DEFAULT_YEARLY_ALLOCATION
from ...utils import (
    check_overlapping_requests,
    calculate_leave_hours,
    validate_leave_request_dates
)


class LeaveRequestListView(generics.ListCreateAPIView):
    """List and create leave requests."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/requests/?status=pending&year=2026&my=true"""
        user = request.user
        my_only = request.query_params.get('my', 'true').lower() == 'true'
        status_filter = request.query_params.get('status')
        year_filter = request.query_params.get('year')
        history_only = request.query_params.get('history', 'false').lower() == 'true'

        # Check if this is a history request for managers
        if history_only:
            queryset = LeaveApprovalService.get_approval_history_for_manager(user)
        # Check if this is a pending approvals request for managers
        elif status_filter == 'pending' and not my_only:
            queryset = LeaveApprovalService.get_pending_requests_for_manager(user)
        elif my_only:
            # Get user's own requests
            queryset = LeaveRequest.objects.filter(user=user)
        else:
            # HR/Admin can see all
            if user.role in ['HR', 'ADMIN']:
                queryset = LeaveRequest.objects.all()
            else:
                queryset = LeaveRequest.objects.filter(user=user)

        # Apply filters
        if status_filter and status_filter != 'pending':
            queryset = queryset.filter(status=status_filter.upper())
        if year_filter:
            queryset = queryset.filter(start_date__year=int(year_filter))

        queryset = queryset.select_related('user', 'leave_category', 'approved_by').order_by('-created_at')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        items = queryset[start:end]

        serializer = LeaveRequestSerializer(items, many=True)
        return Response({
            'count': total,
            'next': f"?page={page+1}&page_size={page_size}" if end < total else None,
            'previous': f"?page={page-1}&page_size={page_size}" if page > 1 else None,
            'results': serializer.data
        })

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/ - Create a new leave request"""
        user = request.user
        data = request.data

        # Parse dates
        try:
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate dates
        is_valid, error = validate_leave_request_dates(start_date, end_date)
        if not is_valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Check for overlapping requests
        overlapping = check_overlapping_requests(user, start_date, end_date)
        if overlapping.exists():
            return Response(
                {'error': 'You have an overlapping leave request for these dates'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse shift type and times
        shift_type = data.get('shift_type', 'FULL_DAY')
        start_time = None
        end_time = None

        if shift_type == 'CUSTOM_HOURS':
            try:
                start_time = datetime.strptime(data.get('start_time'), '%H:%M').time()
                end_time = datetime.strptime(data.get('end_time'), '%H:%M').time()
            except (ValueError, TypeError):
                return Response(
                    {'error': 'start_time and end_time required for CUSTOM_HOURS (format: HH:MM)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Calculate hours
        try:
            total_hours = calculate_leave_hours(user, start_date, end_date, shift_type, start_time, end_time)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Check balance
        year = start_date.year
        balance, _ = LeaveBalance.objects.get_or_create(
            user=user,
            year=year,
            defaults={'allocated_hours': Decimal(str(DEFAULT_YEARLY_ALLOCATION))}
        )

        if total_hours > balance.remaining_hours:
            return Response(
                {'error': f'Insufficient balance. Requested: {total_hours}h, Available: {balance.remaining_hours}h'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create request
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_category_id=data.get('leave_category') or data.get('leave_category_id'),
            start_date=start_date,
            end_date=end_date,
            shift_type=shift_type,
            start_time=start_time,
            end_time=end_time,
            total_hours=total_hours,
            reason=data.get('reason', ''),
            attachment_url=data.get('attachment_url', ''),
            status='PENDING'
        )

        serializer = LeaveRequestSerializer(leave_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
