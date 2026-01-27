"""
Leave Management API Views
"""
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F
from .models import LeaveRequest, LeaveCategory, PublicHoliday
from .serializers import (
    LeaveRequestSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestUpdateSerializer,
    LeaveRequestApproveSerializer,
    LeaveRequestRejectSerializer
)
from .services import LeaveApprovalService
from core.models import Notification


class TeamCalendarView(generics.GenericAPIView):
    """Get team calendar data for a specific month"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Return team members, their approved leaves, and holidays for the month"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get query parameters
        month = int(request.query_params.get('month', 1))
        year = int(request.query_params.get('year', 2026))
        member_ids = request.query_params.getlist('member_ids', [])

        # Get current user
        user = request.user

        # Get team members (same entity, location, department)
        team_filters = Q(entity_id=user.entity_id)
        if user.location_id:
            team_filters &= Q(location_id=user.location_id)
        if user.department_id:
            team_filters &= Q(department_id=user.department_id)

        team_members = User.objects.filter(team_filters).filter(is_active=True)

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

        leaves_query = LeaveRequest.objects.filter(
            user_id__in=member_id_list,
            status='APPROVED'
        ).filter(
            Q(start_date__lt=end_date) & Q(end_date__gte=start_date)
        ).select_related('leave_category', 'user')

        leaves_data = []
        for leave in leaves_query:
            leaves_data.append({
                'id': str(leave.id),
                'member_id': str(leave.user_id),
                'start_date': leave.start_date.isoformat(),
                'end_date': leave.end_date.isoformat(),
                'is_full_day': leave.shift_type == 'FULL_DAY',
                'start_time': leave.start_time.strftime('%H:%M') if leave.start_time else None,
                'end_time': leave.end_time.strftime('%H:%M') if leave.end_time else None,
                'category': leave.leave_category.name if leave.leave_category else 'Leave',
                'total_hours': float(leave.total_hours)
            })

        # Get holidays for the month
        holidays_query = PublicHoliday.objects.filter(
            date__year=year,
            date__month=month,
            is_active=True
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
                'date': holiday.date.isoformat(),
                'name': holiday.name
            }
            for holiday in holidays_query
        ]

        return Response({
            'month': month,
            'year': year,
            'team_members': team_data,
            'leaves': leaves_data,
            'holidays': holidays_data
        }, status=status.HTTP_200_OK)


class LeaveCategoryListView(generics.ListAPIView):
    """List leave categories"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/categories/"""
        categories = LeaveCategory.objects.filter(is_active=True).order_by('sort_order')
        data = [
            {
                'id': str(cat.id),
                'name': cat.name,
                'code': cat.code,
                'color': cat.color,
                'requires_document': cat.requires_document
            }
            for cat in categories
        ]
        return Response(data)


class LeaveBalanceMeView(generics.RetrieveAPIView):
    """Get current user's leave balance"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/balances/me/?year=2026"""
        from leaves.models import LeaveBalance
        from django.utils import timezone
        from decimal import Decimal

        year = int(request.query_params.get('year', timezone.now().year))
        user = request.user

        # Get or create balance for this year
        balance, created = LeaveBalance.objects.get_or_create(
            user=user,
            year=year,
            defaults={'allocated_hours': Decimal('96.00')}
        )

        return Response({
            'id': str(balance.id),
            'year': balance.year,
            'allocated_hours': float(balance.allocated_hours),
            'used_hours': float(balance.used_hours),
            'adjusted_hours': float(balance.adjusted_hours),
            'remaining_hours': float(balance.remaining_hours),
            'remaining_days': float(balance.remaining_hours) / 8,
        })


class LeaveBalanceListView(generics.ListAPIView):
    """List all leave balances (HR/Admin)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/balances/?year=2026"""
        from leaves.models import LeaveBalance
        from django.utils import timezone

        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can view all balances'},
                status=status.HTTP_403_FORBIDDEN
            )

        year = int(request.query_params.get('year', timezone.now().year))
        balances = LeaveBalance.objects.filter(year=year).select_related('user')

        data = [
            {
                'id': str(b.id),
                'user_id': str(b.user.id),
                'user_email': b.user.email,
                'user_name': f"{b.user.first_name} {b.user.last_name}".strip() or b.user.email,
                'year': b.year,
                'allocated_hours': float(b.allocated_hours),
                'used_hours': float(b.used_hours),
                'adjusted_hours': float(b.adjusted_hours),
                'remaining_hours': float(b.remaining_hours),
            }
            for b in balances
        ]
        return Response(data)


class LeaveBalanceAdjustView(generics.GenericAPIView):
    """Adjust user leave balance (HR only)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/balances/{user_id}/adjust/"""
        from leaves.models import LeaveBalance
        from django.utils import timezone
        from decimal import Decimal

        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can adjust balances'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = kwargs.get('user_id')
        year = int(request.data.get('year', timezone.now().year))
        reason = request.data.get('reason', '')

        if not reason:
            return Response(
                {'error': 'Reason is required for adjustment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            balance = LeaveBalance.objects.get(user_id=user_id, year=year)
        except LeaveBalance.DoesNotExist:
            return Response(
                {'error': 'Balance not found for this user/year'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Adjust allocated hours if provided
        if 'allocated_hours' in request.data:
            balance.allocated_hours = Decimal(str(request.data['allocated_hours']))

        # Add adjustment hours if provided
        if 'adjustment_hours' in request.data:
            balance.adjusted_hours += Decimal(str(request.data['adjustment_hours']))

        balance.save()

        # Create notification
        try:
            Notification.objects.create(
                user_id=user_id,
                type='BALANCE_ADJUSTED',
                title='Leave Balance Adjusted',
                message=f'Your leave balance has been adjusted. Reason: {reason}',
                link='/leaves/balance'
            )
        except Exception:
            pass  # Notification is optional

        return Response({
            'id': str(balance.id),
            'year': balance.year,
            'allocated_hours': float(balance.allocated_hours),
            'used_hours': float(balance.used_hours),
            'adjusted_hours': float(balance.adjusted_hours),
            'remaining_hours': float(balance.remaining_hours),
        })


class LeaveRequestListView(generics.ListCreateAPIView):
    """List and create leave requests"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/requests/?status=pending&year=2026&my=true"""
        from .utils import check_overlapping_requests

        user = request.user
        my_only = request.query_params.get('my', 'true').lower() == 'true'
        status_filter = request.query_params.get('status')
        year_filter = request.query_params.get('year')

        # Check if this is a pending approvals request for managers
        if status_filter == 'pending' and not my_only:
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
        page_size = int(request.query_params.get('page_size', 20))
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
        from .utils import calculate_leave_hours, check_overlapping_requests, validate_leave_request_dates
        from leaves.models import LeaveBalance
        from decimal import Decimal
        from datetime import datetime

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
            defaults={'allocated_hours': Decimal('96.00')}
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


class LeaveRequestMyView(generics.ListAPIView):
    """List current user's leave requests"""
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


class LeaveRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Leave request detail view"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/requests/{id}/"""
        from .models import LeaveRequest

        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        data = LeaveApprovalService.get_request_detail_with_conflicts(leave_request)
        return Response(data)


class LeaveRequestApproveView(generics.GenericAPIView):
    """Approve a leave request"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/approve/"""
        from .models import LeaveRequest

        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user can approve this request
        if not LeaveApprovalService.can_manager_approve_request(request.user, leave_request):
            return Response(
                {'error': 'You do not have permission to approve this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate request
        serializer = LeaveRequestApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Approve the request
            approved_request = LeaveApprovalService.approve_leave_request(
                leave_request,
                request.user,
                serializer.validated_data.get('comment', '')
            )

            # Create notification
            Notification.objects.create(
                user=leave_request.user,
                type='LEAVE_APPROVED',
                title='Leave Request Approved',
                message=f'Your leave request for {leave_request.start_date} has been approved.',
                link=f'/leaves/{leave_request.id}'
            )

            return Response({
                'id': str(approved_request.id),
                'status': approved_request.status
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LeaveRequestRejectView(generics.GenericAPIView):
    """Reject a leave request"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/reject/"""
        from .models import LeaveRequest

        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user can approve this request
        if not LeaveApprovalService.can_manager_approve_request(request.user, leave_request):
            return Response(
                {'error': 'You do not have permission to reject this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate request
        serializer = LeaveRequestRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Reject the request
            rejected_request = LeaveApprovalService.reject_leave_request(
                leave_request,
                request.user,
                serializer.validated_data['reason']
            )

            # Create notification
            Notification.objects.create(
                user=leave_request.user,
                type='LEAVE_REJECTED',
                title='Leave Request Rejected',
                message=f'Your leave request for {leave_request.start_date} was rejected.',
                link=f'/leaves/{leave_request.id}'
            )

            return Response({
                'id': str(rejected_request.id),
                'status': rejected_request.status
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LeaveRequestCancelView(generics.GenericAPIView):
    """Cancel a leave request"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/cancel/"""
        from .utils import can_modify_request

        request_id = kwargs.get('pk')
        user = request.user

        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': 'Leave request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check ownership
        if leave_request.user_id != user.id:
            return Response(
                {'error': 'You can only cancel your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if can be cancelled
        can_cancel, error = can_modify_request(leave_request)
        if not can_cancel:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Cancel the request
        leave_request.status = 'CANCELLED'
        leave_request.save()

        return Response({
            'id': str(leave_request.id),
            'status': leave_request.status,
            'message': 'Leave request cancelled successfully'
        })


class PublicHolidayListView(generics.ListCreateAPIView):
    """List and create public holidays"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/holidays/?year=2026"""
        from .models import PublicHoliday
        from django.db.models import Q

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
                'name': h.name,
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
        from .models import PublicHoliday
        from datetime import datetime

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
            name=data.get('name'),
            date=date,
            year=data.get('year', date.year),
            is_recurring=data.get('is_recurring', False),
            entity_id=data.get('entity_id'),
            location_id=data.get('location_id'),
            is_active=True
        )

        return Response({
            'id': str(holiday.id),
            'name': holiday.name,
            'date': holiday.date.isoformat(),
            'year': holiday.year,
            'is_recurring': holiday.is_recurring,
        }, status=status.HTTP_201_CREATED)


class PublicHolidayDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Public holiday detail view"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/holidays/{id}/"""
        from .models import PublicHoliday

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
            'name': holiday.name,
            'date': holiday.date.isoformat(),
            'year': holiday.year,
            'is_recurring': holiday.is_recurring,
            'entity_id': str(holiday.entity_id) if holiday.entity_id else None,
            'location_id': str(holiday.location_id) if holiday.location_id else None,
            'is_active': holiday.is_active,
        })

    def put(self, request, *args, **kwargs):
        """PUT /api/v1/leaves/holidays/{id}/ - Update holiday (HR/Admin only)"""
        from .models import PublicHoliday
        from datetime import datetime

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
            holiday.name = data['name']
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
            'name': holiday.name,
            'date': holiday.date.isoformat(),
            'year': holiday.year,
            'is_recurring': holiday.is_recurring,
            'is_active': holiday.is_active,
        })

    def delete(self, request, *args, **kwargs):
        """DELETE /api/v1/leaves/holidays/{id}/ - Delete holiday (HR/Admin only)"""
        from .models import PublicHoliday

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


class LeaveReportsView(generics.GenericAPIView):
    """Leave reports and analytics (HR/Admin only)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/reports/?year=2026&department_id=xxx"""
        from django.db.models import Sum, Count, Avg
        from django.db.models.functions import TruncMonth
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from .models import LeaveBalance

        User = get_user_model()

        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can view reports'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get filters
        year = int(request.query_params.get('year', timezone.now().year))
        department_id = request.query_params.get('department_id')
        entity_id = request.query_params.get('entity_id')

        # Build base queryset
        requests_qs = LeaveRequest.objects.filter(start_date__year=year)
        balances_qs = LeaveBalance.objects.filter(year=year)
        users_qs = User.objects.filter(is_active=True)

        if department_id:
            requests_qs = requests_qs.filter(user__department_id=department_id)
            balances_qs = balances_qs.filter(user__department_id=department_id)
            users_qs = users_qs.filter(department_id=department_id)
        if entity_id:
            requests_qs = requests_qs.filter(user__entity_id=entity_id)
            balances_qs = balances_qs.filter(user__entity_id=entity_id)
            users_qs = users_qs.filter(entity_id=entity_id)

        # Summary stats
        total_requests = requests_qs.count()
        approved_requests = requests_qs.filter(status='APPROVED').count()
        pending_requests = requests_qs.filter(status='PENDING').count()
        rejected_requests = requests_qs.filter(status='REJECTED').count()

        total_hours_approved = requests_qs.filter(status='APPROVED').aggregate(
            total=Sum('total_hours')
        )['total'] or 0

        # Balance utilization
        balance_stats = balances_qs.aggregate(
            total_allocated=Sum('allocated_hours'),
            total_used=Sum('used_hours'),
        )

        # Requests by month
        monthly_data = requests_qs.filter(status='APPROVED').annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            count=Count('id'),
            hours=Sum('total_hours')
        ).order_by('month')

        # Requests by category
        category_data = requests_qs.filter(status='APPROVED').values(
            'leave_category__name', 'leave_category__color'
        ).annotate(
            count=Count('id'),
            hours=Sum('total_hours')
        ).order_by('-hours')

        # Top users by leave taken
        top_users = requests_qs.filter(status='APPROVED').values(
            'user__email', 'user__first_name', 'user__last_name'
        ).annotate(
            total_hours=Sum('total_hours'),
            request_count=Count('id')
        ).order_by('-total_hours')[:10]

        return Response({
            'year': year,
            'summary': {
                'total_requests': total_requests,
                'approved': approved_requests,
                'pending': pending_requests,
                'rejected': rejected_requests,
                'total_hours_approved': float(total_hours_approved),
                'total_employees': users_qs.count(),
            },
            'balance_utilization': {
                'total_allocated': float(balance_stats['total_allocated'] or 0),
                'total_used': float(balance_stats['total_used'] or 0),
            },
            'monthly_breakdown': [
                {
                    'month': item['month'].strftime('%Y-%m') if item['month'] else None,
                    'count': item['count'],
                    'hours': float(item['hours'] or 0)
                }
                for item in monthly_data
            ],
            'by_category': [
                {
                    'category': item['leave_category__name'] or 'Uncategorized',
                    'color': item['leave_category__color'] or '#6B7280',
                    'count': item['count'],
                    'hours': float(item['hours'] or 0)
                }
                for item in category_data
            ],
            'top_users': [
                {
                    'email': item['user__email'],
                    'name': f"{item['user__first_name'] or ''} {item['user__last_name'] or ''}".strip(),
                    'total_hours': float(item['total_hours']),
                    'request_count': item['request_count']
                }
                for item in top_users
            ]
        })
