"""
Leave service layer for business logic
"""
from django.db import transaction
from django.utils import timezone
from .models import LeaveRequest, LeaveBalance


class LeaveApprovalService:
    """Service for handling leave approval logic"""

    @staticmethod
    def get_pending_requests_for_manager(user):
        """
        Get pending leave requests for a manager based on DepartmentManager assignments.

        Args:
            user: Manager user instance

        Returns:
            QuerySet of pending LeaveRequest objects
        """
        from organizations.models import DepartmentManager
        from users.models import User

        if user.role in ['HR', 'ADMIN']:
            # HR and Admin can see all pending requests
            return LeaveRequest.objects.filter(status='PENDING')

        # For managers, filter by their assigned department+location combinations
        managed = DepartmentManager.objects.filter(
            manager=user,
            is_active=True
        ).values('department_id', 'location_id')

        department_ids = [m['department_id'] for m in managed]
        location_ids = [m['location_id'] for m in managed]

        # Get pending requests from users in the same entity
        # and matching department+location combinations
        queryset = LeaveRequest.objects.filter(
            status='PENDING',
            user__entity=user.entity,
        ).filter(
            user__department_id__in=department_ids,
            user__location_id__in=location_ids,
        ).exclude(user=user)

        return queryset.select_related('user', 'leave_category').order_by('created_at')

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

        Args:
            manager: Manager user instance
            leave_request: LeaveRequest instance

        Returns:
            bool: True if manager can approve, False otherwise
        """
        from organizations.models import DepartmentManager

        # HR and Admin can approve any request
        if manager.role in ['HR', 'ADMIN']:
            return True

        # Check if manager is assigned to this department+location
        return DepartmentManager.objects.filter(
            manager=manager,
            department=leave_request.user.department,
            location=leave_request.user.location,
            is_active=True
        ).exists()

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

        # Deduct from balance
        balance = LeaveBalance.objects.select_for_update().get(
            user=leave_request.user,
            year=leave_request.start_date.year
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
    @transaction.atomic
    def reject_leave_request(leave_request, approver, reason):
        """
        Reject a leave request.

        Args:
            leave_request: LeaveRequest instance
            approver: User instance of the approver
            reason: Rejection reason (min 10 characters)

        Returns:
            LeaveRequest: Updated leave request
        """
        from core.models import AuditLog

        if leave_request.status != 'PENDING':
            raise ValueError("Only pending requests can be rejected")

        if len(reason) < 10:
            raise ValueError("Rejection reason must be at least 10 characters")

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
            old_values={'status': 'PENDING'},
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

        # Add employee balance
        balance = LeaveBalance.objects.filter(
            user=leave_request.user,
            year=leave_request.start_date.year
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
