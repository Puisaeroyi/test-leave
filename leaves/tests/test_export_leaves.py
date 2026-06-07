"""Tests for approved leave export."""
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APIClient

from leaves.models import LeaveCategory, LeaveRequest

User = get_user_model()


class ExportApprovedLeavesTests(TestCase):
    def test_export_shows_both_approvers_and_notes(self):
        employee = User.objects.create_user(
            email='employee-export@example.com',
            password='TestPass123!',
            role=User.Role.EMPLOYEE,
            employee_code='E-100',
            first_name='Export',
            last_name='Employee',
        )
        approver_1 = User.objects.create_user(
            email='approver-1-export@example.com',
            password='TestPass123!',
            role=User.Role.MANAGER,
            first_name='Approver',
            last_name='One',
        )
        approver_2 = User.objects.create_user(
            email='approver-2-export@example.com',
            password='TestPass123!',
            role=User.Role.MANAGER,
            first_name='Approver',
            last_name='Two',
        )
        hr = User.objects.create_user(
            email='hr-export@example.com',
            password='TestPass123!',
            role=User.Role.HR,
        )
        category = LeaveCategory.objects.create(
            category_name='Export Vacation',
            code='EXPORT_VACATION',
            balance_bucket='VACATION',
        )
        LeaveRequest.objects.create(
            user=employee,
            leave_category=category,
            start_date=date(2027, 2, 1),
            end_date=date(2027, 2, 1),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.00'),
            reason='Export check',
            status='APPROVED',
            first_approver=approver_1,
            first_approval_status='APPROVED',
            first_approval_comment='ok-A',
            final_approver=approver_2,
            final_approval_status='APPROVED',
            final_approval_comment='ok-B',
            approved_by=approver_2,
            approved_at=timezone.now(),
            current_approval_step='COMPLETED',
        )

        client = APIClient()
        client.force_authenticate(user=hr)
        response = client.get('/api/v1/leaves/export/approved/?start_date=2027-02-01&end_date=2027-02-28')

        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        self.assertIn('Approver 1', headers)
        self.assertIn('Approver 1 Note', headers)
        self.assertIn('Approver 2', headers)
        self.assertIn('Approver 2 Note', headers)

        row = {headers[index]: sheet[2][index].value for index in range(len(headers))}
        self.assertEqual(row['Approver 1'], 'Approver One')
        self.assertEqual(row['Approver 1 Note'], 'ok-A')
        self.assertEqual(row['Approver 2'], 'Approver Two')
        self.assertEqual(row['Approver 2 Note'], 'ok-B')
