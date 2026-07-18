"""Contract and security tests for the internal credential API."""

import hashlib
import hmac
import json
import time
import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from rest_framework.test import APIClient

from users.views.internal_auth import InternalAuthRateThrottle
from users.services.internal_service_auth import validate_service_secret_config


User = get_user_model()
ENDPOINT = "/api/v1/auth/internal/verify/"
STATUS_ENDPOINT = "/api/v1/auth/internal/status/"
LOOKUP_ENDPOINT = "/api/v1/auth/internal/lookup/"
SERVICE_ID = "document-control"
SERVICE_SECRET = "test-internal-secret-with-at-least-32-bytes"


def signed_headers(
    body: bytes,
    *,
    nonce=None,
    timestamp=None,
    secret=SERVICE_SECRET,
    path=ENDPOINT,
):
    timestamp = str(timestamp or int(time.time()))
    nonce = nonce or str(uuid.uuid4())
    body_digest = hashlib.sha256(body).hexdigest()
    canonical = "\n".join(["POST", path, timestamp, nonce, body_digest])
    signature = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "HTTP_X_SERVICE_ID": SERVICE_ID,
        "HTTP_X_TIMESTAMP": timestamp,
        "HTTP_X_NONCE": nonce,
        "HTTP_X_SIGNATURE": signature,
    }


def post_json(client, payload, **header_overrides):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = signed_headers(body)
    headers.update(header_overrides)
    return client.generic(
        "POST",
        ENDPOINT,
        body,
        content_type="application/json",
        secure=True,
        **headers,
    )


@pytest.fixture(autouse=True)
def clear_internal_auth_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_rejects_weak_internal_service_secret_configuration():
    with pytest.raises(ImproperlyConfigured):
        validate_service_secret_config({SERVICE_ID: "short"})


@pytest.mark.django_db
def test_internal_auth_throttle_key_does_not_expose_email():
    request = type("Request", (), {})()
    request.auth = SERVICE_ID
    request.data = {"email": "Employee@Example.com"}

    key = InternalAuthRateThrottle().get_cache_key(request, None)

    assert "employee@example.com" not in key
    assert "Employee@Example.com" not in key


@pytest.mark.django_db
class TestInternalAuthenticationAPI:
    @override_settings(INTERNAL_AUTH_ENABLED=False)
    def test_endpoint_is_hidden_when_feature_is_disabled(self):
        response = APIClient().post(ENDPOINT, {}, format="json", secure=True)

        assert response.status_code == 404

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_returns_minimum_user_identity_for_valid_credentials(self):
        user = User.objects.create_user(
            email="employee@example.com",
            password="TestPass123!",
            first_login=False,
            first_name="Employee",
            last_name="Name",
            employee_code="E001",
        )

        response = post_json(APIClient(), {
            "email": "employee@example.com",
            "password": "TestPass123!",
        })

        assert response.status_code == 200
        assert response.json() == {
            "authenticated": True,
            "user": {
                "external_user_id": str(user.id),
                "email": "employee@example.com",
                "full_name": "Employee Name",
                "employee_code": "E001",
            },
        }

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_rejects_invalid_service_signature_before_credentials(self):
        body = json.dumps({
            "email": "employee@example.com",
            "password": "TestPass123!",
        }, separators=(",", ":")).encode("utf-8")
        headers = signed_headers(body, secret="wrong-secret")

        response = APIClient().generic(
            "POST", ENDPOINT, body, content_type="application/json",
            secure=True, **headers,
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid service authentication."}

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: [SERVICE_SECRET, "rotated-secret-with-at-least-32-bytes"]},
    )
    def test_accepts_any_configured_secret_for_zero_downtime_rotation(self):
        User.objects.create_user(
            email="employee@example.com",
            password="TestPass123!",
            first_login=False,
        )

        response = post_json(APIClient(), {
            "email": "employee@example.com",
            "password": "TestPass123!",
        }, **signed_headers(
            json.dumps({
                "email": "employee@example.com",
                "password": "TestPass123!",
            }, separators=(",", ":")).encode("utf-8"),
            secret="rotated-secret-with-at-least-32-bytes",
        ))

        assert response.status_code == 200
        assert response.json()["authenticated"] is True

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
        INTERNAL_AUTH_MAX_BODY_BYTES=32,
    )
    def test_rejects_oversized_internal_auth_body_before_parsing_credentials(self):
        body = json.dumps({
            "email": "employee@example.com",
            "password": "x" * 100,
        }, separators=(",", ":")).encode("utf-8")
        headers = signed_headers(body)

        response = APIClient().generic(
            "POST", ENDPOINT, body, content_type="application/json",
            secure=True, **headers,
        )

        assert response.status_code == 413
        assert response.json() == {"detail": "Request body is too large."}

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_unknown_email_and_wrong_password_share_public_response(self):
        User.objects.create_user(
            email="employee@example.com",
            password="TestPass123!",
            first_login=False,
        )
        client = APIClient()

        unknown = post_json(client, {
            "email": "unknown@example.com",
            "password": "WrongPass123!",
        })
        wrong = post_json(client, {
            "email": "employee@example.com",
            "password": "WrongPass123!",
        })

        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json() == wrong.json() == {
            "authenticated": False,
            "code": "INVALID_CREDENTIALS",
        }

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_blocks_valid_default_password_until_changed_in_a(self):
        User.objects.create_user(
            email="first@example.com",
            password="TestPass123!",
            first_login=True,
        )

        response = post_json(APIClient(), {
            "email": "first@example.com",
            "password": "TestPass123!",
        })

        assert response.status_code == 403
        assert response.json() == {
            "authenticated": False,
            "code": "MUST_CHANGE_PASSWORD",
        }

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_rejects_replayed_signed_request(self):
        User.objects.create_user(
            email="employee@example.com",
            password="TestPass123!",
            first_login=False,
        )
        payload = {
            "email": "employee@example.com",
            "password": "TestPass123!",
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = signed_headers(body, nonce="fixed-replay-nonce")
        client = APIClient()

        first = client.generic(
            "POST", ENDPOINT, body, content_type="application/json",
            secure=True, **headers,
        )
        replay = client.generic(
            "POST", ENDPOINT, body, content_type="application/json",
            secure=True, **headers,
        )

        assert first.status_code == 200
        assert replay.status_code == 401
        assert replay.json() == {"detail": "Invalid service authentication."}

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    @patch("users.views.internal_auth.logger")
    def test_audit_log_records_outcome_without_password(self, logger):
        User.objects.create_user(
            email="audit@example.com",
            password="AuditPass123!",
            first_login=False,
        )

        response = post_json(APIClient(), {
            "email": "audit@example.com",
            "password": "AuditPass123!",
        })

        assert response.status_code == 200
        logger.info.assert_called_once()
        logged_values = " ".join(str(value) for value in logger.info.call_args.args)
        assert "AUTHENTICATED" in logged_values
        assert "AuditPass123!" not in logged_values


@pytest.mark.django_db
class TestInternalAccountStatusAPI:
    def post_status(self, user_id):
        body = json.dumps(
            {"external_user_id": str(user_id)}, separators=(",", ":")
        ).encode("utf-8")
        return APIClient().generic(
            "POST",
            STATUS_ENDPOINT,
            body,
            content_type="application/json",
            secure=True,
            **signed_headers(body, path=STATUS_ENDPOINT),
        )

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_returns_active_status_without_password(self):
        user = User.objects.create_user(
            email="status@example.com",
            password="TestPass123!",
            first_login=False,
        )

        response = self.post_status(user.id)

        assert response.status_code == 200
        assert response.json() == {
            "active": True,
            "external_user_id": str(user.id),
            "email": "status@example.com",
        }

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_returns_blocked_status_for_inactive_or_missing_identity(self):
        inactive = User.objects.create_user(
            email="inactive-status@example.com",
            password="TestPass123!",
            first_login=False,
            is_active=False,
        )

        inactive_response = self.post_status(inactive.id)
        missing_response = self.post_status(uuid.uuid4())

        assert inactive_response.status_code == 200
        assert inactive_response.json() == {
            "active": False,
            "code": "ACCOUNT_INACTIVE",
        }
        assert missing_response.status_code == 200
        assert missing_response.json() == {
            "active": False,
            "code": "ACCOUNT_INACTIVE",
        }

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_returns_must_change_password_status(self):
        user = User.objects.create_user(
            email="first-status@example.com",
            password="TestPass123!",
            first_login=True,
        )

        response = self.post_status(user.id)

        assert response.status_code == 200
        assert response.json() == {
            "active": False,
            "code": "MUST_CHANGE_PASSWORD",
        }


@pytest.mark.django_db
class TestInternalAccountLookupAPI:
    def post_lookup(self, email):
        body = json.dumps({"email": email}, separators=(",", ":")).encode("utf-8")
        return APIClient().generic(
            "POST",
            LOOKUP_ENDPOINT,
            body,
            content_type="application/json",
            secure=True,
            **signed_headers(body, path=LOOKUP_ENDPOINT),
        )

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_returns_identity_for_active_user_without_password(self):
        user = User.objects.create_user(
            email="lookup@example.com",
            password="TestPass123!",
            first_login=False,
            first_name="Lookup",
            last_name="User",
            employee_code="L001",
        )

        response = self.post_lookup("LOOKUP@example.com")

        assert response.status_code == 200
        assert response.json() == {
            "found": True,
            "user": {
                "external_user_id": str(user.id),
                "email": "lookup@example.com",
                "full_name": "Lookup User",
                "employee_code": "L001",
                "is_active": True,
                "must_change_password": False,
            },
        }

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_lookup_does_not_return_password_or_hash(self):
        User.objects.create_user(
            email="safe-lookup@example.com",
            password="SecretPass123!",
            first_login=False,
        )

        response = self.post_lookup("safe-lookup@example.com")

        assert response.status_code == 200
        response_text = json.dumps(response.json())
        assert "password_hash" not in response_text.lower()
        assert "pbkdf2" not in response_text.lower()
        assert "SecretPass123!" not in response_text

    @override_settings(
        INTERNAL_AUTH_ENABLED=True,
        INTERNAL_AUTH_SERVICE_SECRETS={SERVICE_ID: SERVICE_SECRET},
    )
    def test_lookup_missing_user_returns_generic_not_found(self):
        response = self.post_lookup("missing@example.com")

        assert response.status_code == 404
        assert response.json() == {"found": False, "code": "USER_NOT_FOUND"}
