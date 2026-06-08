"""Tests for unordered peer leave approval."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.test import TestCase

from core.models import Notification
from leaves.models import BusinessTrip, LeaveBalance, LeaveCategory, LeaveRequest
from leaves.serializers import LeaveRequestSerializer
from leaves.services import LeaveApprovalService
from organizations.models import Entity
from users.utils import build_user_response

User = get_user_model()


class PeerApprovalTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='TestPass123!',
            role=User.Role.EMPLOYEE,
        )
        self.approver_1 = User.objects.create_user(
            email='approver-1@example.com',
            password='TestPass123!',
            role=User.Role.MANAGER,
            first_name='Approver',
            last_name='One',
        )
        self.approver_2 = User.objects.create_user(
            email='approver-2@example.com',
            password='TestPass123!',
            role=User.Role.MANAGER,
            first_name='Approver',
            last_name='Two',
        )
        self.employee.approver_1 = self.approver_1
        self.employee.approver_2 = self.approver_2
        self.employee.save()
        self.category, _ = LeaveCategory.objects.update_or_create(
            code='VACATION',
            defaults={
                'category_name': 'Vacation',
                'balance_bucket': 'VACATION',
            },
        )
        self.balance = LeaveBalance.objects.create(
            user=self.employee,
            year=2027,
            balance_type='VACATION',
            allocated_hours=Decimal('80.00'),
        )

    def assign_separate_entities(self):
        employee_entity = Entity.objects.create(entity_name='Employee Entity', code='EMPENT')
        peer_entity = Entity.objects.create(entity_name='Peer Entity', code='PEERENT')
        self.employee.entity = employee_entity
        self.employee.save()
        self.approver_2.entity = peer_entity
        self.approver_2.save()

    def make_request(self, **kwargs):
        defaults = {
            'user': self.employee,
            'leave_category': self.category,
            'start_date': date(2027, 1, 20),
            'end_date': date(2027, 1, 20),
            'shift_type': 'FULL_DAY',
            'total_hours': Decimal('8.00'),
            'status': 'PENDING',
            'first_approver': self.approver_1,
            'final_approver': self.approver_2,
        }
        defaults.update(kwargs)
        return LeaveRequest.objects.create(**defaults)

    def post_approve(self, actor, leave_request, comment='Approved'):
        client = APIClient()
        client.force_authenticate(user=actor)
        return client.post(
            f'/api/v1/leaves/requests/{leave_request.id}/approve/',
            {'comment': comment},
            format='json',
        )

    def post_reject(self, actor, leave_request, reason='Insufficient staffing coverage'):
        client = APIClient()
        client.force_authenticate(user=actor)
        return client.post(
            f'/api/v1/leaves/requests/{leave_request.id}/reject/',
            {'reason': reason},
            format='json',
        )

    def test_both_approve_any_order_completes(self):
        leave_request = self.make_request()

        response = self.post_approve(self.approver_1, leave_request, 'ok-A')
        self.assertEqual(response.status_code, 200)
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(leave_request.status, 'PENDING')
        self.assertEqual(leave_request.first_approval_status, 'APPROVED')
        self.assertEqual(self.balance.used_hours, Decimal('0.00'))

        response = self.post_approve(self.approver_2, leave_request, 'ok-B')
        self.assertEqual(response.status_code, 200)
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(leave_request.status, 'APPROVED')
        self.assertEqual(leave_request.final_approval_status, 'APPROVED')
        self.assertEqual(leave_request.current_approval_step, 'COMPLETED')
        self.assertEqual(self.balance.used_hours, Decimal('8.00'))

    def test_reverse_order_also_completes(self):
        leave_request = self.make_request()

        self.assertEqual(self.post_approve(self.approver_2, leave_request, 'ok-B').status_code, 200)
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'PENDING')
        self.assertEqual(leave_request.final_approval_status, 'APPROVED')

        self.assertEqual(self.post_approve(self.approver_1, leave_request, 'ok-A').status_code, 200)
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(leave_request.status, 'APPROVED')
        self.assertEqual(self.balance.used_hours, Decimal('8.00'))

    def test_single_rejection_denies_without_deducting_balance(self):
        leave_request = self.make_request()

        self.assertEqual(self.post_approve(self.approver_1, leave_request, 'ok-A').status_code, 200)
        self.assertEqual(self.post_reject(self.approver_2, leave_request).status_code, 200)
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(leave_request.status, 'REJECTED')
        self.assertEqual(leave_request.final_approval_status, 'REJECTED')
        self.assertEqual(self.balance.used_hours, Decimal('0.00'))

    def test_first_rejection_denies_immediately(self):
        leave_request = self.make_request()

        response = self.post_reject(self.approver_1, leave_request)

        self.assertEqual(response.status_code, 200)
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'REJECTED')
        self.assertEqual(leave_request.first_approval_status, 'REJECTED')

    def test_single_approver_completes_alone(self):
        self.employee.approver_2 = None
        self.employee.save()
        leave_request = self.make_request(final_approver=None)

        response = self.post_approve(self.approver_1, leave_request)

        self.assertEqual(response.status_code, 200)
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(leave_request.status, 'APPROVED')
        self.assertEqual(self.balance.used_hours, Decimal('8.00'))

    def test_peer_cannot_act_twice(self):
        leave_request = self.make_request()
        self.assertEqual(self.post_approve(self.approver_1, leave_request).status_code, 200)

        response = self.post_approve(self.approver_1, leave_request)

        self.assertEqual(response.status_code, 403)
        leave_request.refresh_from_db()
        self.assertEqual(leave_request.status, 'PENDING')

    def test_24h_post_approval_reject_rolls_back(self):
        future_start = date(2027, 1, 20)
        leave_request = self.make_request(start_date=future_start, end_date=future_start)
        self.assertEqual(self.post_approve(self.approver_1, leave_request).status_code, 200)
        self.assertEqual(self.post_approve(self.approver_2, leave_request).status_code, 200)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.used_hours, Decimal('8.00'))

        response = self.post_reject(self.approver_1, leave_request, 'Coverage changed after approval')

        self.assertEqual(response.status_code, 200)
        leave_request.refresh_from_db()
        self.balance.refresh_from_db()
        self.assertEqual(leave_request.status, 'REJECTED')
        self.assertEqual(self.balance.used_hours, Decimal('0.00'))

    def test_both_peers_see_pending_request(self):
        leave_request = self.make_request()

        ids_1 = {req.id for req in LeaveApprovalService.get_pending_requests_for_manager(self.approver_1)}
        ids_2 = {req.id for req in LeaveApprovalService.get_pending_requests_for_manager(self.approver_2)}

        self.assertIn(leave_request.id, ids_1)
        self.assertIn(leave_request.id, ids_2)

    def test_approver_2_sees_subordinate_in_team_calendar(self):
        self.assign_separate_entities()
        client = APIClient()
        client.force_authenticate(user=self.approver_2)

        response = client.get('/api/v1/leaves/calendar/?month=1&year=2027')

        self.assertEqual(response.status_code, 200)
        member_ids = {item['id'] for item in response.data['team_members']}
        self.assertIn(str(self.employee.id), member_ids)

    def test_approver_2_sees_subordinate_business_trips(self):
        self.assign_separate_entities()
        trip = BusinessTrip.objects.create(
            user=self.employee,
            city='Tokyo',
            country='Japan',
            start_date=date(2027, 1, 20),
            end_date=date(2027, 1, 21),
            note='Client visit',
        )
        client = APIClient()
        client.force_authenticate(user=self.approver_2)

        response = client.get('/api/v1/leaves/business-trips/team/')

        self.assertEqual(response.status_code, 200)
        trip_ids = {item['id'] for item in response.data['results']}
        self.assertIn(str(trip.id), trip_ids)

    def test_acted_peer_still_sees_request_while_co_pending(self):
        leave_request = self.make_request()
        self.assertEqual(self.post_approve(self.approver_1, leave_request).status_code, 200)

        ids = {req.id for req in LeaveApprovalService.get_pending_requests_for_manager(self.approver_1)}

        self.assertIn(leave_request.id, ids)

    def test_action_required_user_ids_lists_pending_peers(self):
        leave_request = self.make_request()
        data = LeaveRequestSerializer(leave_request).data
        self.assertEqual(
            set(data['action_required_user_ids']),
            {str(self.approver_1.id), str(self.approver_2.id)},
        )

        self.assertEqual(self.post_approve(self.approver_1, leave_request).status_code, 200)
        leave_request.refresh_from_db()
        data = LeaveRequestSerializer(leave_request).data
        self.assertEqual(data['action_required_user_ids'], [str(self.approver_2.id)])

        self.assertEqual(self.post_approve(self.approver_2, leave_request).status_code, 200)
        leave_request.refresh_from_db()
        data = LeaveRequestSerializer(leave_request).data
        self.assertEqual(data['action_required_user_ids'], [])

    def test_single_approver_timeline_shows_only_approver_label(self):
        self.employee.approver_2 = None
        self.employee.save()
        leave_request = self.make_request(final_approver=None)

        data = LeaveRequestSerializer(leave_request).data

        self.assertEqual(len(data['approval_timeline']), 1)
        self.assertEqual(data['approval_timeline'][0]['step'], 'FIRST')
        self.assertEqual(data['approval_timeline'][0]['label'], 'Approver')
        self.assertEqual(data['approval_timeline'][0]['approver_id'], str(self.approver_1.id))

    def test_two_approver_timeline_shows_first_and_second_labels(self):
        leave_request = self.make_request()

        data = LeaveRequestSerializer(leave_request).data

        self.assertEqual(
            [step['label'] for step in data['approval_timeline']],
            ['First Approver', 'Second Approver'],
        )

    def test_user_has_approver_1_and_2_fields(self):
        self.assertEqual(self.employee.approver_1, self.approver_1)
        self.assertEqual(self.employee.approver_2, self.approver_2)
        with self.assertRaises(AttributeError):
            getattr(self.employee, 'approver')
        with self.assertRaises(AttributeError):
            getattr(self.employee, 'final_approver')

    def test_me_payload_keeps_external_keys(self):
        data = build_user_response(self.employee)

        self.assertEqual(data['approver']['id'], str(self.approver_1.id))
        self.assertEqual(data['final_approver']['id'], str(self.approver_2.id))

    def test_both_peers_notified_at_creation(self):
        client = APIClient()
        client.force_authenticate(user=self.employee)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2027-01-20',
            'end_date': '2027-01-20',
            'shift_type': 'FULL_DAY',
            'leave_category': str(self.category.id),
            'reason': 'Family plans',
        })

        self.assertEqual(response.status_code, 201)
        leave_request_id = response.data['id']
        recipients = set(
            Notification.objects.filter(
                related_object_id=leave_request_id,
                type='LEAVE_PENDING',
            ).values_list('user_id', flat=True)
        )
        self.assertEqual(recipients, {self.approver_1.id, self.approver_2.id})

    def test_no_email_or_notification_on_first_peer_action(self):
        leave_request = self.make_request()
        Notification.objects.create(
            user=self.approver_1,
            type='LEAVE_PENDING',
            title='Pending',
            message='Pending',
            related_object_id=leave_request.id,
        )
        Notification.objects.create(
            user=self.approver_2,
            type='LEAVE_PENDING',
            title='Pending',
            message='Pending',
            related_object_id=leave_request.id,
        )

        response = self.post_approve(self.approver_1, leave_request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Notification.objects.filter(
                related_object_id=leave_request.id,
                type='LEAVE_PENDING',
            ).count(),
            2,
        )
