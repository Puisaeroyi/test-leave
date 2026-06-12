from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from organizations.models import Department, Entity, Location
from users.models import User


class UserManagementApiTests(TestCase):
    def setUp(self):
        self.entity = Entity.objects.create(
            entity_name='Test Company',
            code='TEST',
        )
        self.location = Location.objects.create(
            entity=self.entity,
            location_name='Test Office',
            city='Ho Chi Minh City',
            country='Vietnam',
            timezone='Asia/Ho_Chi_Minh',
        )
        self.department = Department.objects.create(
            entity=self.entity,
            location=self.location,
            department_name='Engineering',
            code='ENG',
        )
        self.admin = User.objects.create_user(
            email='admin-create-user@example.com',
            password='AdminPass123!',
            role=User.Role.ADMIN,
            entity=self.entity,
            location=self.location,
            department=self.department,
        )
        self.first_approver = User.objects.create_user(
            email='first-approver-create-user@example.com',
            password='ApproverPass123!',
            role=User.Role.MANAGER,
            entity=self.entity,
            location=self.location,
            department=self.department,
        )
        self.second_approver = User.objects.create_user(
            email='second-approver-create-user@example.com',
            password='ApproverPass123!',
            role=User.Role.MANAGER,
            entity=self.entity,
            location=self.location,
            department=self.department,
        )
        self.third_approver = User.objects.create_user(
            email='third-approver-create-user@example.com',
            password='ApproverPass123!',
            role=User.Role.MANAGER,
            entity=self.entity,
            location=self.location,
            department=self.department,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.hr = User.objects.create_user(
            email='hr-user-management@example.com',
            password='HrPass123!',
            role=User.Role.HR,
            entity=self.entity,
            location=self.location,
            department=self.department,
            approver_1=self.first_approver,
            approver_2=self.second_approver,
        )
        self.other_entity = Entity.objects.create(
            entity_name='Other Company',
            code='OTHER',
        )
        self.other_location = Location.objects.create(
            entity=self.other_entity,
            location_name='Other Office',
            city='Da Nang',
            country='Vietnam',
            timezone='Asia/Ho_Chi_Minh',
        )
        self.other_department = Department.objects.create(
            entity=self.other_entity,
            location=self.other_location,
            department_name='Other Engineering',
            code='OTHER_ENG',
        )
        self.other_user = User.objects.create_user(
            email='other-entity-user@example.com',
            password='OtherPass123!',
            role=User.Role.EMPLOYEE,
            entity=self.other_entity,
            location=self.other_location,
            department=self.other_department,
        )

    @patch.dict('os.environ', {'DEFAULT_IMPORT_PASSWORD': 'DefaultPass123!'})
    def test_admin_can_create_user_with_default_password_and_two_approvers(self):
        response = self.client.post('/api/v1/auth/users/', {
            'email': 'new-user-create-user@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'employee_code': 'NEW001',
            'role': User.Role.EMPLOYEE,
            'entity': str(self.entity.id),
            'location': str(self.location.id),
            'department': str(self.department.id),
            'approver': str(self.first_approver.id),
            'final_approver': str(self.second_approver.id),
        }, format='json')

        self.assertEqual(response.status_code, 201, response.content)

        user = User.objects.get(email='new-user-create-user@example.com')
        self.assertTrue(user.check_password('DefaultPass123!'))
        self.assertTrue(user.first_login)
        self.assertEqual(user.approver_1, self.first_approver)
        self.assertEqual(user.approver_2, self.second_approver)
        self.assertNotIn('work_shift', response.data)
        self.assertEqual(response.data['approver']['id'], str(self.first_approver.id))
        self.assertEqual(response.data['final_approver']['id'], str(self.second_approver.id))

    def test_user_update_ignores_removed_work_shift_payload(self):
        response = self.client.patch(
            f'/api/v1/auth/users/{self.first_approver.id}/',
            {'work_shift': '00000000-0000-0000-0000-000000000000'},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn('work_shift', response.data)

    def test_hr_lists_only_users_in_own_entity(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.get('/api/v1/auth/users/')

        self.assertEqual(response.status_code, 200)
        user_ids = {item['id'] for item in response.data}
        self.assertIn(str(self.first_approver.id), user_ids)
        self.assertNotIn(str(self.other_user.id), user_ids)

    def test_admin_still_lists_users_across_entities(self):
        response = self.client.get('/api/v1/auth/users/')

        self.assertEqual(response.status_code, 200)
        user_ids = {item['id'] for item in response.data}
        self.assertIn(str(self.first_approver.id), user_ids)
        self.assertIn(str(self.other_user.id), user_ids)

    def test_hr_cannot_retrieve_or_update_user_from_another_entity(self):
        self.client.force_authenticate(user=self.hr)

        detail_response = self.client.get(f'/api/v1/auth/users/{self.other_user.id}/')
        update_response = self.client.patch(
            f'/api/v1/auth/users/{self.other_user.id}/',
            {'first_name': 'Unauthorized'},
            format='json',
        )

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(update_response.status_code, 404)
        self.other_user.refresh_from_db()
        self.assertNotEqual(self.other_user.first_name, 'Unauthorized')

    def test_hr_cannot_change_own_first_approver(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.patch(
            f'/api/v1/auth/users/{self.hr.id}/',
            {'approver': str(self.third_approver.id)},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.hr.refresh_from_db()
        self.assertEqual(self.hr.approver_1, self.first_approver)

    def test_hr_cannot_change_own_second_approver(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.patch(
            f'/api/v1/auth/users/{self.hr.id}/',
            {'final_approver': str(self.third_approver.id)},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.hr.refresh_from_db()
        self.assertEqual(self.hr.approver_2, self.second_approver)

    def test_hr_cannot_clear_own_approvers_through_api(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.patch(
            f'/api/v1/auth/users/{self.hr.id}/',
            {'approver': None, 'final_approver': None},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.hr.refresh_from_db()
        self.assertEqual(self.hr.approver_1, self.first_approver)
        self.assertEqual(self.hr.approver_2, self.second_approver)

    def test_hr_can_change_approvers_for_user_in_own_entity(self):
        employee = User.objects.create_user(
            email='same-entity-employee@example.com',
            password='EmployeePass123!',
            role=User.Role.EMPLOYEE,
            entity=self.entity,
            location=self.location,
            department=self.department,
            approver_1=self.first_approver,
        )
        self.client.force_authenticate(user=self.hr)

        response = self.client.patch(
            f'/api/v1/auth/users/{employee.id}/',
            {
                'approver': str(self.second_approver.id),
                'final_approver': str(self.third_approver.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.content)
        employee.refresh_from_db()
        self.assertEqual(employee.approver_1, self.second_approver)
        self.assertEqual(employee.approver_2, self.third_approver)

    def test_admin_can_change_approvers_for_any_user(self):
        response = self.client.patch(
            f'/api/v1/auth/users/{self.other_user.id}/',
            {
                'approver': str(self.first_approver.id),
                'final_approver': str(self.second_approver.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.other_user.refresh_from_db()
        self.assertEqual(self.other_user.approver_1, self.first_approver)
        self.assertEqual(self.other_user.approver_2, self.second_approver)

    @patch.dict('os.environ', {'DEFAULT_IMPORT_PASSWORD': 'DefaultPass123!'})
    def test_hr_cannot_create_user_in_another_entity(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.post('/api/v1/auth/users/', {
            'email': 'unauthorized-other-user@example.com',
            'first_name': 'Other',
            'last_name': 'User',
            'role': User.Role.EMPLOYEE,
            'entity': str(self.other_entity.id),
            'location': str(self.other_location.id),
            'department': str(self.other_department.id),
            'approver': str(self.other_user.id),
        }, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(email='unauthorized-other-user@example.com').exists())

    @patch.dict('os.environ', {'DEFAULT_IMPORT_PASSWORD': 'DefaultPass123!'})
    def test_hr_cannot_create_admin_user(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.post('/api/v1/auth/users/', {
            'email': 'unauthorized-admin@example.com',
            'first_name': 'Unauthorized',
            'last_name': 'Admin',
            'role': User.Role.ADMIN,
            'entity': str(self.entity.id),
            'location': str(self.location.id),
            'department': str(self.department.id),
            'approver': str(self.first_approver.id),
        }, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(email='unauthorized-admin@example.com').exists())

    def test_hr_cannot_adjust_balance_for_user_from_another_entity(self):
        self.client.force_authenticate(user=self.hr)

        response = self.client.put(
            f'/api/v1/auth/{self.other_user.id}/balance/adjust/',
            {
                'allocated_hours': 80,
                'balance_type': 'VACATION',
                'reason': 'Unauthorized adjustment',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_hr_without_entity_cannot_view_or_adjust_unassigned_users(self):
        unassigned_hr = User.objects.create_user(
            email='unassigned-hr@example.com',
            password='HrPass123!',
            role=User.Role.HR,
        )
        unassigned_user = User.objects.create_user(
            email='unassigned-user@example.com',
            password='UserPass123!',
            role=User.Role.EMPLOYEE,
        )
        self.client.force_authenticate(user=unassigned_hr)

        list_response = self.client.get('/api/v1/auth/users/')
        balance_response = self.client.put(
            f'/api/v1/auth/{unassigned_user.id}/balance/adjust/',
            {
                'allocated_hours': 80,
                'balance_type': 'VACATION',
                'reason': 'Unauthorized adjustment',
            },
            format='json',
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data, [])
        self.assertEqual(balance_response.status_code, 404)
