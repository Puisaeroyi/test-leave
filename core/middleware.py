"""
Custom middleware for the Leave Management System.
"""
import hashlib
import json
import uuid
from django.core.cache import cache
from django.http import JsonResponse


class IdempotencyMiddleware:
    """
    Middleware to prevent duplicate POST/PUT/PATCH requests using idempotency keys.

    Client sends X-Idempotency-Key header with a unique UUID.
    If the same key is seen again within the cache TTL, return the cached response.
    """

    CACHE_TTL = 300  # 5 minutes - enough for retries, not too long
    IDEMPOTENT_METHODS = ('POST', 'PUT', 'PATCH')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to mutating methods
        if request.method not in self.IDEMPOTENT_METHODS:
            return self.get_response(request)

        # Check for idempotency key header
        idempotency_key = request.headers.get('X-Idempotency-Key')
        if not idempotency_key:
            # No key provided - proceed normally (backward compatible)
            return self.get_response(request)

        # Build cache key: user_id + endpoint + idempotency_key
        user_id = getattr(request.user, 'id', 'anon') if hasattr(request, 'user') else 'anon'
        cache_key = f"idempotency:{user_id}:{request.path}:{idempotency_key}"

        # Check if we have a cached response
        cached = cache.get(cache_key)
        if cached is not None:
            # Return cached response with indicator header
            response = JsonResponse(
                cached['data'],
                status=cached['status'],
                safe=isinstance(cached['data'], dict)
            )
            response['X-Idempotency-Replayed'] = 'true'
            return response

        # Process the request
        response = self.get_response(request)

        # Cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            try:
                # Try to get JSON data from response
                if hasattr(response, 'data'):
                    data = response.data
                elif hasattr(response, 'content'):
                    data = json.loads(response.content.decode('utf-8'))
                else:
                    data = {}

                cache.set(cache_key, {
                    'data': data,
                    'status': response.status_code,
                }, self.CACHE_TTL)
            except (json.JSONDecodeError, AttributeError):
                # Non-JSON response, don't cache
                pass

        return response


class AuditLoggingMiddleware:
    """Record every successful authenticated mutation without storing request secrets."""

    MUTATING_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')
    ACTION_BY_METHOD = {
        'POST': 'CREATE',
        'PUT': 'UPDATE',
        'PATCH': 'UPDATE',
        'DELETE': 'DELETE',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method not in self.MUTATING_METHODS or not 200 <= response.status_code < 300:
            return response

        user = self._authenticated_user(request)
        if not user:
            return response

        from core.models import AuditLog

        AuditLog.objects.create(
            user=user,
            action=self._action(request),
            entity_type='APIRequest',
            entity_id=self._target_id(request, user.id),
            new_values={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
            },
            ip_address=self._client_ip(request),
        )
        return response

    @staticmethod
    def _authenticated_user(request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return user
        try:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            authenticated = JWTAuthentication().authenticate(request)
            return authenticated[0] if authenticated else None
        except Exception:
            return None

    def _action(self, request):
        path = request.path.lower()
        for marker, action in (
            ('/approve/', 'APPROVE'),
            ('/reject/', 'REJECT'),
            ('/publish/', 'PUBLISH'),
            ('/unpublish/', 'UNPUBLISH'),
            ('/generate/', 'GENERATE'),
        ):
            if marker in path:
                return action
        return self.ACTION_BY_METHOD[request.method]

    @staticmethod
    def _target_id(request, fallback):
        for part in reversed(request.path.strip('/').split('/')):
            try:
                return uuid.UUID(part)
            except (ValueError, TypeError):
                continue
        return fallback

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
