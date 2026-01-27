"""
Core models: Notification, AuditLog
"""
import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """In-app notification for users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50)  # e.g., 'LEAVE_APPROVED', 'LEAVE_PENDING', 'LEAVE_REJECTED'
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(max_length=500, blank=True)
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


class AuditLog(models.Model):
    """Audit log for tracking all actions in the system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50)  # e.g., 'CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT'
    entity_type = models.CharField(max_length=50)  # e.g., 'LeaveRequest', 'User', 'LeaveBalance'
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
