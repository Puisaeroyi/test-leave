#!/usr/bin/env python3
"""Test script to reproduce the leave request creation error."""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, '/home/silver/leave/test-leave')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from leaves.models import LeaveCategory, LeaveBalance, LeaveRequest
from leaves.views.requests.list_create import LeaveRequestListView
from decimal import Decimal
from datetime import datetime, date
import uuid

User = get_user_model()

def test_create_leave_request():
    """Test creating a leave request to reproduce the 500 error."""

    # Get or create a test user
    try:
        user = User.objects.filter(role='EMPLOYEE').first()
        if not user:
            print("No EMPLOYEE user found. Creating one...")
            user = User.objects.create_user(
                email='testemp@example.com',
                password='test123456',
                first_name='Test',
                last_name='Employee',
                role='EMPLOYEE'
            )
            print(f"Created test user: {user.email}")
    except Exception as e:
        print(f"Error getting/creating user: {e}")
        return

    # Get a leave category
    try:
        category = LeaveCategory.objects.first()
        if not category:
            print("No leave categories found. Creating one...")
            category = LeaveCategory.objects.create(
                category_name='Annual Leave',
                code='ANNUAL',
                requires_document=False,
                sort_order=1
            )
            print(f"Created category: {category.category_name}")
    except Exception as e:
        print(f"Error getting/creating category: {e}")
        return

    # Ensure user has a balance
    try:
        year = date.today().year
        balance, created = LeaveBalance.objects.get_or_create(
            user=user,
            year=year,
            defaults={'allocated_hours': Decimal('96.00')}
        )
        if created:
            print(f"Created balance for {year}: 96 hours")
        else:
            print(f"Existing balance: {balance.remaining_hours} hours remaining")
    except Exception as e:
        print(f"Error getting/creating balance: {e}")
        return

    # Prepare test data (similar to frontend payload)
    test_data = {
        'leave_category': str(category.id),
        'start_date': '2026-02-10',
        'end_date': '2026-02-10',
        'shift_type': 'FULL_DAY',
        'start_time': None,
        'end_time': None,
        'reason': 'Test leave request',
        'attachment_url': None
    }

    print(f"\n{'='*60}")
    print("TESTING LEAVE REQUEST CREATION")
    print(f"{'='*60}")
    print(f"User: {user.email} (role: {user.role})")
    print(f"Category: {category.category_name} (id: {category.id})")
    print(f"Balance: {balance.remaining_hours} hours")
    print(f"\nPayload:")
    print(json.dumps(test_data, indent=2))
    print(f"{'='*60}\n")

    # Create a mock request
    factory = RequestFactory()
    request = factory.post('/api/v1/leaves/requests/', test_data, content_type='application/json')
    request.user = user

    # Test the view
    view = LeaveRequestListView.as_view()

    try:
        response = view(request)
        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {response.data}")

        if response.status_code == 500:
            print("\n❌ 500 INTERNAL SERVER ERROR DETECTED")
            print("This is the error we're investigating!")
        elif response.status_code == 201:
            print("\n✅ SUCCESS - Leave request created successfully")
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"\n❌ EXCEPTION RAISED: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

    # Check if any leave requests were created
    requests_count = LeaveRequest.objects.filter(user=user).count()
    print(f"\nTotal leave requests for user: {requests_count}")

if __name__ == '__main__':
    test_create_leave_request()
