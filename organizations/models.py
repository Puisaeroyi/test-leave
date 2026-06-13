"""
Organization models: Entity, Location, Department
"""
import uuid
from django.db import models
from django.core.exceptions import ValidationError

from .constants import TIMEZONE_CHOICES


class Entity(models.Model):
    """Company or subsidiary entity"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'entities'
        verbose_name_plural = 'entities'

    def __str__(self):
        return self.entity_name


class Location(models.Model):
    """Physical office location"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='locations')
    location_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'locations'
        unique_together = ['entity', 'location_name']

    def __str__(self):
        return f"{self.location_name} - {self.city}"


class Department(models.Model):
    """Organizational department - can belong to a specific location or entity-wide"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='departments')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='departments', null=True, blank=True)
    department_name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    holiday_requires_leave = models.BooleanField(
        default=False,
        help_text="Employees must submit leave requests for published holidays.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        # Department code is unique per entity+location combination
        # For entity-wide departments (location=null), entity+code must be unique
        unique_together = [['entity', 'location', 'code']]

    def __str__(self):
        if self.location:
            return f"{self.department_name} ({self.code}) @ {self.location.location_name}"
        return f"{self.department_name} ({self.code})"


class WorkShift(models.Model):
    """Named working shift assigned to employees in a department."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='work_shifts')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    includes_weekends = models.BooleanField(
        default=False,
        help_text="All 7 days count as deductible working days for this shift.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'work_shifts'
        unique_together = ['department', 'name']
        ordering = ['department', 'start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time:%H:%M}-{self.end_time:%H:%M})"


class UnifiedImportPlaceholder(models.Model):
    """Placeholder model for unified organization import interface."""
    class Meta:
        managed = False  # No database table created
        verbose_name = "Organization Import"
        verbose_name_plural = "Organization Import"

    def __str__(self):
        return "Organization Import"
