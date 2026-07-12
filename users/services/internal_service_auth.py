"""HMAC authentication for trusted internal backend callers."""

import hashlib
import hmac
import time

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed, NotFound


AUTHENTICATION_ERROR = "Invalid service authentication."
MIN_SERVICE_SECRET_LENGTH = 32


class RequestBodyTooLarge(APIException):
    status_code = 413
    default_detail = "Request body is too large."
    default_code = "request_body_too_large"


def configured_secrets(secret_config):
    if isinstance(secret_config, str):
        return [secret_config]
    if isinstance(secret_config, (list, tuple)):
        return [secret for secret in secret_config if isinstance(secret, str) and secret]
    return []


def validate_service_secret_config(service_secrets):
    if not isinstance(service_secrets, dict) or not service_secrets:
        raise ImproperlyConfigured(
            "INTERNAL_AUTH_SERVICE_SECRETS must be a non-empty JSON object."
        )
    for service_id, secret_config in service_secrets.items():
        if not isinstance(service_id, str) or not service_id.strip():
            raise ImproperlyConfigured(
                "INTERNAL_AUTH_SERVICE_SECRETS contains an invalid service id."
            )
        secrets = configured_secrets(secret_config)
        if not secrets:
            raise ImproperlyConfigured(
                f"INTERNAL_AUTH_SERVICE_SECRETS for {service_id} must not be empty."
            )
        for secret in secrets:
            if len(secret) < MIN_SERVICE_SECRET_LENGTH:
                raise ImproperlyConfigured(
                    f"INTERNAL_AUTH_SERVICE_SECRETS for {service_id} must be at least "
                    f"{MIN_SERVICE_SECRET_LENGTH} characters."
                )


class InternalServiceAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if not getattr(settings, "INTERNAL_AUTH_ENABLED", False):
            raise NotFound()

        service_id = request.headers.get("X-Service-Id", "")
        timestamp = request.headers.get("X-Timestamp", "")
        nonce = request.headers.get("X-Nonce", "")
        supplied_signature = request.headers.get("X-Signature", "")
        service_secrets = getattr(settings, "INTERNAL_AUTH_SERVICE_SECRETS", {})
        validate_service_secret_config(service_secrets)
        secrets = configured_secrets(service_secrets.get(service_id))

        if not all([service_id, timestamp, nonce, supplied_signature, secrets]):
            raise AuthenticationFailed(AUTHENTICATION_ERROR)

        try:
            timestamp_value = int(timestamp)
        except (TypeError, ValueError) as exc:
            raise AuthenticationFailed(AUTHENTICATION_ERROR) from exc

        allowed_skew = getattr(settings, "INTERNAL_AUTH_TIMESTAMP_SKEW_SECONDS", 300)
        if abs(int(time.time()) - timestamp_value) > allowed_skew:
            raise AuthenticationFailed(AUTHENTICATION_ERROR)

        max_body_bytes = getattr(settings, "INTERNAL_AUTH_MAX_BODY_BYTES", 4096)
        if len(request.body) > max_body_bytes:
            raise RequestBodyTooLarge()

        body_digest = hashlib.sha256(request.body).hexdigest()
        canonical_request = "\n".join([
            request.method.upper(),
            request.path,
            timestamp,
            nonce,
            body_digest,
        ])
        signature_is_valid = any(
            hmac.compare_digest(
                hmac.new(
                    secret.encode("utf-8"),
                    canonical_request.encode("utf-8"),
                    hashlib.sha256,
                ).hexdigest(),
                supplied_signature,
            )
            for secret in secrets
        )
        if not signature_is_valid:
            raise AuthenticationFailed(AUTHENTICATION_ERROR)

        nonce_key = f"internal_auth_nonce:{service_id}:{nonce}"
        if not cache.add(nonce_key, True, timeout=allowed_skew * 2):
            raise AuthenticationFailed(AUTHENTICATION_ERROR)

        return AnonymousUser(), service_id

    def authenticate_header(self, request):
        return "HMAC"
