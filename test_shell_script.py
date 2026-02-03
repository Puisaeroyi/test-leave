#!/usr/bin/env python3
"""Django management command to test leave request creation."""

from django.core.management.base import BaseCommand
from datetime import date
from decimal import Decimal

class Command(BaseCommand):
    help = 'Test leave request creation to reproduce 500 error'

    def handle(self, *args, **options):
        from users.models import User
        from leaves.models import LeaveCategory, LeaveBalance, LeaveRequest
        from leaves.utils import calculate_leave_hours

        self.stdout.write("="*60)
        self.stdout.write("TESTING LEAVE REQUEST CREATION")
        self.stdout.write("="*60)

        # Get test data
        user = User.objects.filter(role='EMPLOYEE').first()
        if not user:
            self.stdout.write(self.style.ERROR("No EMPLOYEE user found"))
            return

        category = LeaveCategory.objects.first()
        if not category:
            self.stdout.write(self.style.ERROR("No leave category found"))
            return

        self.stdout.write(f"User: {user.email}")
        self.stdout.write(f"Category: {category.category_name} (ID: {category.id})")

        # Test data
        start_date = date(2026, 2, 10)
        end_date = date(2026, 2, 10)

        # Calculate hours
        try:
            total_hours = calculate_leave_hours(user, start_date, end_date, 'FULL_DAY')
            self.stdout.write(f"Calculated hours: {total_hours}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error calculating hours: {e}"))
            import traceback
            traceback.print_exc()
            return

        # Test creating the request
        try:
            request = LeaveRequest.objects.create(
                user=user,
                leave_category=category,
                start_date=start_date,
                end_date=end_date,
                shift_type='FULL_DAY',
                total_hours=total_hours,
                reason='Test request'
            )
            self.stdout.write(self.style.SUCCESS(f"SUCCESS: Created request {request.id}"))
            self.stdout.write(f"   Status: {request.status}")
            self.stdout.write(f"   Total Hours: {request.total_hours}")

            # Clean up
            request.delete()
            self.stdout.write("Cleaned up test request")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERROR: {e}"))
            import traceback
            traceback.print_exc()
