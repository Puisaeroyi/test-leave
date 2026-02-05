"""
User signals for auto-creating LeaveBalance on user onboarding

DEPRECATED: DepartmentManager auto-creation signal commented out below.
DepartmentManager is no longer used for approval logic - replaced by User.approver FK.
DepartmentManager table is kept for reporting only.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal

from .models import User
from leaves.models import LeaveBalance


@receiver(post_save, sender=User)
def create_leave_balance_on_onboarding(sender, instance, created, **kwargs):
    """
    Auto-create LeaveBalance when user completes onboarding

    Signal triggers when:
    - User is first created (has entity, location, department)
    - User updates their profile to complete onboarding

    Creates a LeaveBalance for the current year with default 96 hours.
    """
    # Check if user has completed onboarding (has entity, location, department)
    if instance.has_completed_onboarding:
        current_year = timezone.now().year

        # Create LeaveBalance if it doesn't exist for current year
        LeaveBalance.objects.get_or_create(
            user=instance,
            year=current_year,
            defaults={'allocated_hours': Decimal('96.00')}
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
