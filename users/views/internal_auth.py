"""Internal authentication endpoint for approved backend services."""

import hashlib
import logging

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from django.contrib.auth import get_user_model

from users.serializers.internal_auth import (
    InternalAccountLookupSerializer,
    InternalAccountStatusSerializer,
    InternalCredentialSerializer,
)
from users.services.credential_verification import (
    CredentialOutcome,
    normalize_login_email,
    verify_credentials,
)
from users.services.internal_service_auth import InternalServiceAuthentication


logger = logging.getLogger(__name__)


def audit_internal_auth(request, operation, outcome):
    logger.info(
        "internal_auth operation=%s service_id=%s outcome=%s request_id=%s",
        operation,
        request.auth or "unknown",
        outcome,
        request.headers.get("X-Request-Id", ""),
    )


class InternalAuthRateThrottle(SimpleRateThrottle):
    scope = "internal_auth"

    def get_cache_key(self, request, view):
        service_id = request.auth or "unknown"
        email = normalize_login_email(request.data.get("email", ""))
        email_digest = hashlib.sha256(email.encode("utf-8")).hexdigest()
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{service_id}:{email_digest}",
        }


class InternalCredentialVerifyView(GenericAPIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [AllowAny]
    serializer_class = InternalCredentialSerializer
    throttle_classes = [InternalAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification = verify_credentials(
            serializer.validated_data["email"],
            serializer.validated_data["password"],
        )
        audit_internal_auth(request, "verify", verification.outcome.value)

        if verification.outcome == CredentialOutcome.INVALID_CREDENTIALS:
            return Response(
                {"authenticated": False, "code": "INVALID_CREDENTIALS"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        blocked_statuses = {
            CredentialOutcome.ACCOUNT_LOCKED: "ACCOUNT_LOCKED",
            CredentialOutcome.ACCOUNT_INACTIVE: "ACCOUNT_INACTIVE",
            CredentialOutcome.MUST_CHANGE_PASSWORD: "MUST_CHANGE_PASSWORD",
        }
        if verification.outcome in blocked_statuses:
            return Response(
                {
                    "authenticated": False,
                    "code": blocked_statuses[verification.outcome],
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user = verification.user
        return Response({
            "authenticated": True,
            "user": {
                "external_user_id": str(user.id),
                "email": user.email,
                "full_name": user.get_full_name().strip() or user.email,
                "employee_code": user.employee_code,
            },
        })


class InternalStatusRateThrottle(SimpleRateThrottle):
    scope = "internal_status"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.auth or "unknown",
        }


class InternalAccountStatusView(GenericAPIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [AllowAny]
    serializer_class = InternalAccountStatusSerializer
    throttle_classes = [InternalStatusRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_model = get_user_model()
        user = user_model.objects.filter(
            id=serializer.validated_data["external_user_id"]
        ).first()

        if not user or not user.is_active or user.status != user_model.Status.ACTIVE:
            audit_internal_auth(request, "status", "ACCOUNT_INACTIVE")
            return Response({"active": False, "code": "ACCOUNT_INACTIVE"})
        if user.first_login:
            audit_internal_auth(request, "status", "MUST_CHANGE_PASSWORD")
            return Response({"active": False, "code": "MUST_CHANGE_PASSWORD"})
        audit_internal_auth(request, "status", "ACTIVE")
        return Response({
            "active": True,
            "external_user_id": str(user.id),
            "email": user.email,
        })


class InternalLookupRateThrottle(SimpleRateThrottle):
    scope = "internal_status"

    def get_cache_key(self, request, view):
        service_id = request.auth or "unknown"
        email = normalize_login_email(request.data.get("email", ""))
        email_digest = hashlib.sha256(email.encode("utf-8")).hexdigest()
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"lookup:{service_id}:{email_digest}",
        }


class InternalAccountLookupView(GenericAPIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [AllowAny]
    serializer_class = InternalAccountLookupSerializer
    throttle_classes = [InternalLookupRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_model = get_user_model()
        email = normalize_login_email(serializer.validated_data["email"])
        user = user_model.objects.filter(email__iexact=email).first()

        if not user:
            audit_internal_auth(request, "lookup", "USER_NOT_FOUND")
            return Response(
                {"found": False, "code": "USER_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_active = user.is_active and user.status == user_model.Status.ACTIVE
        audit_internal_auth(request, "lookup", "FOUND")
        return Response({
            "found": True,
            "user": {
                "external_user_id": str(user.id),
                "email": user.email,
                "full_name": user.get_full_name().strip() or user.email,
                "employee_code": user.employee_code,
                "is_active": is_active,
                "must_change_password": user.first_login,
            },
        })
