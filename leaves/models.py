"""
Leave management models: LeaveCategory, LeaveBalance, LeaveRequest, PublicHoliday, BusinessTrip
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings


class LeaveCategory(models.Model):
    """Leave category for reporting and balance routing."""
    class BalanceBucket(models.TextChoices):
        VACATION = 'VACATION', 'Vacation'
        SICK = 'SICK', 'Sick'
        NONE = 'NONE', 'None'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    balance_bucket = models.CharField(
        max_length=20,
        choices=BalanceBucket.choices,
        default=BalanceBucket.NONE,
    )
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
    """Annual leave balance per user."""
    class BalanceType(models.TextChoices):
        VACATION = 'VACATION', 'Vacation'
        SICK = 'SICK', 'Sick Leave'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balances')
    year = models.IntegerField()
    balance_type = models.CharField(max_length=30, choices=BalanceType.choices, default=BalanceType.VACATION)
    allocated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    used_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    adjusted_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_balances'
        unique_together = ['user', 'year', 'balance_type']
        ordering = ['user', 'year', 'balance_type']

    def __str__(self):
        return f"{self.user.email} - {self.year} - {self.get_balance_type_display()}"

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

    class ApprovalStep(models.TextChoices):
        FIRST = 'FIRST', 'First Approver'
        FINAL = 'FINAL', 'Final Approver'
        COMPLETED = 'COMPLETED', 'Completed'

    class ApprovalDecision(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_category = models.ForeignKey(LeaveCategory, on_delete=models.SET_NULL, null=True, blank=True)
    balance_type_snapshot = models.CharField(
        max_length=20,
        choices=LeaveCategory.BalanceBucket.choices,
        null=True,
        blank=True,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=ShiftType.choices)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    start_day_offset = models.PositiveSmallIntegerField(default=0)
    end_day_offset = models.PositiveSmallIntegerField(default=0)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2)
    leave_breakdown = models.JSONField(blank=True, default=list)
    reason = models.TextField(blank=True)
    attachment_url = models.CharField(max_length=500, blank=True, null=True)
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
    first_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='first_step_leave_requests',
    )
    final_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_step_leave_requests',
    )
    current_approval_step = models.CharField(
        max_length=20,
        choices=ApprovalStep.choices,
        default=ApprovalStep.FIRST,
    )
    first_approval_status = models.CharField(
        max_length=20,
        choices=ApprovalDecision.choices,
        default=ApprovalDecision.PENDING,
    )
    first_approval_comment = models.TextField(blank=True)
    first_approval_at = models.DateTimeField(null=True, blank=True)
    final_approval_status = models.CharField(
        max_length=20,
        choices=ApprovalDecision.choices,
        default=ApprovalDecision.PENDING,
    )
    final_approval_comment = models.TextField(blank=True)
    final_approval_at = models.DateTimeField(null=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.balance_type_snapshot:
            self.balance_type_snapshot = (
                self.leave_category.balance_bucket
                if self.leave_category_id
                else LeaveCategory.BalanceBucket.NONE
            )
        super().save(*args, **kwargs)


class HolidayTemplate(models.Model):
    """Versioned source calendar used to generate company holiday drafts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country_code = models.CharField(max_length=2)
    year = models.IntegerField()
    name = models.CharField(max_length=120)
    source_name = models.CharField(max_length=200)
    source_url = models.URLField(max_length=500, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'holiday_templates'
        unique_together = ['country_code', 'year', 'version']
        ordering = ['country_code', 'year']

    def __str__(self):
        return self.name


class HolidayTemplateDate(models.Model):
    """One holiday date or date range in a source template."""
    class HolidayType(models.TextChoices):
        STATUTORY = 'STATUTORY', 'Statutory'
        OBSERVED = 'OBSERVED', 'Observed'
        COMPENSATORY = 'COMPENSATORY', 'Compensatory'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(HolidayTemplate, on_delete=models.CASCADE, related_name='dates')
    holiday_name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    holiday_type = models.CharField(
        max_length=20, choices=HolidayType.choices, default=HolidayType.STATUTORY
    )
    source_note = models.TextField(blank=True)

    class Meta:
        db_table = 'holiday_template_dates'
        unique_together = ['template', 'start_date', 'holiday_name']
        ordering = ['start_date']


class HolidayCalendar(models.Model):
    """Company-owned holiday calendar for an entity or location."""
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    country_code = models.CharField(max_length=2)
    year = models.IntegerField()
    entity = models.ForeignKey(
        'organizations.Entity', on_delete=models.CASCADE, related_name='holiday_calendars'
    )
    location = models.ForeignKey(
        'organizations.Location',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='holiday_calendars',
    )
    source_template = models.ForeignKey(
        HolidayTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='calendars'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_holiday_calendars',
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'holiday_calendars'
        unique_together = ['year', 'entity', 'location', 'country_code']
        ordering = ['-year', 'country_code', 'name']

    def __str__(self):
        return self.name


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
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    class HolidayType(models.TextChoices):
        STATUTORY = 'STATUTORY', 'Statutory'
        OBSERVED = 'OBSERVED', 'Observed'
        COMPENSATORY = 'COMPENSATORY', 'Compensatory'
        COMPANY = 'COMPANY', 'Company'

    calendar = models.ForeignKey(
        HolidayCalendar,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='holidays',
    )
    holiday_name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    year = models.IntegerField()
    holiday_type = models.CharField(
        max_length=20, choices=HolidayType.choices, default=HolidayType.STATUTORY
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PUBLISHED)
    source_note = models.TextField(blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_holidays',
    )
    published_at = models.DateTimeField(null=True, blank=True)
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
    attachment_url = models.CharField(max_length=500, blank=True, null=True)
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
