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
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

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
        self.assertEqual(response.data['approver']['id'], str(self.first_approver.id))
        self.assertEqual(response.data['final_approver']['id'], str(self.second_approver.id))
