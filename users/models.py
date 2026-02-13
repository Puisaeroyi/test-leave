"""
Custom User model with email authentication and role-based access
"""
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """Custom manager for email-based User model"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password"""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        # Set username to email if not provided
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with email-based authentication"""

    class Role(models.TextChoices):
        EMPLOYEE = 'EMPLOYEE', 'Employee'
        MANAGER = 'MANAGER', 'Manager'
        HR = 'HR', 'HR'
        ADMIN = 'ADMIN', 'Admin'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_code = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Unique employee identifier")
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    entity = models.ForeignKey('organizations.Entity', on_delete=models.PROTECT, null=True, blank=True)
    location = models.ForeignKey('organizations.Location', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('organizations.Department', on_delete=models.SET_NULL, null=True, blank=True)
    # Approver field for person-to-person approval system (cross-entity supported)
    approver = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        help_text="Direct approver for leave requests. Cross-entity approval supported."
    )
    join_date = models.DateField(null=True, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    first_login = models.BooleanField(
        default=True,
        help_text="Flag to force password change on first login"
    )

    # Use custom manager for email-based authentication
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is USERNAME_FIELD, so not needed here

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    def clean(self):
        """Validate user fields according to Django best practices."""
        super().clean()

        # Validate entity and location match
        if self.entity and self.location:
            if self.location.entity != self.entity:
                raise ValidationError({
                    'location': ValidationError(
                        f"Location '{self.location.location_name}' belongs to entity "
                        f"'{self.location.entity.entity_name}', not '{self.entity.entity_name}'. "
                        f"Please select a location within {self.entity.entity_name}."
                    )
                })

        # Validate entity and department match
        if self.entity and self.department:
            if self.department.entity != self.entity:
                raise ValidationError({
                    'department': ValidationError(
                        f"Department '{self.department.department_name}' belongs to entity "
                        f"'{self.department.entity.entity_name}', not '{self.entity.entity_name}'. "
                        f"Please select a department within {self.entity.entity_name}."
                    )
                })

        # Validate approver is not self (circular reference prevention)
        if self.approver and self.approver == self:
            raise ValidationError({
                'approver': ValidationError(
                    "A user cannot be their own approver. "
                    "Please select a different approver or leave the field blank."
                )
            })

    def save(self, *args, **kwargs):
        # Set username to email if not set
        if not self.username:
            self.username = self.email
        elif self.username != self.email:
            self.username = self.email

        # Call full_clean() to trigger clean() validation
        # This maintains backwards compatibility while using Django's proper validation
        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def has_completed_onboarding(self):
        """Check if user has completed onboarding (has entity, location, department)"""
        return bool(self.entity and self.location and self.department)
