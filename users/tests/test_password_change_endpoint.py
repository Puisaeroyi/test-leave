"""Tests for authenticated password-change endpoint and first-login regression."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

PASSWORD_CHANGE_URL = "/api/v1/auth/password-change/"
FIRST_LOGIN_CHANGE_URL = "/api/v1/auth/change-password/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
LOGIN_URL = "/api/v1/auth/login/"


@pytest.mark.django_db
class TestPasswordChangeEndpoint:
    def setup_method(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="change@example.com",
            password="CurrentPass123!",
            first_login=False,
        )
        self.client.force_authenticate(user=self.user)

    def test_wrong_current_password_leaves_password_unchanged(self):
        response = self.client.post(
            PASSWORD_CHANGE_URL,
            {
                "current_password": "WrongPass123!",
                "new_password": "BrandNewPass456!",
                "new_password_confirm": "BrandNewPass456!",
            },
        )
        assert response.status_code == 400
        assert "current_password" in response.data
        self.user.refresh_from_db()
        assert self.user.check_password("CurrentPass123!")

    def test_new_equals_current_rejected(self):
        response = self.client.post(
            PASSWORD_CHANGE_URL,
            {
                "current_password": "CurrentPass123!",
                "new_password": "CurrentPass123!",
                "new_password_confirm": "CurrentPass123!",
            },
        )
        assert response.status_code == 400
        assert "new_password" in response.data

    def test_weak_password_rejected(self):
        response = self.client.post(
            PASSWORD_CHANGE_URL,
            {
                "current_password": "CurrentPass123!",
                "new_password": "123",
                "new_password_confirm": "123",
            },
        )
        assert response.status_code == 400
        self.user.refresh_from_db()
        assert self.user.check_password("CurrentPass123!")

    def test_success_blacklists_old_refresh_and_returns_valid_pair(self):
        old_refresh = str(RefreshToken.for_user(self.user))

        response = self.client.post(
            PASSWORD_CHANGE_URL,
            {
                "current_password": "CurrentPass123!",
                "new_password": "BrandNewPass456!",
                "new_password_confirm": "BrandNewPass456!",
            },
        )

        assert response.status_code == 200
        assert "tokens" in response.data["user"]
        new_refresh = response.data["user"]["tokens"]["refresh"]
        new_access = response.data["user"]["tokens"]["access"]
        assert new_access
        assert new_refresh

        self.user.refresh_from_db()
        assert self.user.check_password("BrandNewPass456!")

        old_refresh_resp = self.client.post(REFRESH_URL, {"refresh": old_refresh})
        assert old_refresh_resp.status_code in (401, 400)

        # Fresh refresh must work (issued after blacklist sweep)
        unauth = APIClient()
        new_refresh_resp = unauth.post(REFRESH_URL, {"refresh": new_refresh})
        assert new_refresh_resp.status_code == 200
        assert "access" in new_refresh_resp.data

    def test_unauthenticated_rejected(self):
        client = APIClient()
        response = client.post(
            PASSWORD_CHANGE_URL,
            {
                "current_password": "CurrentPass123!",
                "new_password": "BrandNewPass456!",
                "new_password_confirm": "BrandNewPass456!",
            },
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestFirstLoginChangePasswordRegression:
    """First-login ChangePasswordView must remain unchanged."""

    def setup_method(self):
        cache.clear()
        self.client = APIClient()

    def test_first_login_true_allows_password_change(self):
        user = User.objects.create_user(
            email="first@example.com",
            password="TempPass123!",
            first_login=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            FIRST_LOGIN_CHANGE_URL,
            {
                "password": "FirstLoginPass456!",
                "password_confirm": "FirstLoginPass456!",
            },
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_login is False
        assert user.check_password("FirstLoginPass456!")
        assert "tokens" in response.data["user"]

    def test_first_login_false_forbidden(self):
        user = User.objects.create_user(
            email="already@example.com",
            password="AlreadyPass123!",
            first_login=False,
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            FIRST_LOGIN_CHANGE_URL,
            {
                "password": "ShouldNotWork456!",
                "password_confirm": "ShouldNotWork456!",
            },
        )

        assert response.status_code == 403
        user.refresh_from_db()
        assert user.check_password("AlreadyPass123!")
