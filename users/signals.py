"""
User signals for auto-creating LeaveBalance on user onboarding.
"""
from datetime import date
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User
from leaves.models import LeaveBalance
from leaves.services import calculate_vacation_hours

# Fixed defaults for non-dynamic balance types
FIXED_BALANCE_DEFAULTS = {
    'SICK': Decimal('40.00'),
}


@receiver(post_save, sender=User)
def create_leave_balance_on_onboarding(sender, instance, created, **kwargs):
    """
    Auto-create LeaveBalance when user completes onboarding.

    Vacation uses dynamic allocation based on years of service.
    Sick uses a fixed default.
    """
    if instance.has_completed_onboarding:
        current_year = timezone.now().year

        # Skip if balances already exist (created by utility in ViewSet)
        if LeaveBalance.objects.filter(user=instance, year=current_year).exists():
            return

        reference_date = date(current_year, 1, 1)

        for balance_type in LeaveBalance.BalanceType.values:
            if balance_type == 'VACATION':
                hours = calculate_vacation_hours(
                    instance.join_date, reference_date
                )
            else:
                hours = FIXED_BALANCE_DEFAULTS.get(
                    balance_type, Decimal('0.00')
                )

            LeaveBalance.objects.update_or_create(
                user=instance,
                year=current_year,
                balance_type=balance_type,
                defaults={'allocated_hours': hours},
            )
