"""
Serializers for User Authentication and Management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from organizations.models import Entity, Location, Department, WorkShift

from .utils import validate_active_relationship

User = get_user_model()

# Account lockout settings
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 3600  # 1 hour in seconds

GENERIC_LOGIN_ERROR = "Invalid credentials."


def validate_avatar_url_value(value):
    if not value or value.startswith('/media/'):
        return value
    validator = URLValidator(schemes=['http', 'https'])
    try:
        validator(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(
            "Avatar must be an http(s) URL or a relative /media/ path."
        ) from exc
    return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate credentials with account lockout protection."""
        email = attrs.get('email')
        password = attrs.get('password')

        if not (email and password):
            raise serializers.ValidationError(GENERIC_LOGIN_ERROR)

        # Check if account is locked out
        cache_key = f"login_fail_{email.lower()}"
        fail_count = cache.get(cache_key, 0)

        if fail_count >= MAX_LOGIN_ATTEMPTS:
            raise serializers.ValidationError(
                "Account temporarily locked due to too many failed attempts. Try again later."
            )

        # Try to authenticate user
        from django.contrib.auth import authenticate
        user = authenticate(username=email, password=password)

        if not user or not user.is_active:
            # Increment failed attempts
            cache.set(cache_key, fail_count + 1, LOCKOUT_DURATION)
            raise serializers.ValidationError(GENERIC_LOGIN_ERROR)

        # Reset failed attempts on success
        cache.delete(cache_key)

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password on first login."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })
        validate_password(attrs['password'])
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class ApproverSerializer(serializers.Serializer):
        """Nested serializer for approver field"""
        id = serializers.UUIDField()
        email = serializers.EmailField()
        first_name = serializers.CharField(allow_blank=True)
        last_name = serializers.CharField(allow_blank=True)

    class EntitySerializer(serializers.Serializer):
        """Nested serializer for entity field"""
        id = serializers.UUIDField()
        entity_name = serializers.CharField()

    class DepartmentSerializer(serializers.Serializer):
        """Nested serializer for department field"""
        id = serializers.UUIDField()
        department_name = serializers.CharField()

    class WorkShiftSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        name = serializers.CharField()
        pattern_type = serializers.CharField()
        start_time = serializers.TimeField(format='%H:%M')
        end_time = serializers.TimeField(format='%H:%M')
        break_start_time = serializers.TimeField(format='%H:%M', allow_null=True)
        break_end_time = serializers.TimeField(format='%H:%M', allow_null=True)
        includes_weekends = serializers.BooleanField()
        cycle_days = serializers.JSONField()

    approver = ApproverSerializer(source='approver_1', read_only=True, allow_null=True)
    final_approver = ApproverSerializer(source='approver_2', read_only=True, allow_null=True)
    entity = EntitySerializer(read_only=True, allow_null=True)
    department = DepartmentSerializer(read_only=True, allow_null=True)
    work_shift = WorkShiftSerializer(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'employee_code',
            'email',
            'first_name',
            'last_name',
            'role',
            'status',
            'is_active',
            'entity',
            'location',
            'department',
            'work_shift',
            'shift_cycle_start_date',
            'approver',  # First approval step
            'final_approver',  # Optional final approval step
            'join_date',
            'avatar_url',
        ]
        read_only_fields = [
            'id', 'email', 'role', 'status', 'is_active', 'join_date',
            'approver', 'final_approver', 'employee_code'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    approver = serializers.PrimaryKeyRelatedField(
        source='approver_1',
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    final_approver = serializers.PrimaryKeyRelatedField(
        source='approver_2',
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    work_shift = serializers.PrimaryKeyRelatedField(
        queryset=WorkShift.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    shift_cycle_start_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'employee_code',
            'avatar_url',
            'work_shift',
            'shift_cycle_start_date',
            'approver',  # HR/Admin can assign first approver
            'final_approver',  # HR/Admin can assign second approver
        ]

    def validate_email(self, value):
        """Validate email is unique"""
        # Exclude current user from uniqueness check
        instance = self.instance
        if instance:
            if User.objects.filter(email=value).exclude(id=instance.id).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        else:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_avatar_url(self, value):
        return validate_avatar_url_value(value)

    def validate_approver(self, value):
        """Only HR/Admin can assign first approver"""
        request = self.context.get('request')
        if request and request.user.role not in [User.Role.HR, User.Role.ADMIN]:
            raise serializers.ValidationError("Only HR/Admin can assign first approver.")
        return value

    def validate_final_approver(self, value):
        """Only HR/Admin can assign second approver"""
        request = self.context.get('request')
        if request and request.user.role not in [User.Role.HR, User.Role.ADMIN]:
            raise serializers.ValidationError("Only HR/Admin can assign second approver.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if (
            request
            and self.instance
            and request.user.role == User.Role.HR
            and request.user.id == self.instance.id
        ):
            approver_changes = {}
            if (
                'approver_1' in attrs
                and attrs['approver_1'] != self.instance.approver_1
            ):
                approver_changes['approver'] = (
                    "HR users cannot change their own first approver."
                )
            if (
                'approver_2' in attrs
                and attrs['approver_2'] != self.instance.approver_2
            ):
                approver_changes['final_approver'] = (
                    "HR users cannot change their own second approver."
                )
            if approver_changes:
                raise serializers.ValidationError(approver_changes)

        approver = attrs.get('approver_1', getattr(self.instance, 'approver_1', None))
        final_approver = attrs.get('approver_2', getattr(self.instance, 'approver_2', None))
        work_shift = attrs.get('work_shift', getattr(self.instance, 'work_shift', None))
        if self.instance and approver and approver.id == self.instance.id:
            raise serializers.ValidationError({'approver': "A user cannot be their own first approver."})
        if self.instance and final_approver and final_approver.id == self.instance.id:
            raise serializers.ValidationError({'final_approver': "A user cannot be their own second approver."})
        if approver and final_approver and approver.id == final_approver.id:
            raise serializers.ValidationError({
                'final_approver': "Second approver must be different from first approver."
            })
        if work_shift and self.instance.department_id and work_shift.department_id != self.instance.department_id:
            raise serializers.ValidationError({'work_shift': "Selected shift does not belong to department."})
        shift_cycle_start_date = attrs.get(
            'shift_cycle_start_date',
            getattr(self.instance, 'shift_cycle_start_date', None),
        )
        if work_shift and work_shift.pattern_type == WorkShift.PatternType.ROTATING_CYCLE and not shift_cycle_start_date:
            raise serializers.ValidationError({'shift_cycle_start_date': 'Cycle start date is required for rotating shifts.'})
        return attrs

    def to_representation(self, instance):
        return UserSerializer(instance, context=self.context).data


class UserCreateSerializer(serializers.Serializer):
    """Serializer for HR/Admin user creation. Auto-sets password to DEFAULT_IMPORT_PASSWORD."""

    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    employee_code = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    role = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.EMPLOYEE)
    entity = serializers.UUIDField(required=True)
    location = serializers.UUIDField(required=True)
    department = serializers.UUIDField(required=True)
    work_shift = serializers.UUIDField(required=False, allow_null=True)
    shift_cycle_start_date = serializers.DateField(required=False, allow_null=True)
    approver = serializers.UUIDField(required=True)
    final_approver = serializers.UUIDField(required=False, allow_null=True)
    join_date = serializers.DateField(required=False, allow_null=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_entity(self, value):
        return validate_active_relationship(Entity, value, 'entity')

    def validate_location(self, value):
        return validate_active_relationship(Location, value, 'location')

    def validate_department(self, value):
        return validate_active_relationship(Department, value, 'department')

    def validate_work_shift(self, value):
        if not value:
            return None
        try:
            return WorkShift.objects.get(id=value, is_active=True)
        except WorkShift.DoesNotExist:
            raise serializers.ValidationError("Work shift not found or inactive.")

    def validate_approver(self, value):
        try:
            return User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("First approver not found or inactive.")

    def validate_final_approver(self, value):
        if not value:
            return None
        try:
            return User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Second approver not found or inactive.")

    def validate(self, attrs):
        entity = attrs.get('entity')
        location = attrs.get('location')
        department = attrs.get('department')
        work_shift = attrs.get('work_shift')
        shift_cycle_start_date = attrs.get('shift_cycle_start_date')

        if location and entity and location.entity != entity:
            raise serializers.ValidationError({
                "location": "Selected location does not belong to the selected entity."
            })
        if department and entity and department.entity != entity:
            raise serializers.ValidationError({
                "department": "Selected department does not belong to the selected entity."
            })
        if work_shift and department and work_shift.department_id != department.id:
            raise serializers.ValidationError({"work_shift": "Selected shift does not belong to department."})
        if work_shift and work_shift.pattern_type == WorkShift.PatternType.ROTATING_CYCLE and not shift_cycle_start_date:
            raise serializers.ValidationError({"shift_cycle_start_date": "Cycle start date is required for rotating shifts."})
        approver = attrs.get('approver')
        final_approver = attrs.get('final_approver')
        if approver and final_approver and approver.id == final_approver.id:
            raise serializers.ValidationError({
                "final_approver": "Second approver must be different from first approver."
            })
        return attrs

    def create(self, validated_data):
        from datetime import date
        from users.resources import get_default_import_password

        user = User.objects.create_user(
            email=validated_data['email'],
            password=get_default_import_password(),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            employee_code=validated_data.get('employee_code') or None,
            role=validated_data.get('role', User.Role.EMPLOYEE),
            entity=validated_data['entity'],
            location=validated_data['location'],
            department=validated_data['department'],
            work_shift=validated_data.get('work_shift'),
            shift_cycle_start_date=validated_data.get('shift_cycle_start_date'),
            approver_1=validated_data.get('approver'),
            approver_2=validated_data.get('final_approver'),
            join_date=validated_data.get('join_date') or date.today(),
            first_login=True,
        )
        return user
