#!/usr/bin/env python3
"""Test script using Django shell to reproduce the error."""

import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Setup minimal Django without full settings
os.environ['DJANGO_SECRET_KEY'] = 'test-secret-key'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1'
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/leave_management'

import django
from django.conf import settings

# Configure minimal settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        ALLOWED_HOSTS=['*'],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'leave_management',
                'USER': 'postgres',
                'PASSWORD': 'postgres',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'users',
            'organizations',
            'leaves',
            'core',
        ],
        USE_TZ=True,
    )

django.setup()

# Now import models
from users.models import User
from leaves.models import LeaveCategory, LeaveBalance, LeaveRequest
from leaves.utils import calculate_leave_hours

def test_direct_creation():
    """Test direct model creation to isolate the issue."""

    print("="*60)
    print("TESTING DIRECT LEAVE REQUEST CREATION")
    print("="*60)

    # Get test data
    user = User.objects.filter(role='EMPLOYEE').first()
    if not user:
        print("❌ No EMPLOYEE user found in database")
        return

    category = LeaveCategory.objects.first()
    if not category:
        print("❌ No leave category found")
        return

    print(f"User: {user.email}")
    print(f"Category: {category.category_name} (ID: {category.id})")

    # Test data
    start_date = date(2026, 2, 10)
    end_date = date(2026, 2, 10)

    # Calculate hours
    try:
        total_hours = calculate_leave_hours(user, start_date, end_date, 'FULL_DAY')
        print(f"Calculated hours: {total_hours}")
    except Exception as e:
        print(f"❌ Error calculating hours: {e}")
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
        print(f"✅ SUCCESS: Created request {request.id}")
        print(f"   Status: {request.status}")
        print(f"   Total Hours: {request.total_hours}")

        # Clean up
        request.delete()
        print("🧹 Cleaned up test request")

    except Exception as e:
        print(f"❌ ERROR creating request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_direct_creation()
