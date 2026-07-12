"""Tests for the shared credential verification service."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

from users.services.credential_verification import (
    CredentialOutcome,
    login_failure_cache_key,
    verify_credentials,
)


User = get_user_model()


@pytest.fixture(autouse=True)
def clear_login_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestCredentialVerification:
    def test_returns_authenticated_for_active_user(self):
        user = User.objects.create_user(
            email="active@example.com",
            password="TestPass123!",
            first_login=False,
        )

        result = verify_credentials("ACTIVE@example.com", "TestPass123!")

        assert result.outcome == CredentialOutcome.AUTHENTICATED
        assert result.user == user

    def test_returns_must_change_password_after_valid_password(self):
        user = User.objects.create_user(
            email="first@example.com",
            password="TestPass123!",
            first_login=True,
        )

        result = verify_credentials("first@example.com", "TestPass123!")

        assert result.outcome == CredentialOutcome.MUST_CHANGE_PASSWORD
        assert result.user == user

    @pytest.mark.parametrize("email", ["unknown@example.com", "active@example.com"])
    def test_returns_same_outcome_for_unknown_email_and_wrong_password(self, email):
        User.objects.create_user(
            email="active@example.com",
            password="TestPass123!",
            first_login=False,
        )

        result = verify_credentials(email, "WrongPass123!")

        assert result.outcome == CredentialOutcome.INVALID_CREDENTIALS
        assert result.user is None

    def test_returns_inactive_only_after_valid_password(self):
        user = User.objects.create_user(
            email="inactive@example.com",
            password="TestPass123!",
            first_login=False,
            is_active=False,
        )

        result = verify_credentials("inactive@example.com", "TestPass123!")

        assert result.outcome == CredentialOutcome.ACCOUNT_INACTIVE
        assert result.user == user

    def test_returns_business_inactive_only_after_valid_password(self):
        user = User.objects.create_user(
            email="disabled@example.com",
            password="TestPass123!",
            first_login=False,
            status=User.Status.INACTIVE,
        )

        result = verify_credentials("disabled@example.com", "TestPass123!")

        assert result.outcome == CredentialOutcome.ACCOUNT_INACTIVE
        assert result.user == user

    def test_locks_identity_after_maximum_failed_attempts(self):
        User.objects.create_user(
            email="locked@example.com",
            password="TestPass123!",
            first_login=False,
        )

        for _ in range(5):
            result = verify_credentials("locked@example.com", "WrongPass123!")
            assert result.outcome == CredentialOutcome.INVALID_CREDENTIALS

        result = verify_credentials("locked@example.com", "TestPass123!")

        assert result.outcome == CredentialOutcome.ACCOUNT_LOCKED
        assert result.user is None

    def test_login_failure_cache_key_does_not_expose_email(self):
        key = login_failure_cache_key("Employee@Example.com")

        assert "employee@example.com" not in key
        assert "Employee@Example.com" not in key
