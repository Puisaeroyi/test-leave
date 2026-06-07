import math
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import migrations
from django.db.models import Sum


VACATION_TYPES = ['EXEMPT_VACATION', 'NON_EXEMPT_VACATION']
SICK_TYPES = ['EXEMPT_SICK', 'NON_EXEMPT_SICK']
OLD_TYPES = VACATION_TYPES + SICK_TYPES

VACATION_TIERS = {
    (2, 5): Decimal('80.00'),
    (6, 10): Decimal('120.00'),
    (11, 15): Decimal('160.00'),
    (16, None): Decimal('200.00'),
}

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


def calculate_vacation_hours(join_date, reference_date):
    if join_date is None:
        return Decimal('80.00')
    if join_date.year > reference_date.year:
        return Decimal('0.00')
    if join_date.year == reference_date.year:
        return FIRST_YEAR_PRORATE[join_date.month]

    completed_years = math.floor((reference_date - join_date).days / 365.25)
    yos = max(completed_years + 1, 2)

    for (low, high), hours in VACATION_TIERS.items():
        if high is None and yos >= low:
            return hours
        if high is not None and low <= yos <= high:
            return hours
    return Decimal('200.00')


def sum_old_balances(LeaveBalance, user_id, year, balance_types):
    sums = LeaveBalance.objects.filter(
        user_id=user_id,
        year=year,
        balance_type__in=balance_types,
    ).aggregate(
        used=Sum('used_hours'),
        adjusted=Sum('adjusted_hours'),
    )
    return {
        'used_hours': sums['used'] or Decimal('0.00'),
        'adjusted_hours': sums['adjusted'] or Decimal('0.00'),
    }


def merge_leave_balances(apps, schema_editor):
    LeaveBalance = apps.get_model('leaves', 'LeaveBalance')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    groups = (
        LeaveBalance.objects.filter(balance_type__in=OLD_TYPES)
        .values('user_id', 'year')
        .distinct()
    )

    for group in groups:
        user_id = group['user_id']
        year = group['year']
        user = User.objects.filter(id=user_id).first()
        reference_date = date(year, 1, 1)
        vacation_values = sum_old_balances(LeaveBalance, user_id, year, VACATION_TYPES)
        sick_values = sum_old_balances(LeaveBalance, user_id, year, SICK_TYPES)

        LeaveBalance.objects.update_or_create(
            user_id=user_id,
            year=year,
            balance_type='VACATION',
            defaults={
                'allocated_hours': calculate_vacation_hours(
                    getattr(user, 'join_date', None),
                    reference_date,
                ),
                **vacation_values,
            },
        )
        LeaveBalance.objects.update_or_create(
            user_id=user_id,
            year=year,
            balance_type='SICK',
            defaults={
                'allocated_hours': Decimal('40.00'),
                **sick_values,
            },
        )

    LeaveBalance.objects.filter(balance_type__in=OLD_TYPES).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('leaves', '0013_seed_leave_categories'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(merge_leave_balances, noop_reverse),
    ]
