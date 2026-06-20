"""
Leave service layer for business logic
"""
import math
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import LeaveBalance, LeaveRequest


# --- VACATION dynamic allocation constants ---

# Tier table: (min_year_of_service, max_year_of_service) -> hours
# Year 1 handled separately via FIRST_YEAR_PRORATE
VACATION_TIERS = {
    (2, 5): Decimal('80.00'),     # 10 days
    (6, 10): Decimal('120.00'),   # 15 days
    (11, 15): Decimal('160.00'),  # 20 days
    (16, None): Decimal('200.00'),  # 25 days (cap)
}

# 1st-year prorate by join month
FIRST_YEAR_PRORATE = {
    1: Decimal('72.00'),
    2: Decimal('64.00'),
    3: Decimal('56.00'),
    4: Decimal('48.00'),
    5: Decimal('40.00'),
    6: Decimal('32.00'),
    7: Decimal('24.00'),
    8: Decimal('16.00'),
    9: Decimal('8.00'),
    10: Decimal('0.00'),
    11: Decimal('0.00'),
    12: Decimal('0.00'),
}

# Default fallback when join_date is None
DEFAULT_VACATION_HOURS = Decimal('80.00')

DEFAULT_SICK_HOURS = Decimal('40.00')


class BalanceCalculationService:
    """Service for calculating leave balance types and allocations"""

    @staticmethod
    def calculate_balance_type(leave_category) -> str:
        """
        Determine balance type from the category balance bucket.

        Args:
            leave_category: LeaveCategory instance or None

        Returns:
            str: Balance type key: VACATION, SICK, or NONE
        """
        return getattr(leave_category, 'balance_bucket', 'NONE') or 'NONE'

    @staticmethod
    def calculate_default_allocation(balance_type: str, user, year: int) -> Decimal:
        """
        Calculate default allocation including YoS-based vacation.

        Args:
            balance_type: Balance type key
            user: User instance
            year: Balance year

        Returns:
            Decimal: Default allocated hours
        """
        if balance_type == 'VACATION':
            reference_date = date(year, 1, 1)
            return calculate_vacation_hours(user.join_date, reference_date)

        if balance_type == 'SICK':
            return DEFAULT_SICK_HOURS
        return Decimal('0.00')


def get_year_of_service(join_date: date, reference_date: date) -> int:
    """
    Calculate year of service (1-based).

    Uses YEARFRAC-equivalent: floor((reference_date - join_date).days / 365.25) + 1
    """
    delta_days = (reference_date - join_date).days
    completed_years = math.floor(delta_days / 365.25)
    return completed_years + 1


def calculate_vacation_hours(join_date, reference_date: date) -> Decimal:
    """
    Calculate vacation allocated hours based on years of service.

    Args:
        join_date: Employee join date (date or None)
        reference_date: Jan 1st of the balance year

    Returns:
        Decimal hours allocation
    """
    if join_date is None:
        return DEFAULT_VACATION_HOURS

    # Future year: employee hasn't started yet
    if join_date.year > reference_date.year:
        return Decimal('0.00')

    # Same year as balance year: first-year prorate by join month
    if join_date.year == reference_date.year:
        return FIRST_YEAR_PRORATE[join_date.month]

    yos = get_year_of_service(join_date, reference_date)

    # Prior-year joiners with <365 days get yos=1; treat as tier 2 (they
    # already received prorated allocation in their join year)
    if yos < 2:
        yos = 2

    # Tier lookup
    for (low, high), hours in VACATION_TIERS.items():
        if high is None:
            if yos >= low:
                return hours
        elif low <= yos <= high:
            return hours

    # Fallback (shouldn't happen): return cap
    return Decimal('200.00')


class LeaveApprovalService:
    """Service for handling leave approval logic"""

    @staticmethod
    def _peer_approvers(leave_request):
        """Return the request's assigned peer approvers from snapshots or user defaults."""
        return (
            leave_request.first_approver or leave_request.user.approver_1,
            leave_request.final_approver or leave_request.user.approver_2,
        )

    @staticmethod
    def _assigned_peers(leave_request):
        peers = []
        for peer in LeaveApprovalService._peer_approvers(leave_request):
            if peer and peer not in peers:
                peers.append(peer)
        return peers

    @staticmethod
    def _decision_for_peer(leave_request, peer):
        peer_1, peer_2 = LeaveApprovalService._peer_approvers(leave_request)
        if peer_1 == peer:
            return leave_request.first_approval_status
        if peer_2 == peer:
            return leave_request.final_approval_status
        return None

    @staticmethod
    def get_action_required_user_ids(leave_request):
        if leave_request.status != LeaveRequest.Status.PENDING:
            return []

        pending_ids = []
        peer_1, peer_2 = LeaveApprovalService._peer_approvers(leave_request)
        if peer_1 and leave_request.first_approval_status == LeaveRequest.ApprovalDecision.PENDING:
            pending_ids.append(str(peer_1.id))
        if (
            peer_2
            and peer_2 != peer_1
            and leave_request.final_approval_status == LeaveRequest.ApprovalDecision.PENDING
        ):
            pending_ids.append(str(peer_2.id))
        return pending_ids

    @staticmethod
    def _pending_action_query(user):
        return Q(
            status=LeaveRequest.Status.PENDING,
            first_approval_status=LeaveRequest.ApprovalDecision.PENDING,
            first_approver=user,
        ) | Q(
            status=LeaveRequest.Status.PENDING,
            first_approval_status=LeaveRequest.ApprovalDecision.PENDING,
            first_approver__isnull=True,
            user__approver_1=user,
        ) | Q(
            status=LeaveRequest.Status.PENDING,
            final_approval_status=LeaveRequest.ApprovalDecision.PENDING,
            final_approver=user,
        ) | Q(
            status=LeaveRequest.Status.PENDING,
            final_approval_status=LeaveRequest.ApprovalDecision.PENDING,
            final_approver__isnull=True,
            user__approver_2=user,
        )

    @staticmethod
    def get_pending_review_count(user):
        return LeaveRequest.objects.filter(
            LeaveApprovalService._pending_action_query(user)
        ).exclude(user=user).distinct().count()

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
        pending_for_user = LeaveApprovalService._pending_action_query(user)
        acted_pending = Q(status='PENDING') & (
            Q(first_approver=user, first_approval_status__in=['APPROVED', 'REJECTED'])
            | Q(
                first_approver__isnull=True,
                user__approver_1=user,
                first_approval_status__in=['APPROVED', 'REJECTED'],
            )
            | Q(final_approver=user, final_approval_status__in=['APPROVED', 'REJECTED'])
            | Q(
                final_approver__isnull=True,
                user__approver_2=user,
                final_approval_status__in=['APPROVED', 'REJECTED'],
            )
        )
        acted_history = Q(
            status__in=['APPROVED', 'REJECTED'],
        ) & (
            Q(first_approver=user)
            | Q(final_approver=user)
            | Q(approved_by=user)
            | Q(first_approver__isnull=True, user__approver_1=user)
            | Q(final_approver__isnull=True, user__approver_2=user)
        )

        return LeaveRequest.objects.filter(
            pending_for_user | acted_pending | acted_history
        ).exclude(user=user).select_related(
            'user', 'leave_category', 'first_approver', 'final_approver',
            'user__approver_1', 'user__approver_2'
        ).distinct().order_by('created_at')

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
            Q(first_approver=user)
            | Q(final_approver=user)
            | Q(approved_by=user)
            | Q(first_approver__isnull=True, user__approver_1=user)
            | Q(final_approver__isnull=True, user__approver_2=user),
            status__in=['APPROVED', 'REJECTED'],
        ).distinct()

        return queryset.select_related(
            'user', 'leave_category', 'first_approver', 'final_approver',
            'user__approver_1', 'user__approver_2'
        ).order_by('-approved_at')

    @staticmethod
    def can_manager_approve_request(manager, leave_request):
        """
        Check if a manager can approve a specific leave request.

        Permission based solely on approver relationship.
        No role-based bypass - HR/ADMIN must be assigned as approver to approve.

        Args:
            manager: Manager user instance
            leave_request: LeaveRequest instance

        Returns:
            bool: True if manager can approve, False otherwise
        """
        first_approver, final_approver = LeaveApprovalService._peer_approvers(leave_request)

        if leave_request.status == 'PENDING':
            return (
                first_approver == manager
                and leave_request.first_approval_status == LeaveRequest.ApprovalDecision.PENDING
            ) or (
                final_approver == manager
                and leave_request.final_approval_status == LeaveRequest.ApprovalDecision.PENDING
            )

        if leave_request.status == 'APPROVED':
            return (
                leave_request.approved_by == manager
                or first_approver == manager
                or final_approver == manager
            )

        return False

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
        if leave_request.status != 'PENDING':
            raise ValueError("Only pending requests can be approved")

        now = timezone.now()
        first_approver, final_approver = LeaveApprovalService._peer_approvers(leave_request)
        leave_request.first_approver = first_approver
        leave_request.final_approver = final_approver

        if first_approver == approver:
            if leave_request.first_approval_status != LeaveRequest.ApprovalDecision.PENDING:
                raise ValueError("This approver has already acted on this request")
            leave_request.first_approval_status = 'APPROVED'
            leave_request.first_approval_comment = comment
            leave_request.first_approval_at = now
            decision_step = 'FIRST'
        elif final_approver == approver:
            if leave_request.final_approval_status != LeaveRequest.ApprovalDecision.PENDING:
                raise ValueError("This approver has already acted on this request")
            leave_request.final_approval_status = 'APPROVED'
            leave_request.final_approval_comment = comment
            leave_request.final_approval_at = now
            decision_step = 'FINAL'
        else:
            raise ValueError("Only an assigned approver can approve this request")

        assigned_peers = LeaveApprovalService._assigned_peers(leave_request)
        all_approved = assigned_peers and all(
            LeaveApprovalService._decision_for_peer(leave_request, peer) == LeaveRequest.ApprovalDecision.APPROVED
            for peer in assigned_peers
        )

        if not all_approved:
            leave_request.save()
            LeaveApprovalService._create_approval_audit(
                leave_request, approver, decision_step, 'PENDING', comment, now
            )
            return leave_request

        # Final approval completes the request and deducts balance when applicable.
        leave_request.status = 'APPROVED'
        leave_request.current_approval_step = 'COMPLETED'
        leave_request.approved_by = approver
        leave_request.approved_at = now
        leave_request.approver_comment = comment
        leave_request.save()

        balance_type = LeaveApprovalService._get_balance_type(leave_request)
        if balance_type != 'NONE':
            try:
                balance = LeaveBalance.objects.select_for_update().get(
                    user=leave_request.user,
                    year=leave_request.start_date.year,
                    balance_type=balance_type
                )
            except LeaveBalance.DoesNotExist:
                raise ValueError(
                    f"No {balance_type} balance found for year {leave_request.start_date.year}. "
                    "Cannot approve without an existing balance record."
                )
            if leave_request.total_hours > balance.remaining_hours:
                raise ValueError(
                    f"Insufficient balance. Requested: {leave_request.total_hours}h, "
                    f"Available: {balance.remaining_hours}h"
                )
            balance.used_hours += leave_request.total_hours
            balance.save()

        LeaveApprovalService._create_approval_audit(
            leave_request, approver, decision_step, 'APPROVED', comment, now
        )

        return leave_request

    @staticmethod
    def _create_approval_audit(leave_request, approver, step, resulting_status, comment, acted_at):
        from core.models import AuditLog

        AuditLog.objects.create(
            user=approver,
            action='APPROVE',
            entity_type='LeaveRequest',
            entity_id=leave_request.id,
            old_values={'status': 'PENDING', 'step': step},
            new_values={
                'status': resulting_status,
                'step': step,
                'approved_by': str(approver.id),
                'approved_at': acted_at.isoformat(),
                'comment': comment,
            },
        )

    @staticmethod
    def _get_balance_type(leave_request):
        """
        Determine balance type based on leave category.

        Args:
            leave_request: LeaveRequest instance

        Returns:
            str: BalanceType key, or NONE for non-deducting categories.
        """
        return (
            leave_request.balance_type_snapshot
            or BalanceCalculationService.calculate_balance_type(leave_request.leave_category)
        )

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

            balance_type = LeaveApprovalService._get_balance_type(leave_request)
            if balance_type != 'NONE':
                balance = LeaveBalance.objects.select_for_update().get(
                    user=leave_request.user,
                    year=leave_request.start_date.year,
                    balance_type=balance_type
                )
                balance.used_hours = max(Decimal('0.00'), balance.used_hours - leave_request.total_hours)
                balance.save()

        # Store old status for audit
        old_status = leave_request.status

        now = timezone.now()
        first_approver, final_approver = LeaveApprovalService._peer_approvers(leave_request)
        leave_request.first_approver = first_approver
        leave_request.final_approver = final_approver
        if first_approver == approver:
            leave_request.first_approval_status = 'REJECTED'
            leave_request.first_approval_comment = reason
            leave_request.first_approval_at = now
        elif final_approver == approver:
            leave_request.final_approval_status = 'REJECTED'
            leave_request.final_approval_comment = reason
            leave_request.final_approval_at = now
        elif leave_request.status == 'PENDING':
            raise ValueError("Only an assigned approver can reject this request")

        # Update leave request
        leave_request.status = 'REJECTED'
        leave_request.current_approval_step = 'COMPLETED'
        leave_request.approved_by = approver
        leave_request.approved_at = now
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
        if balance_type != 'NONE':
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
