"""
Organization models: Entity, Location, Department, DepartmentManager
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


class DepartmentManager(models.Model):
    """Junction table for manager-department-location assignments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    manager = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='managed_departments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'department_managers'
        unique_together = [['entity', 'department', 'location', 'manager'], ['department', 'location', 'manager']]
        verbose_name_plural = 'department managers'

    def __str__(self):
        entity_part = f" ({self.entity.code})" if self.entity else ""
        return f"{self.manager.email} - {self.department.department_name} @ {self.location.location_name}{entity_part}"

    def clean(self):
        """Validate entity consistency."""
        if self.entity and self.department and self.department.entity != self.entity:
            raise ValidationError({
                'department': ValidationError(
                    f"Department '{self.department.department_name}' belongs to entity "
                    f"'{self.department.entity.entity_name}', not '{self.entity.entity_name}'"
                )
            })
        if self.entity and self.location and self.location.entity != self.entity:
            raise ValidationError({
                'location': ValidationError(
                    f"Location '{self.location.location_name}' belongs to entity "
                    f"'{self.location.entity.entity_name}', not '{self.entity.entity_name}'"
                )
            })

    def save(self, *args, **kwargs):
        # Auto-set entity from department if not set
        if not self.entity and self.department:
            self.entity = self.department.entity
        # Validate using clean() for proper validation framework integration
        self.full_clean()
        super().save(*args, **kwargs)


class UnifiedImportPlaceholder(models.Model):
    """Placeholder model for unified organization import interface."""
    class Meta:
        managed = False  # No database table created
        verbose_name = "Organization Import"
        verbose_name_plural = "Organization Import"

    def __str__(self):
        return "Organization Import"
