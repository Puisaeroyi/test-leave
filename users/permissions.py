"""
Custom permissions for User Management
"""
from rest_framework import permissions
from users.models import User


class IsHRAdmin(permissions.BasePermission):
    """
    Permission check for HR or Admin role
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in [User.Role.HR, User.Role.ADMIN]
        )


class IsManagerOrAbove(permissions.BasePermission):
    """
    Permission check for Manager, HR, or Admin role
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in [User.Role.MANAGER, User.Role.HR, User.Role.ADMIN]
        )


# Aliases for backward compatibility
IsHROrAdmin = IsHRAdmin
IsManagerOrHROrAdmin = IsManagerOrAbove


class IsOwnerOrHRAdmin(permissions.BasePermission):
    """
    Permission check: User can view/edit own profile, HR/Admin can view/edit all
    """
    def has_object_permission(self, request, view, obj):
        # Allow HR and Admin to access any user
        if request.user.role in [User.Role.HR, User.Role.ADMIN]:
            return True

        # Allow users to view/edit their own profile
        return obj == request.user


class IsSameEntityOrHRAdmin(permissions.BasePermission):
    """
    Permission check: Users can only see users in same entity, HR/Admin can see all
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        # Allow HR and Admin to access any user
        if request.user.role in [User.Role.HR, User.Role.ADMIN]:
            return True

        # Allow access to users in the same entity
        if request.user.entity and obj.entity:
            return request.user.entity == obj.entity

        return False
