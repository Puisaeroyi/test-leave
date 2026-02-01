"""
Organization models: Entity, Location, Department, DepartmentManager
"""
import uuid
from django.db import models


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

    # Timezone choices for America and Asia
    TIMEZONE_CHOICES = [
        # America
        ('America/New_York', 'America/New_York (EST/EDT)'),
        ('America/Chicago', 'America/Chicago (CST/CDT)'),
        ('America/Denver', 'America/Denver (MST/MDT)'),
        ('America/Los_Angeles', 'America/Los_Angeles (PST/PDT)'),
        ('America/Phoenix', 'America/Phoenix (MST)'),
        ('America/Toronto', 'America/Toronto (EST/EDT)'),
        ('America/Vancouver', 'America/Vancouver (PST/PDT)'),
        ('America/Mexico_City', 'America/Mexico_City (CST/CDT)'),
        ('America/Bogota', 'America/Bogota (COT)'),
        ('America/Lima', 'America/Lima (PET)'),
        ('America/Santiago', 'America/Santiago (CLT/CLST)'),
        ('America/Sao_Paulo', 'America/Sao_Paulo (BRT/BRST)'),
        ('America/Buenos_Aires', 'America/Buenos_Aires (ART)'),
        # Asia
        ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh (GMT+7)'),
        ('Asia/Bangkok', 'Asia/Bangkok (GMT+7)'),
        ('Asia/Jakarta', 'Asia/Jakarta (WIB)'),
        ('Asia/Singapore', 'Asia/Singapore (GMT+8)'),
        ('Asia/Hong_Kong', 'Asia/Hong_Kong (HKT)'),
        ('Asia/Shanghai', 'Asia/Shanghai (CST)'),
        ('Asia/Tokyo', 'Asia/Tokyo (JST)'),
        ('Asia/Seoul', 'Asia/Seoul (KST)'),
        ('Asia/Manila', 'Asia/Manila (PST)'),
        ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur (MYT)'),
        ('Asia/Taipei', 'Asia/Taipei (NST)'),
        ('Asia/Dubai', 'Asia/Dubai (GST)'),
        ('Asia/Riyadh', 'Asia/Riyadh (AST)'),
        ('Asia/Qatar', 'Asia/Qatar (AST)'),
        ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
        ('Asia/Mumbai', 'Asia/Mumbai (IST)'),
        ('Asia/Karachi', 'Asia/Karachi (PKT)'),
        ('Asia/Dhaka', 'Asia/Dhaka (BST)'),
        ('Asia/Colombo', 'Asia/Colombo (IST)'),
        ('Asia/Yangon', 'Asia/Yangon (MMT)'),
        # Common UTC
        ('UTC', 'UTC'),
    ]
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

    def save(self, *args, **kwargs):
        # Validate entity consistency
        if self.entity and self.department and self.department.entity != self.entity:
            raise ValueError(
                f"Department '{self.department.department_name}' belongs to entity "
                f"'{self.department.entity.entity_name}', not '{self.entity.entity_name}'"
            )
        if self.entity and self.location and self.location.entity != self.entity:
            raise ValueError(
                f"Location '{self.location.location_name}' belongs to entity "
                f"'{self.location.entity.entity_name}', not '{self.entity.entity_name}'"
            )
        # Auto-set entity from department if not set
        if not self.entity and self.department:
            self.entity = self.department.entity
        super().save(*args, **kwargs)


class UnifiedImportPlaceholder(models.Model):
    """Placeholder model for unified organization import interface."""
    class Meta:
        managed = False  # No database table created
        verbose_name = "Organization Import"
        verbose_name_plural = "Organization Import"

    def __str__(self):
        return "Organization Import"
