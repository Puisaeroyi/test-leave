"""
User signals for auto-creating LeaveBalance on user onboarding

DEPRECATED: DepartmentManager auto-creation signal commented out below.
DepartmentManager is no longer used for approval logic - replaced by User.approver FK.
DepartmentManager table is kept for reporting only.
"""
from datetime import date
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User
from leaves.models import LeaveBalance
from leaves.services import calculate_exempt_vacation_hours

# Fixed defaults for non-dynamic balance types
FIXED_BALANCE_DEFAULTS = {
    'NON_EXEMPT_VACATION': Decimal('40.00'),
    'EXEMPT_SICK': Decimal('40.00'),
    'NON_EXEMPT_SICK': Decimal('40.00'),
}


@receiver(post_save, sender=User)
def create_leave_balance_on_onboarding(sender, instance, created, **kwargs):
    """
    Auto-create LeaveBalance when user completes onboarding.

    EXEMPT_VACATION uses dynamic allocation based on years of service.
    Other balance types use fixed defaults.
    """
    if instance.has_completed_onboarding:
        current_year = timezone.now().year
        reference_date = date(current_year, 1, 1)

        for balance_type in LeaveBalance.BalanceType.values:
            if balance_type == 'EXEMPT_VACATION':
                hours = calculate_exempt_vacation_hours(
                    instance.join_date, reference_date
                )
            else:
                hours = FIXED_BALANCE_DEFAULTS.get(
                    balance_type, Decimal('0.00')
                )

            LeaveBalance.objects.get_or_create(
                user=instance,
                year=current_year,
                balance_type=balance_type,
                defaults={'allocated_hours': hours},
            )


# DEPRECATED: DepartmentManager auto-creation signal
# No longer needed for approval logic - replaced by User.approver FK
# DepartmentManager table kept for reporting only
#
# @receiver(post_save, sender=User)
# def create_department_manager_for_manager_role(sender, instance, **kwargs):
#     """
#     Automatically create DepartmentManager entry when user role is MANAGER or above
#     and user has department and location assigned.
#     """
#     from organizations.models import DepartmentManager
#
#     # Only proceed for MANAGER, HR, or ADMIN roles
#     if instance.role not in [User.Role.MANAGER, User.Role.HR, User.Role.ADMIN]:
#         return
#
#     # Need department and location to create DepartmentManager
#     if not instance.department or not instance.location:
#         return
#
#     # Check if DepartmentManager already exists
#     existing = DepartmentManager.objects.filter(
#         manager=instance,
#         department=instance.department,
#         location=instance.location
#     ).first()
#
#     if not existing:
#         # Create new DepartmentManager entry
#         DepartmentManager.objects.get_or_create(
#             entity=instance.entity,
#             department=instance.department,
#             location=instance.location,
#             manager=instance
#         )
