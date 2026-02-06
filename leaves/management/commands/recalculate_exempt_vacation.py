"""
Recalculate EXEMPT_VACATION allocated_hours for all active onboarded employees.

Intended for yearly cron (Jan 1st):
    0 0 1 1 * cd /app && python manage.py recalculate_exempt_vacation
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from leaves.models import LeaveBalance
from leaves.services import calculate_exempt_vacation_hours

User = get_user_model()


class Command(BaseCommand):
    help = 'Recalculate EXEMPT_VACATION allocation based on years of service'

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

    def handle(self, *args, **options):
        year = options['year']
        dry_run = options['dry_run']
        reference_date = date(year, 1, 1)

        self.stdout.write(
            f"Recalculating EXEMPT_VACATION for year {year} "
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
                hours = calculate_exempt_vacation_hours(
                    user.join_date, reference_date
                )

                if dry_run:
                    self.stdout.write(
                        f"  [DRY RUN] {user.email}: {hours}h"
                    )
                    continue

                obj, created = LeaveBalance.objects.update_or_create(
                    user=user,
                    year=year,
                    balance_type=LeaveBalance.BalanceType.EXEMPT_VACATION,
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
