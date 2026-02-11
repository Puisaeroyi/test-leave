"""
Custom middleware for the Leave Management System.
"""
import hashlib
import json
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
