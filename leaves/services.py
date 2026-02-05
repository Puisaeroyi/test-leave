"""
Leave service layer for business logic
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import LeaveRequest, LeaveBalance


class LeaveApprovalService:
    """Service for handling leave approval logic"""

    @staticmethod
    def get_pending_requests_for_manager(user):
        """
        Get pending leave requests for a manager based on approver relationship.

        Returns only requests where the current user is the assigned approver.
        Supports cross-entity approval (no entity/department/location filtering).

        Args:
            user: Manager user instance

        Returns:
            QuerySet of pending LeaveRequest objects
        """
        from users.models import User

        # Show requests where current user is the assigned approver
        # No role check - the approver relationship IS the permission
        # Include both PENDING and APPROVED (for 24h denial window)
        return LeaveRequest.objects.filter(
            status__in=['PENDING', 'APPROVED'],
            user__approver=user
        ).exclude(user=user).select_related('user', 'leave_category').order_by('created_at')

    @staticmethod
    def get_approval_history_for_manager(user):
        """
        Get approval history (approved/rejected requests) for a manager.

        Args:
            user: Manager user instance

        Returns:
            QuerySet of approved/rejected LeaveRequest objects
        """
        # Get all requests that this user has approved or rejected
        queryset = LeaveRequest.objects.filter(
            approved_by=user,
            status__in=['APPROVED', 'REJECTED']
        )

        return queryset.select_related('user', 'leave_category').order_by('-approved_at')

    @staticmethod
    def can_manager_approve_request(manager, leave_request):
        """
        Check if a manager can approve a specific leave request.

        Permission based solely on approver relationship (request.user.approver == manager).
        No role-based bypass - HR/ADMIN must be assigned as approver to approve.

        Args:
            manager: Manager user instance
            leave_request: LeaveRequest instance

        Returns:
            bool: True if manager can approve, False otherwise
        """
        # User can approve if they are the assigned approver
        # No role-based bypass - approver relationship IS the permission
        return leave_request.user.approver == manager

    @staticmethod
    @transaction.atomic
    def approve_leave_request(leave_request, approver, comment=''):
        """
        Approve a leave request and update balance.

        Args:
            leave_request: LeaveRequest instance
            approver: User instance of the approver
            comment: Optional comment from approver

        Returns:
            LeaveRequest: Updated leave request
        """
        from core.models import AuditLog

        if leave_request.status != 'PENDING':
            raise ValueError("Only pending requests can be approved")

        # Update leave request
        leave_request.status = 'APPROVED'
        leave_request.approved_by = approver
        leave_request.approved_at = timezone.now()
        leave_request.approver_comment = comment
        leave_request.save()

        # Deduct from balance (find by balance_type)
        balance_type = LeaveApprovalService._get_balance_type(leave_request)
        balance = LeaveBalance.objects.select_for_update().get(
            user=leave_request.user,
            year=leave_request.start_date.year,
            balance_type=balance_type
        )
        balance.used_hours += leave_request.total_hours
        balance.save()

        # Create audit log
        AuditLog.objects.create(
            user=approver,
            action='APPROVE',
            entity_type='LeaveRequest',
            entity_id=leave_request.id,
            old_values={'status': 'PENDING'},
            new_values={
                'status': 'APPROVED',
                'approved_by': str(approver.id),
                'approved_at': leave_request.approved_at.isoformat(),
                'comment': comment
            }
        )

        return leave_request

    @staticmethod
    def _get_balance_type(leave_request):
        """
        Determine balance type based on leave category and exempt type.

        Args:
            leave_request: LeaveRequest instance

        Returns:
            str: BalanceType key (e.g., 'EXEMPT_VACATION')
        """
        is_vacation = leave_request.leave_category and leave_request.leave_category.code.lower() == 'vacation'
        is_exempt = leave_request.exempt_type == 'EXEMPT'

        if is_vacation:
            return 'EXEMPT_VACATION' if is_exempt else 'NON_EXEMPT_VACATION'
        else:
            return 'EXEMPT_SICK' if is_exempt else 'NON_EXEMPT_SICK'

    @staticmethod
    @transaction.atomic
    def reject_leave_request(leave_request, approver, reason):
        """
        Reject a leave request (supports both PENDING and APPROVED status).

        For APPROVED requests:
        - Validates 24-hour time constraint (must be >24h before leave starts)
        - Restores the deducted balance

        Args:
            leave_request: LeaveRequest instance
            approver: User instance of the approver
            reason: Rejection reason (min 10 characters)

        Returns:
            LeaveRequest: Updated leave request
        """
        from core.models import AuditLog

        if leave_request.status not in ['PENDING', 'APPROVED']:
            raise ValueError("Only pending or approved requests can be rejected")

        if len(reason) < 10:
            raise ValueError("Rejection reason must be at least 10 characters")

        # For approved requests, validate 24-hour time constraint
        if leave_request.status == 'APPROVED':
            # Create aware datetime for start_date (midnight of leave start day)
            leave_start = timezone.make_aware(
                timezone.datetime.combine(leave_request.start_date, timezone.datetime.min.time())
            )
            cutoff_time = leave_start - timedelta(hours=24)
            now = timezone.now()

            if now >= cutoff_time:
                raise ValidationError(
                    "Cannot reject approved requests within 24 hours of leave start date. "
                    f"Leave starts on {leave_request.start_date}, cutoff was {cutoff_time.strftime('%Y-%m-%d %H:%M')}"
                )

            # Restore balance (find by balance_type)
            balance_type = LeaveApprovalService._get_balance_type(leave_request)
            balance = LeaveBalance.objects.select_for_update().get(
                user=leave_request.user,
                year=leave_request.start_date.year,
                balance_type=balance_type
            )
            balance.used_hours -= leave_request.total_hours
            balance.save()

        # Store old status for audit
        old_status = leave_request.status

        # Update leave request
        leave_request.status = 'REJECTED'
        leave_request.approved_by = approver
        leave_request.approved_at = timezone.now()
        leave_request.rejection_reason = reason
        leave_request.save()

        # Create audit log
        AuditLog.objects.create(
            user=approver,
            action='REJECT',
            entity_type='LeaveRequest',
            entity_id=leave_request.id,
            old_values={'status': old_status},
            new_values={
                'status': 'REJECTED',
                'approved_by': str(approver.id),
                'approved_at': leave_request.approved_at.isoformat(),
                'rejection_reason': reason
            }
        )

        return leave_request

    @staticmethod
    def get_request_detail_with_conflicts(leave_request):
        """
        Get leave request detail with employee balance and team conflicts.

        Args:
            leave_request: LeaveRequest instance

        Returns:
            dict: Request data with balance and conflicts
        """
        from .serializers import LeaveRequestSerializer

        # Get serialized data
        serializer = LeaveRequestSerializer(leave_request)
        data = serializer.data

        # Add employee balance for the relevant balance type
        balance_type = LeaveApprovalService._get_balance_type(leave_request)
        balance = LeaveBalance.objects.filter(
            user=leave_request.user,
            year=leave_request.start_date.year,
            balance_type=balance_type
        ).first()

        if balance:
            data['employee_balance'] = {
                'remaining_hours': float(balance.remaining_hours),
                'remaining_days': float(balance.remaining_hours) / 8,
            }

        # Find team conflicts (approved overlapping leaves)
        conflicts = LeaveRequest.objects.filter(
            user__entity=leave_request.user.entity,
            user__location=leave_request.user.location,
            user__department=leave_request.user.department,
            status='APPROVED',
            start_date__lte=leave_request.end_date,
            end_date__gte=leave_request.start_date,
        ).exclude(user=leave_request.user)

        data['team_conflicts'] = [
            {
                'id': str(c.id),
                'name': f"{c.user.first_name} {c.user.last_name}".strip() or c.user.email,
                'dates': f"{c.start_date} - {c.end_date}",
                'start_date': str(c.start_date),
                'end_date': str(c.end_date)
            }
            for c in conflicts
        ]

        return data
