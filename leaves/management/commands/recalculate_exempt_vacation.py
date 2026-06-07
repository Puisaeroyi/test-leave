"""
Recalculate leave balance allocations for all active onboarded employees.

Handles the two balance types:
- VACATION: dynamic by years of service
- SICK: fixed 40h

Intended for yearly cron (Jan 1st):
    0 0 1 1 * cd /app && python manage.py recalculate_exempt_vacation
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from leaves.models import LeaveBalance
from leaves.services import calculate_vacation_hours

User = get_user_model()

# Command filename is historical because production cron calls it directly.
FIXED_BALANCE_DEFAULTS = {
    'SICK': Decimal('40.00'),
}


class Command(BaseCommand):
    help = 'Recalculate leave balance allocations for all active onboarded employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=date.today().year,
            help='Balance year to recalculate (default: current year)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to database',
        )
        parser.add_argument(
            '--all-types',
            action='store_true',
            help='Accepted for backwards compatibility; recalculates VACATION and SICK.',
        )

    def handle(self, *args, **options):
        year = options['year']
        dry_run = options['dry_run']
        reference_date = date(year, 1, 1)

        self.stdout.write(
            f"Recalculating VACATION and SICK for year {year} "
            f"(ref: {reference_date}){' [DRY RUN]' if dry_run else ''}"
        )

        users = User.objects.filter(
            is_active=True,
            entity__isnull=False,
            location__isnull=False,
            department__isnull=False,
        )

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for user in users:
                vacation_hours = calculate_vacation_hours(
                    user.join_date, reference_date
                )

                if dry_run:
                    self.stdout.write(
                        f"  [DRY RUN] {user.email}: VACATION={vacation_hours}h, SICK=40.00h"
                    )
                    continue

                obj, created = LeaveBalance.objects.update_or_create(
                    user=user,
                    year=year,
                    balance_type=LeaveBalance.BalanceType.VACATION,
                    defaults={'allocated_hours': vacation_hours},
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                for balance_type, hours in FIXED_BALANCE_DEFAULTS.items():
                    obj, created = LeaveBalance.objects.update_or_create(
                        user=user,
                        year=year,
                        balance_type=balance_type,
                        defaults={'allocated_hours': hours},
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

        total = users.count()
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"[DRY RUN] {total} users would be processed"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Done: {total} users processed — "
                f"{created_count} created, {updated_count} updated"
            ))
