"""
Leave management models: LeaveCategory, LeaveBalance, LeaveRequest, PublicHoliday, BusinessTrip
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings


class LeaveCategory(models.Model):
    """Leave category for reporting purposes (all draw from unified balance)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    requires_document = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_categories'
        ordering = ['sort_order']

    def __str__(self):
        return self.category_name


class LeaveBalance(models.Model):
    """Annual leave balance per user (96h default, unified pool)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balances')
    year = models.IntegerField()
    allocated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('96.00'))
    used_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    adjusted_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_balances'
        unique_together = ['user', 'year']

    def __str__(self):
        return f"{self.user.email} - {self.year}"

    @property
    def remaining_hours(self):
        """Calculate remaining hours (allocated + adjusted - used)"""
        return self.allocated_hours + self.adjusted_hours - self.used_hours


class LeaveRequest(models.Model):
    """Leave request with status tracking"""
    class ShiftType(models.TextChoices):
        FULL_DAY = 'FULL_DAY', 'Full Day'
        CUSTOM_HOURS = 'CUSTOM_HOURS', 'Custom Hours'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_category = models.ForeignKey(LeaveCategory, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=ShiftType.choices)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    attachment_url = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    approver_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_requests'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.start_date} to {self.end_date}"


class PublicHoliday(models.Model):
    """Public holidays scoped by entity/location (supports multi-day holidays)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(
        'organizations.Entity',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='public_holidays'
    )
    location = models.ForeignKey(
        'organizations.Location',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='public_holidays'
    )
    holiday_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    year = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'public_holidays'
        unique_together = ['entity', 'location', 'start_date']
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        if self.start_date == self.end_date:
            return f"{self.holiday_name} - {self.start_date}"
        return f"{self.holiday_name} - {self.start_date} to {self.end_date}"


class BusinessTrip(models.Model):
    """Business trip - separate from leave requests (no approval, no balance impact)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_trips')
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    note = models.TextField(blank=True)
    attachment_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_trips'
        indexes = [
            models.Index(fields=['user', 'start_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.city}, {self.country} ({self.start_date})"
