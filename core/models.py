"""
Core models: Notification, AuditLog
"""
import uuid
from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    """Notification type choices"""
    LEAVE_APPROVED = 'LEAVE_APPROVED', 'Leave Approved'
    LEAVE_PENDING = 'LEAVE_PENDING', 'Leave Pending'
    LEAVE_REJECTED = 'LEAVE_REJECTED', 'Leave Rejected'
    LEAVE_CANCELLED = 'LEAVE_CANCELLED', 'Leave Cancelled'
    LEAVE_UPDATED = 'LEAVE_UPDATED', 'Leave Updated'
    BALANCE_LOW = 'BALANCE_LOW', 'Balance Low'
    LEAVE_HOURS_RECALCULATED = 'LEAVE_HOURS_RECALCULATED', 'Leave Hours Recalculated'
    HOLIDAY_CALENDAR_UPDATED = 'HOLIDAY_CALENDAR_UPDATED', 'Holiday Calendar Updated'


class Notification(models.Model):
    """In-app notification for users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=NotificationType.choices)  # e.g., 'LEAVE_APPROVED', 'LEAVE_PENDING', 'LEAVE_REJECTED'
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(max_length=500, blank=True)
    related_object_id = models.UUIDField(null=True, blank=True)  # ID of related object (e.g., leave_request.id)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class Announcement(models.Model):
    """Admin-authored announcement article shown to users after login."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    body = models.TextField()
    body_html = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_announcements',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'announcements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['starts_at', 'expires_at']),
        ]

    def __str__(self):
        return self.title


class AuditAction(models.TextChoices):
    """Audit log action choices"""
    CREATE = 'CREATE', 'Create'
    UPDATE = 'UPDATE', 'Update'
    DELETE = 'DELETE', 'Delete'
    APPROVE = 'APPROVE', 'Approve'
    REJECT = 'REJECT', 'Reject'
    GENERATE = 'GENERATE', 'Generate'
    PUBLISH = 'PUBLISH', 'Publish'
    UNPUBLISH = 'UNPUBLISH', 'Unpublish'
    SPLIT_SCOPE = 'SPLIT_SCOPE', 'Split Scope'


class AuditEntityType(models.TextChoices):
    """Audit log entity type choices"""
    LEAVE_REQUEST = 'LeaveRequest', 'Leave Request'
    BUSINESS_TRIP = 'BusinessTrip', 'Business Trip'
    USER = 'User', 'User'
    LEAVE_BALANCE = 'LeaveBalance', 'Leave Balance'
    ENTITY = 'Entity', 'Entity'
    LOCATION = 'Location', 'Location'
    DEPARTMENT = 'Department', 'Department'
    HOLIDAY_CALENDAR = 'HolidayCalendar', 'Holiday Calendar'
    PUBLIC_HOLIDAY = 'PublicHoliday', 'Public Holiday'
    API_REQUEST = 'APIRequest', 'API Request'


class AuditLog(models.Model):
    """Audit log for tracking all actions in the system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=50, choices=AuditAction.choices)  # e.g., 'CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT'
    entity_type = models.CharField(max_length=50, choices=AuditEntityType.choices)  # e.g., 'LeaveRequest', 'User', 'LeaveBalance'
    entity_id = models.UUIDField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.action} {self.entity_type}"
