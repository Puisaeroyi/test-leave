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
        'employee_code': user.employee_code,
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

    # Add manager information (only for EMPLOYEES, not for MANAGERS/ADMIN/HR)
    from organizations.models import DepartmentManager
    if user.role == 'EMPLOYEE' and user.department and user.location:
        try:
            dept_manager = DepartmentManager.objects.filter(
                department=user.department,
                location=user.location,
                is_active=True
            ).select_related('manager').first()
            if dept_manager:
                response['manager'] = {
                    'id': str(dept_manager.manager.id),
                    'email': dept_manager.manager.email,
                    'first_name': dept_manager.manager.first_name,
                    'last_name': dept_manager.manager.last_name,
                    'full_name': f"{dept_manager.manager.first_name or ''} {dept_manager.manager.last_name or ''}".strip() or dept_manager.manager.email,
                }
        except Exception as e:
            logger.warning(f"Failed to fetch manager for user {user.email}: {e}")

    # Add managed departments information (for MANAGERS/ADMIN/HR)
    if user.role in ['MANAGER', 'ADMIN', 'HR']:
        try:
            managed_depts = DepartmentManager.objects.filter(
                manager=user,
                is_active=True
            ).select_related('department', 'location').order_by('department__department_name')
            if managed_depts.exists():
                response['managed_departments'] = [
                    {
                        'department': dm.department.department_name,
                        'location': f"{dm.location.location_name}, {dm.location.city}",
                        'department_id': str(dm.department.id),
                        'location_id': str(dm.location.id),
                    }
                    for dm in managed_depts
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch managed departments for user {user.email}: {e}")

    if include_tokens:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        response['tokens'] = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    return response
