"""
Tests for Notifications API
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Notification

User = get_user_model()


@pytest.fixture
def setup_user_with_notifications():
    """Create a user with notifications for testing"""
    user = User.objects.create_user(
        email='test@example.com',
        password='TestPass123!',
        first_name='Test',
        last_name='User'
    )

    # Create notifications
    n1 = Notification.objects.create(
        user=user,
        type='LEAVE_APPROVED',
        title='Leave Approved',
        message='Your leave request has been approved',
        link='/leaves/1',
        is_read=False
    )
    n2 = Notification.objects.create(
        user=user,
        type='LEAVE_REJECTED',
        title='Leave Rejected',
        message='Your leave request has been rejected',
        link='/leaves/2',
        is_read=True
    )
    n3 = Notification.objects.create(
        user=user,
        type='BALANCE_ADJUSTED',
        title='Balance Adjusted',
        message='Your leave balance has been adjusted',
        link='/leaves/balance',
        is_read=False
    )

    return {'user': user, 'notifications': [n1, n2, n3]}


@pytest.mark.django_db
class TestNotifications:
    """Test notification endpoints"""

    def test_list_notifications(self, setup_user_with_notifications):
        """Test listing user's notifications"""
        user = setup_user_with_notifications['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/notifications/')

        assert response.status_code == 200
        assert response.data['count'] == 3
        assert response.data['unread_count'] == 2
        assert len(response.data['results']) == 3

    def test_unread_count(self, setup_user_with_notifications):
        """Test getting unread notification count"""
        user = setup_user_with_notifications['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/notifications/unread-count/')

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_mark_notification_read(self, setup_user_with_notifications):
        """Test marking a single notification as read"""
        user = setup_user_with_notifications['user']
        notifications = setup_user_with_notifications['notifications']
        unread_notification = notifications[0]

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(f'/api/v1/notifications/{unread_notification.id}/')

        assert response.status_code == 200
        assert response.data['is_read'] is True

        # Verify in database
        unread_notification.refresh_from_db()
        assert unread_notification.is_read is True

    def test_mark_all_read(self, setup_user_with_notifications):
        """Test marking all notifications as read"""
        user = setup_user_with_notifications['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/notifications/mark-all-read/')

        assert response.status_code == 200
        assert response.data['updated_count'] == 2

        # Verify unread count is now 0
        count_response = client.get('/api/v1/notifications/unread-count/')
        assert count_response.data['count'] == 0

    def test_notification_not_found(self, setup_user_with_notifications):
        """Test marking a non-existent notification as read"""
        user = setup_user_with_notifications['user']

        client = APIClient()
        client.force_authenticate(user=user)

        # Use a random UUID
        response = client.patch('/api/v1/notifications/00000000-0000-0000-0000-000000000000/')

        assert response.status_code == 404

    def test_delete_notification(self, setup_user_with_notifications):
        """Test deleting a single notification"""
        user = setup_user_with_notifications['user']
        notifications = setup_user_with_notifications['notifications']
        notification = notifications[0]

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.delete(f'/api/v1/notifications/{notification.id}/')

        assert response.status_code == 200
        assert response.data['deleted'] is True

        # Verify notification no longer exists
        assert not Notification.objects.filter(id=notification.id).exists()

    def test_dismiss_all_notifications(self, setup_user_with_notifications):
        """Test deleting all notifications for current user"""
        user = setup_user_with_notifications['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.delete('/api/v1/notifications/dismiss-all/')

        assert response.status_code == 200
        assert response.data['deleted_count'] == 3

        # Verify all notifications are deleted
        assert Notification.objects.filter(user=user).count() == 0
