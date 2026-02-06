"""
Recalculate leave balance allocations for all active onboarded employees.

Handles all 4 balance types:
- EXEMPT_VACATION: dynamic by years of service
- NON_EXEMPT_VACATION: fixed 40h
- EXEMPT_SICK: fixed 40h
- NON_EXEMPT_SICK: fixed 40h

Intended for yearly cron (Jan 1st):
    0 0 1 1 * cd /app && python manage.py recalculate_exempt_vacation
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from leaves.models import LeaveBalance
from leaves.services import calculate_exempt_vacation_hours

User = get_user_model()

# Fixed defaults for non-dynamic balance types
FIXED_BALANCE_DEFAULTS = {
    'NON_EXEMPT_VACATION': Decimal('40.00'),
    'EXEMPT_SICK': Decimal('40.00'),
    'NON_EXEMPT_SICK': Decimal('40.00'),
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
            help='Recalculate all 4 balance types (default: EXEMPT_VACATION only)',
        )

    def handle(self, *args, **options):
        year = options['year']
        dry_run = options['dry_run']
        all_types = options['all_types']
        reference_date = date(year, 1, 1)

        mode = "all balance types" if all_types else "EXEMPT_VACATION only"
        self.stdout.write(
            f"Recalculating {mode} for year {year} "
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
                # Always recalculate EXEMPT_VACATION (dynamic)
                ev_hours = calculate_exempt_vacation_hours(
                    user.join_date, reference_date
                )

                if dry_run:
                    self.stdout.write(
                        f"  [DRY RUN] {user.email}: EXEMPT_VACATION={ev_hours}h"
                    )
                    continue

                obj, created = LeaveBalance.objects.update_or_create(
                    user=user,
                    year=year,
                    balance_type=LeaveBalance.BalanceType.EXEMPT_VACATION,
                    defaults={'allocated_hours': ev_hours},
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # Recalculate fixed balance types if --all-types
                if all_types:
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
