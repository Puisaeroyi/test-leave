"""Tests for sequential first/final leave approval."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from leaves.models import LeaveBalance, LeaveCategory, LeaveRequest

User = get_user_model()


class TwoStepApprovalTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='TestPass123!',
            role=User.Role.EMPLOYEE,
        )
        self.first_approver = User.objects.create_user(
            email='first@example.com',
            password='TestPass123!',
            role=User.Role.MANAGER,
        )
        self.final_approver = User.objects.create_user(
            email='final@example.com',
            password='TestPass123!',
            role=User.Role.MANAGER,
        )
        self.employee.approver = self.first_approver
        self.employee.final_approver = self.final_approver
        self.employee.save()
        self.category = LeaveCategory.objects.create(
            category_name='Vacation',
            code='VACATION',
        )
        self.balance = LeaveBalance.objects.create(
            user=self.employee,
            year=2027,
            balance_type='EXEMPT_VACATION',
            allocated_hours=Decimal('80.00'),
        )
        self.leave_request = LeaveRequest.objects.create(
            user=self.employee,
            leave_category=self.category,
            start_date=date(2027, 1, 20),
            end_date=date(2027, 1, 20),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.00'),
            status='PENDING',
            first_approver=self.first_approver,
            final_approver=self.final_approver,
            current_approval_step='FIRST',
        )

    def test_first_approval_moves_to_final_without_deducting_balance(self):
        client = APIClient()
        client.force_authenticate(user=self.first_approver)

        response = client.post(
            f'/api/v1/leaves/requests/{self.leave_request.id}/approve/',
            {'comment': 'First review complete'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(self.leave_request.status, 'PENDING')
        self.assertEqual(self.leave_request.current_approval_step, 'FINAL')
        self.assertEqual(self.leave_request.first_approval_status, 'APPROVED')
        self.assertEqual(self.leave_request.first_approval_comment, 'First review complete')
        self.assertEqual(self.balance.used_hours, Decimal('0.00'))

    def test_first_approver_still_sees_request_while_final_approval_is_pending(self):
        self.leave_request.first_approval_status = 'APPROVED'
        self.leave_request.first_approval_comment = 'Reviewed by first approver'
        self.leave_request.current_approval_step = 'FINAL'
        self.leave_request.save()
        client = APIClient()
        client.force_authenticate(user=self.first_approver)

        response = client.get('/api/v1/leaves/requests/?my=false&status=pending')

        self.assertEqual(response.status_code, 200)
        request_ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(self.leave_request.id), request_ids)

    def test_final_approval_completes_request_and_deducts_balance(self):
        self.leave_request.first_approval_status = 'APPROVED'
        self.leave_request.current_approval_step = 'FINAL'
        self.leave_request.save()
        client = APIClient()
        client.force_authenticate(user=self.final_approver)

        response = client.post(
            f'/api/v1/leaves/requests/{self.leave_request.id}/approve/',
            {'comment': 'Final approval granted'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(self.leave_request.status, 'APPROVED')
        self.assertEqual(self.leave_request.current_approval_step, 'COMPLETED')
        self.assertEqual(self.leave_request.final_approval_status, 'APPROVED')
        self.assertEqual(self.leave_request.final_approval_comment, 'Final approval granted')
        self.assertEqual(self.leave_request.approved_by, self.final_approver)
        self.assertEqual(self.balance.used_hours, Decimal('8.00'))

    def test_final_approver_can_deny_and_reason_is_preserved(self):
        self.leave_request.first_approval_status = 'APPROVED'
        self.leave_request.current_approval_step = 'FINAL'
        self.leave_request.save()
        client = APIClient()
        client.force_authenticate(user=self.final_approver)

        response = client.post(
            f'/api/v1/leaves/requests/{self.leave_request.id}/reject/',
            {'reason': 'Insufficient staffing coverage'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.leave_request.refresh_from_db()
        self.assertEqual(self.leave_request.status, 'REJECTED')
        self.assertEqual(self.leave_request.final_approval_status, 'REJECTED')
        self.assertEqual(self.leave_request.rejection_reason, 'Insufficient staffing coverage')
        self.assertEqual(self.leave_request.current_approval_step, 'COMPLETED')

    def test_owner_detail_contains_two_step_timeline(self):
        self.leave_request.first_approval_status = 'APPROVED'
        self.leave_request.first_approval_comment = 'Looks good'
        self.leave_request.current_approval_step = 'FINAL'
        self.leave_request.save()
        client = APIClient()
        client.force_authenticate(user=self.employee)

        response = client.get(f'/api/v1/leaves/requests/{self.leave_request.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['approval_timeline']), 2)
        self.assertEqual(response.data['approval_timeline'][0]['step'], 'FIRST')
        self.assertEqual(response.data['approval_timeline'][0]['note'], 'Looks good')
        self.assertEqual(response.data['approval_timeline'][1]['step'], 'FINAL')
