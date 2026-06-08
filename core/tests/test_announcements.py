"""
Tests for admin-managed announcements.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import timedelta

from core.models import Announcement

User = get_user_model()


class AnnouncementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='TestPass123!',
            role=User.Role.ADMIN,
            first_name='Admin',
            last_name='User',
        )
        self.hr = User.objects.create_user(
            email='hr@example.com',
            password='TestPass123!',
            role=User.Role.HR,
        )
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='TestPass123!',
            role=User.Role.EMPLOYEE,
        )

    def test_admin_can_create_announcement(self):
        client = APIClient()
        client.force_authenticate(user=self.admin)

        response = client.post('/api/v1/notifications/announcements/', {
            'title': 'Policy Update',
            'body': 'Please read the new leave policy.',
            'is_active': True,
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], 'Policy Update')
        self.assertEqual(response.data['body'], 'Please read the new leave policy.')
        self.assertIs(response.data['is_active'], True)
        self.assertEqual(response.data['created_by'], 'admin@example.com')
        self.assertEqual(response.data['created_by_name'], 'Admin User')
        self.assertTrue(Announcement.objects.filter(title='Policy Update').exists())

    def test_admin_can_create_rich_announcement_content(self):
        client = APIClient()
        client.force_authenticate(user=self.admin)

        response = client.post('/api/v1/notifications/announcements/', {
            'title': 'Formatted Update',
            'body': 'Formatted body preview.',
            'body_html': (
                '<h1 style="text-align: center">Formatted body</h1>'
                '<p style="text-align: justify"><strong>Important</strong> update copied from Word.</p>'
                '<figure><img src="data:image/png;base64,abcd" alt="Chart"><figcaption>Chart caption</figcaption></figure>'
                '<script>alert("xss")</script>'
            ),
            'is_active': True,
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('text-align: center', response.data['body_html'])
        self.assertIn('text-align: justify', response.data['body_html'])
        self.assertIn('<strong>Important</strong>', response.data['body_html'])
        self.assertIn('<figcaption>Chart caption</figcaption>', response.data['body_html'])
        self.assertIn('data:image/png;base64,abcd', response.data['body_html'])
        self.assertNotIn('<script>', response.data['body_html'])

    def test_non_admin_cannot_create_announcement(self):
        client = APIClient()
        client.force_authenticate(user=self.hr)

        response = client.post('/api/v1/notifications/announcements/', {
            'title': 'HR Update',
            'body': 'This should not be allowed.',
        }, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Announcement.objects.filter(title='HR Update').exists())

    def test_non_admin_only_sees_active_announcements(self):
        now = timezone.now()
        Announcement.objects.create(
            title='Visible',
            body='Visible to users.',
            is_active=True,
            starts_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=1),
            created_by=self.admin,
        )
        Announcement.objects.create(
            title='Draft',
            body='Admin only.',
            is_active=False,
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.employee)

        response = client.get('/api/v1/notifications/announcements/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.data['results']], ['Visible'])

    def test_non_admin_does_not_see_scheduled_or_expired_announcements(self):
        now = timezone.now()
        expired = Announcement.objects.create(
            title='Expired',
            body='Expired announcement.',
            is_active=True,
            starts_at=now - timedelta(days=2),
            expires_at=now - timedelta(days=1),
            created_by=self.admin,
        )
        Announcement.objects.create(
            title='Scheduled',
            body='Scheduled announcement.',
            is_active=True,
            starts_at=now + timedelta(days=1),
            expires_at=now + timedelta(days=2),
            created_by=self.admin,
        )
        Announcement.objects.create(
            title='Current',
            body='Current announcement.',
            is_active=True,
            starts_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=1),
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.employee)

        response = client.get('/api/v1/notifications/announcements/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.data['results']], ['Current'])
        expired.refresh_from_db()
        self.assertIs(expired.is_active, False)

    def test_admin_default_list_only_shows_visible_announcements(self):
        Announcement.objects.create(
            title='Visible',
            body='Visible to users.',
            is_active=True,
            created_by=self.admin,
        )
        Announcement.objects.create(
            title='Draft',
            body='Admin only.',
            is_active=False,
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)

        response = client.get('/api/v1/notifications/announcements/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['title'] for item in response.data['results']], ['Visible'])

    def test_admin_can_include_inactive_announcements_for_management(self):
        now = timezone.now()
        Announcement.objects.create(
            title='Visible',
            body='Visible to users.',
            is_active=True,
            created_by=self.admin,
        )
        Announcement.objects.create(
            title='Draft',
            body='Admin only.',
            is_active=False,
            created_by=self.admin,
        )
        Announcement.objects.create(
            title='Expired',
            body='Expired admin article.',
            is_active=True,
            starts_at=now - timedelta(days=2),
            expires_at=now - timedelta(days=1),
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)

        response = client.get('/api/v1/notifications/announcements/?include_inactive=true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item['title'] for item in response.data['results']},
            {'Visible', 'Draft', 'Expired'},
        )

    def test_announcements_are_paginated_newest_first(self):
        older = Announcement.objects.create(
            title='Older',
            body='Older announcement.',
            is_active=True,
            created_by=self.admin,
        )
        newer = Announcement.objects.create(
            title='Newer',
            body='Newer announcement.',
            is_active=True,
            created_by=self.admin,
        )
        Announcement.objects.filter(pk=newer.pk).update(created_at=older.created_at.replace(year=older.created_at.year + 1))

        client = APIClient()
        client.force_authenticate(user=self.employee)

        response = client.get('/api/v1/notifications/announcements/?page=1&page_size=1')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertTrue(response.data['next'])
        self.assertFalse(response.data['previous'])
        self.assertEqual([item['title'] for item in response.data['results']], ['Newer'])
