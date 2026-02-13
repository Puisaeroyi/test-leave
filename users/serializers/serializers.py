"""
Serializers for User Authentication and Management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from organizations.models import Entity, Location, Department

from .utils import validate_active_relationship

User = get_user_model()

# Account lockout settings
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 3600  # 1 hour in seconds

GENERIC_LOGIN_ERROR = "Invalid credentials."


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

    approver = ApproverSerializer(read_only=True, allow_null=True)
    entity = EntitySerializer(read_only=True, allow_null=True)
    department = DepartmentSerializer(read_only=True, allow_null=True)

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
            'approver',  # New field for person-to-person approval
            'join_date',
            'avatar_url',
        ]
        read_only_fields = ['id', 'email', 'role', 'status', 'is_active', 'join_date', 'approver', 'employee_code']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'employee_code',
            'avatar_url',
            'approver',  # HR/Admin can assign approver
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

    def validate_approver(self, value):
        """Only HR/Admin can assign approver"""
        request = self.context.get('request')
        if request and request.user.role not in [User.Role.HR, User.Role.ADMIN]:
            raise serializers.ValidationError("Only HR/Admin can assign approver.")
        return value


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
    approver = serializers.UUIDField(required=True)
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

    def validate_approver(self, value):
        try:
            return User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Approver not found or inactive.")

    def validate(self, attrs):
        entity = attrs.get('entity')
        location = attrs.get('location')
        department = attrs.get('department')

        if location and entity and location.entity != entity:
            raise serializers.ValidationError({
                "location": "Selected location does not belong to the selected entity."
            })
        if department and entity and department.entity != entity:
            raise serializers.ValidationError({
                "department": "Selected department does not belong to the selected entity."
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
            approver=validated_data.get('approver'),
            join_date=validated_data.get('join_date') or date.today(),
            first_login=True,
        )
        return user
