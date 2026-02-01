"""User utility functions."""

import logging
from typing import Dict, Any

from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def build_user_response(user: User, include_tokens: bool = False) -> Dict[str, Any]:
    """Build standardized user response dict.

    Args:
        user: User instance
        include_tokens: Whether to include JWT tokens in response

    Returns:
        Dictionary with user data matching API response format
    """
    response = {
        'id': str(user.id),
        'email': user.email,
        'role': user.role,
        'status': user.status,
        'entity_id': str(user.entity.id) if user.entity else None,
        'entity_name': user.entity.entity_name if user.entity else None,
        'location_id': str(user.location.id) if user.location else None,
        'location_name': f"{user.location.location_name}, {user.location.city}" if user.location else None,
        'department_id': str(user.department.id) if user.department else None,
        'department_name': user.department.department_name if user.department else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }

    # Add optional fields for specific endpoints
    if hasattr(user, 'join_date') and user.join_date:
        response['join_date'] = user.join_date.isoformat()
    if hasattr(user, 'avatar_url') and user.avatar_url:
        response['avatar_url'] = user.avatar_url

    if include_tokens:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        response['tokens'] = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    return response
