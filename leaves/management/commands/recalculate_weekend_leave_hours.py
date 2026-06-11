"""Recalculate full-day weekend leave after marking 7-day work shifts.

Rollout: flag affected work shifts, run the default dry-run, review output,
then run with --execute. Negative remaining balances are allowed and reported.
"""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from leaves.models import LeaveBalance, LeaveRequest
from leaves.services import BalanceCalculationService
from leaves.utils import calculate_leave_hours


class Command(BaseCommand):
    help = "Recalculate FULL_DAY leave hours for users on weekend-inclusive shifts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=date.today().year,
            help="Leave request start year to recalculate (default: current year)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to database (default behavior)",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Write recalculated request hours and approved balance deltas",
        )

    def handle(self, *args, **options):
        year = options["year"]
        dry_run = options["dry_run"] or not options["execute"]
        changes = self._collect_changes(year)

        self.stdout.write(
            f"Weekend leave recalculation for {year}"
            f"{' [DRY RUN]' if dry_run else ''}. Negative balances may result."
        )

        if dry_run:
            self._write_report(changes)
            return

        with transaction.atomic():
            for change in changes:
                if change["missing_balance"]:
                    continue
                leave = LeaveRequest.objects.select_for_update().get(id=change["request_id"])
                leave.total_hours = change["new_hours"]
                leave.save(update_fields=["total_hours", "updated_at"])

                balance = change["balance"]
                if balance:
                    locked_balance = LeaveBalance.objects.select_for_update().get(id=balance.id)
                    locked_balance.used_hours += change["delta"]
                    locked_balance.save(update_fields=["used_hours", "updated_at"])
                    change["balance_after_remaining"] = locked_balance.remaining_hours

        self._write_report(changes)

    def _collect_changes(self, year):
        requests = LeaveRequest.objects.filter(
            shift_type=LeaveRequest.ShiftType.FULL_DAY,
            status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
            user__work_shift__includes_weekends=True,
            start_date__year=year,
        ).select_related(
            "user",
            "user__work_shift",
            "user__department",
            "user__entity",
            "user__location",
            "leave_category",
        )

        changes = []
        for leave in requests:
            new_hours = calculate_leave_hours(
                leave.user,
                leave.start_date,
                leave.end_date,
                leave.shift_type,
            )
            if new_hours == leave.total_hours:
                continue

            delta = new_hours - leave.total_hours
            change = {
                "request_id": leave.id,
                "user_email": leave.user.email,
                "dates": f"{leave.start_date} to {leave.end_date}",
                "status": leave.status,
                "old_hours": leave.total_hours,
                "new_hours": new_hours,
                "delta": delta,
                "balance": None,
                "balance_before_remaining": None,
                "balance_after_remaining": None,
                "missing_balance": False,
            }

            if leave.status == LeaveRequest.Status.APPROVED:
                balance_type = BalanceCalculationService.calculate_balance_type(leave.leave_category)
                if balance_type != "NONE":
                    balance = LeaveBalance.objects.filter(
                        user=leave.user,
                        year=leave.start_date.year,
                        balance_type=balance_type,
                    ).first()
                    if balance:
                        change["balance"] = balance
                        change["balance_before_remaining"] = balance.remaining_hours
                        change["balance_after_remaining"] = balance.remaining_hours - delta
                    else:
                        change["missing_balance"] = True

            changes.append(change)
        return changes

    def _write_report(self, changes):
        applied = 0
        skipped = 0
        negative = 0

        for change in changes:
            missing_balance = change["missing_balance"]
            if missing_balance:
                skipped += 1
                marker = "MISSING BALANCE - REQUEST NOT SAFE TO EXECUTE"
            elif (
                change["balance_after_remaining"] is not None
                and change["balance_after_remaining"] < Decimal("0.00")
            ):
                applied += 1
                negative += 1
                marker = "WENT NEGATIVE"
            else:
                applied += 1
                marker = ""

            self.stdout.write(
                f"{change['user_email']} request={change['request_id']} "
                f"{change['dates']} {change['status']} "
                f"{change['old_hours']}h -> {change['new_hours']}h "
                f"delta={change['delta']}h {marker}".rstrip()
            )
            if change["balance_before_remaining"] is not None:
                self.stdout.write(
                    f"  remaining: {change['balance_before_remaining']}h "
                    f"-> {change['balance_after_remaining']}h"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Summary: {applied} request(s) recalculated, "
                f"{skipped} skipped, {negative} went negative"
            )
        )
