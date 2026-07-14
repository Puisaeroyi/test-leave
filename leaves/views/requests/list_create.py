"""Leave request list and create views."""

from datetime import datetime
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q

from ...models import LeaveRequest, LeaveBalance, LeaveCategory
from ...serializers import LeaveRequestSerializer
from ...services import LeaveApprovalService, BalanceCalculationService
from ...constants import DEFAULT_PAGE_SIZE
from ...utils import (
    check_overlapping_requests,
    calculate_leave_hours,
    calculate_full_day_leave_breakdown,
    check_overlapping_custom_hours,
    infer_custom_hour_offsets,
    ZERO_DEDUCTIBLE_HOURS_MESSAGE,
    validate_leave_request_dates,
    validate_attachment_url
)
from users.models import User
from core.services.notification_service import create_leave_pending_notification
from core.services.email_service import send_leave_pending_email, send_leave_submitted_email
import logging
logger = logging.getLogger(__name__)

LEAVE_REQUEST_RELATED_FIELDS = (
    'user',
    'user__location',
    'user__department',
    'user__approver_1',
    'user__approver_2',
    'leave_category',
    'approved_by',
    'first_approver',
    'final_approver',
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
            # HR/Admin see requests within their entity only
            if user.role in [User.Role.HR, User.Role.ADMIN]:
                queryset = LeaveRequest.objects.filter(user__entity=user.entity)
            else:
                queryset = LeaveRequest.objects.filter(user=user)

        # Apply filters
        if status_filter and status_filter != 'pending':
            queryset = queryset.filter(status=status_filter.upper())
        if year_filter:
            try:
                year_val = int(year_filter)
                if 1900 <= year_val <= 2100:
                    queryset = queryset.filter(start_date__year=year_val)
            except (ValueError, TypeError):
                pass

        queryset = queryset.select_related(*LEAVE_REQUEST_RELATED_FIELDS).order_by('-created_at')

        # Pagination with DoS protection
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))))
        except (ValueError, TypeError):
            page = 1
            page_size = DEFAULT_PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        items = queryset[start:end]

        serializer = LeaveRequestSerializer(
            items, many=True, context={'request': request, 'actor': user}
        )
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

        if not user.approver_1_id and not user.approver_2_id:
            return Response(
                {
                    'error': (
                        'Cannot submit leave request because no approver is assigned. '
                        'Please contact HR.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        shift_type = data.get('shift_type', 'FULL_DAY')
        if shift_type not in LeaveRequest.ShiftType.values:
            return Response(
                {'error': 'Invalid shift_type. Must be FULL_DAY or CUSTOM_HOURS'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Full-day requests conflict by work date. Custom-hour requests need the
        # actual calendar-time comparison below, but still conflict with full days.
        overlapping = check_overlapping_requests(user, start_date, end_date)
        has_date_conflict = (
            overlapping.exists()
            if shift_type != 'CUSTOM_HOURS'
            else overlapping.exclude(shift_type=LeaveRequest.ShiftType.CUSTOM_HOURS).exists()
        )
        if has_date_conflict:
            return Response(
                {'error': 'You have an overlapping leave request for these dates'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse shift type and times
        start_time = None
        end_time = None
        start_day_offset = 0
        end_day_offset = 0

        if shift_type == 'CUSTOM_HOURS':
            try:
                start_time = datetime.strptime(data.get('start_time'), '%H:%M').time()
                end_time = datetime.strptime(data.get('end_time'), '%H:%M').time()
                if user.work_shift_id:
                    start_day_offset, end_day_offset = infer_custom_hour_offsets(
                        user, start_time, end_time
                    )
                else:
                    start_day_offset = int(data.get('start_day_offset', 0))
                    end_day_offset = int(data.get('end_day_offset', 0))
            except (ValueError, TypeError):
                return Response(
                    {'error': 'start_time and end_time required for CUSTOM_HOURS (format: HH:MM)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if check_overlapping_custom_hours(
                user, start_date, start_time, end_time, start_day_offset, end_day_offset
            ):
                return Response(
                    {'error': 'You have an overlapping custom-hours leave request'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Validate attachment URL if provided
        attachment_url = data.get('attachment_url', '')
        is_valid, error = validate_attachment_url(attachment_url)
        if not is_valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Block submissions from deactivated entities
        if user.entity and not user.entity.is_active:
            return Response(
                {'error': 'Your entity has been deactivated. Cannot submit leave requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Calculate hours
        try:
            if shift_type == 'FULL_DAY':
                total_hours, leave_breakdown = calculate_full_day_leave_breakdown(
                    user, start_date, end_date,
                )
            else:
                total_hours = calculate_leave_hours(
                    user, start_date, end_date, shift_type, start_time, end_time,
                    start_day_offset=start_day_offset, end_day_offset=end_day_offset,
                )
                leave_breakdown = []
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if total_hours <= 0:
            return Response(
                {'error': ZERO_DEDUCTIBLE_HOURS_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )

        category_id = data.get('leave_category') or data.get('leave_category_id')
        leave_category = LeaveCategory.objects.filter(id=category_id).first() if category_id else None
        if category_id and leave_category is None:
            return Response(
                {'error': 'Invalid leave category'},
                status=status.HTTP_400_BAD_REQUEST
            )
        balance_type = BalanceCalculationService.calculate_balance_type(leave_category)

        # Check balance + create request inside transaction to prevent race conditions
        year = start_date.year

        try:
            with transaction.atomic():
                if balance_type != 'NONE':
                    default_hours = BalanceCalculationService.calculate_default_allocation(
                        balance_type, user, year
                    )
                    # Lock balance row to prevent concurrent overdraw
                    balance, _ = LeaveBalance.objects.select_for_update().get_or_create(
                        user=user,
                        year=year,
                        balance_type=balance_type,
                        defaults={'allocated_hours': default_hours}
                    )

                    if total_hours > balance.remaining_hours:
                        return Response(
                            {'error': f'Insufficient balance. Requested: {total_hours}h, Available: {balance.remaining_hours}h'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # Create request inside same transaction
                leave_request = LeaveRequest.objects.create(
                    user=user,
                    leave_category_id=category_id,
                    balance_type_snapshot=balance_type,
                    start_date=start_date,
                    end_date=end_date,
                    shift_type=shift_type,
                    start_time=start_time,
                    end_time=end_time,
                    start_day_offset=start_day_offset,
                    end_day_offset=end_day_offset,
                    total_hours=total_hours,
                    leave_breakdown=leave_breakdown,
                    reason=data.get('reason', ''),
                    attachment_url=attachment_url,
                    status='PENDING',
                    first_approver=user.approver_1,
                    final_approver=user.approver_2,
                )
        except Exception as e:
            logger.error(f"Error creating leave request: {e}")
            return Response(
                {'error': 'Failed to create leave request. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Notify assigned peers once at creation.
        for peer in (user.approver_1, user.approver_2):
            if peer:
                create_leave_pending_notification(peer, leave_request)
                send_leave_pending_email(peer, leave_request)
        send_leave_submitted_email(leave_request)

        serializer = LeaveRequestSerializer(
            leave_request, context={'request': request, 'actor': user}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
