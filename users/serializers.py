"""
Serializers for User Authentication and Management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from organizations.models import Entity, Location, Department

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration"""
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

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })

        # Validate password using Django's password validators
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')

        # Extract optional fields
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name,
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


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'status',
            'entity',
            'location',
            'department',
            'join_date',
            'avatar_url',
        ]
        read_only_fields = ['id', 'email', 'role', 'status', 'join_date']


class OnboardingSerializer(serializers.Serializer):
    """Serializer for user onboarding"""
    entity = serializers.UUIDField(required=True)
    location = serializers.UUIDField(required=True)
    department = serializers.UUIDField(required=True)

    def validate_entity(self, value):
        """Validate entity exists and is active"""
        try:
            entity = Entity.objects.get(id=value, is_active=True)
            return entity
        except Entity.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive entity selected.")

    def validate_location(self, value):
        """Validate location exists and is active"""
        try:
            location = Location.objects.get(id=value, is_active=True)
            return location
        except Location.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive location selected.")

    def validate_department(self, value):
        """Validate department exists and is active"""
        try:
            department = Department.objects.get(id=value, is_active=True)
            return department
        except Department.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive department selected.")

    def validate(self, attrs):
        """Validate relationships between entity, location, and department"""
        entity = attrs.get('entity')
        location = attrs.get('location')
        department = attrs.get('department')

        # Check if location belongs to entity
        if location.entity != entity:
            raise serializers.ValidationError({
                "location": "Selected location does not belong to the selected entity."
            })

        # Check if department belongs to entity
        if department.entity != entity:
            raise serializers.ValidationError({
                "department": "Selected department does not belong to the selected entity."
            })

        return attrs

    def update(self, instance, validated_data):
        """Update user with onboarding data"""
        instance.entity = validated_data['entity']
        instance.location = validated_data['location']
        instance.department = validated_data['department']

        # Set join date if not already set
        if not instance.join_date:
            from datetime import date
            instance.join_date = date.today()

        instance.save()
        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'avatar_url',
            'status',
        ]

    def validate_status(self, value):
        """Only admins can change status"""
        request = self.context.get('request')
        if request and not request.user.role == User.Role.ADMIN:
            raise serializers.ValidationError("Only admins can change user status.")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user list"""
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'status', 'department', 'department_name']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single user"""
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    entity_name = serializers.CharField(source='entity.name', read_only=True, allow_null=True)
    location_name = serializers.CharField(source='location.name', read_only=True, allow_null=True)
    has_completed_onboarding = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role', 'status',
            'department', 'department_name', 'entity', 'entity_name',
            'location', 'location_name', 'join_date', 'avatar_url',
            'has_completed_onboarding'
        ]
