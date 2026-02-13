"""
Tests for User Authentication (Login, Logout, Onboarding)
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date

User = get_user_model()


@pytest.mark.django_db
class TestAuthentication:
    """Test authentication endpoints"""

    def test_login_success(self):
        """Test successful login"""
        User.objects.create_user(email='test@example.com', password='TestPass123!')

        client = APIClient()
        response = client.post('/api/v1/auth/login/', {
            'email': 'test@example.com',
            'password': 'TestPass123!',
        })

        assert response.status_code == 200
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        User.objects.create_user(email='test@example.com', password='TestPass123!')

        client = APIClient()
        response = client.post('/api/v1/auth/login/', {
            'email': 'test@example.com',
            'password': 'WrongPassword123!',
        })

        assert response.status_code == 400

    def test_logout_success(self):
        """Test successful logout (token blacklist)"""
        user = User.objects.create_user(email='test@example.com', password='TestPass123!')

        client = APIClient()
        # Login first
        login_response = client.post('/api/v1/auth/login/', {
            'email': 'test@example.com',
            'password': 'TestPass123!',
        })

        access_token = login_response.data['tokens']['access']
        refresh_token = login_response.data['tokens']['refresh']

        # Set auth header for logout
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Logout
        logout_response = client.post('/api/v1/auth/logout/', {
            'refresh': refresh_token,
        })

        assert logout_response.status_code == 200

    def test_get_user_me_authenticated(self):
        """Test getting current user info when authenticated"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/auth/me/')

        assert response.status_code == 200
        assert response.data['email'] == 'test@example.com'

    def test_get_user_me_unauthenticated(self):
        """Test getting current user info without authentication"""
        client = APIClient()

        response = client.get('/api/v1/auth/me/')

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_onboarding_success(self):
        """Test successful onboarding"""
        from organizations.models import Entity, Location, Department

        # Create organization data
        entity = Entity.objects.create(name='Test Entity', code='TEST')
        location = Location.objects.create(
            entity=entity,
            name='Test Location',
            city='Test City',
            country='Test Country',
            timezone='UTC'
        )
        department = Department.objects.create(
            entity=entity,
            name='Test Department',
            code='TEST'
        )

        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/auth/onboarding/', {
            'entity': str(entity.id),
            'location': str(location.id),
            'department': str(department.id),
        })

        assert response.status_code == 200

        # Refresh user from DB and verify onboarding completed
        user.refresh_from_db()
        assert user.entity == entity
        assert user.location == location
        assert user.department == department
        assert user.has_completed_onboarding is True
