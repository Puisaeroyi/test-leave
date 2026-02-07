"""
Serializers for User Authentication and Management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from organizations.models import Entity, Location, Department

from .utils import validate_active_relationship

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration with onboarding data"""
    email = serializers.EmailField(required=True)
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
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    employee_code = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=50)
    # Onboarding fields
    entity = serializers.UUIDField(required=True)
    location = serializers.UUIDField(required=True)
    department = serializers.UUIDField(required=True)

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_entity(self, value):
        """Validate entity exists and is active"""
        return validate_active_relationship(Entity, value, 'entity')

    def validate_location(self, value):
        """Validate location exists and is active"""
        return validate_active_relationship(Location, value, 'location')

    def validate_department(self, value):
        """Validate department exists and is active"""
        return validate_active_relationship(Department, value, 'department')

    def validate(self, attrs):
        """Validate passwords match and organization relationships"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })

        # Validate password using Django's password validators
        validate_password(attrs['password'])

        # Validate entity/location/department relationships
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
        """Create new user with onboarding data"""
        from datetime import date

        validated_data.pop('password_confirm')

        # Extract fields
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        employee_code = validated_data.pop('employee_code', None)
        entity = validated_data.pop('entity')
        location = validated_data.pop('location')
        department = validated_data.pop('department')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name,
            employee_code=employee_code,
            entity=entity,
            location=location,
            department=department,
            join_date=date.today(),
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate credentials"""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Try to authenticate user
            from django.contrib.auth import authenticate
            user = authenticate(username=email, password=password)

            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    "This user account has been disabled."
                )

            attrs['user'] = user
            return attrs

        raise serializers.ValidationError(
            "Must include email and password."
        )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password (first login or general)"""
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
        from users.resources import DEFAULT_IMPORT_PASSWORD

        user = User.objects.create_user(
            email=validated_data['email'],
            password=DEFAULT_IMPORT_PASSWORD,
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
