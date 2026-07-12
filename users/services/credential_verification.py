"""Shared password verification and account-state decisions."""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache


MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 3600
_DUMMY_PASSWORD_HASH = make_password(secrets.token_urlsafe(32))


class CredentialOutcome(StrEnum):
    AUTHENTICATED = "AUTHENTICATED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    MUST_CHANGE_PASSWORD = "MUST_CHANGE_PASSWORD"


@dataclass(frozen=True)
class CredentialVerification:
    outcome: CredentialOutcome
    user: object | None = None


def normalize_login_email(email: str) -> str:
    
    user_model = get_user_model()
    return user_model.objects.normalize_email((email or "").strip()).lower()


def login_failure_cache_key(email: str) -> str:
    email_digest = hashlib.sha256(normalize_login_email(email).encode("utf-8")).hexdigest()
    return f"login_fail_{email_digest}"


def verify_credentials(email: str, password: str) -> CredentialVerification:
    """Verify a password once and return an HTTP-independent auth outcome."""
    user_model = get_user_model()
    normalized_email = normalize_login_email(email)
    cache_key = login_failure_cache_key(normalized_email)
    failure_count = cache.get(cache_key, 0)

    if failure_count >= MAX_LOGIN_ATTEMPTS:
        return CredentialVerification(CredentialOutcome.ACCOUNT_LOCKED)

    user = user_model.objects.filter(email__iexact=normalized_email).first()
    password_matches = (
        user.check_password(password)
        if user is not None
        else check_password(password, _DUMMY_PASSWORD_HASH)
    )

    if not password_matches:
        cache.set(cache_key, failure_count + 1, LOCKOUT_DURATION)
        return CredentialVerification(CredentialOutcome.INVALID_CREDENTIALS)

    cache.delete(cache_key)

    if not user.is_active or user.status != user_model.Status.ACTIVE:
        return CredentialVerification(CredentialOutcome.ACCOUNT_INACTIVE, user)

    if user.first_login:
        return CredentialVerification(CredentialOutcome.MUST_CHANGE_PASSWORD, user)

    return CredentialVerification(CredentialOutcome.AUTHENTICATED, user)
