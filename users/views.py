"""
User & Authentication API Views
"""
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()


class IsHROrAdmin(BasePermission):
    """Permission class for HR and Admin roles"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['HR', 'ADMIN']


class IsManagerOrHROrAdmin(BasePermission):
    """Permission class for Manager, HR and Admin roles"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['MANAGER', 'HR', 'ADMIN']


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    POST /api/v1/auth/register/
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        from users.serializers import RegisterSerializer
        from rest_framework_simplejwt.tokens import RefreshToken

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'role': user.role,
                'status': user.status,
                'entity': str(user.entity.id) if user.entity else None,
                'location': str(user.location.id) if user.location else None,
                'department': str(user.department.id) if user.department else None,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    User login endpoint
    POST /api/v1/auth/login/
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        from users.serializers import LoginSerializer
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import login

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Update last login
        login(request, user)

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'role': user.role,
                'status': user.status,
                'entity': str(user.entity.id) if user.entity else None,
                'location': str(user.location.id) if user.location else None,
                'department': str(user.department.id) if user.department else None,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """
    User logout endpoint (blacklist refresh token)
    POST /api/v1/auth/logout/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Invalid token or already logged out'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserMeView(generics.RetrieveAPIView):
    """
    Get current user info
    GET /api/v1/auth/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({
            'id': str(user.id),
            'email': user.email,
            'role': user.role,
            'status': user.status,
            'entity': str(user.entity.id) if user.entity else None,
            'entity_name': user.entity.name if user.entity else None,
            'location': str(user.location.id) if user.location else None,
            'location_name': f"{user.location.name}, {user.location.city}" if user.location else None,
            'department': str(user.department.id) if user.department else None,
            'department_name': user.department.name if user.department else None,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'join_date': user.join_date.isoformat() if user.join_date else None,
            'avatar_url': user.avatar_url,
        })


class OnboardingView(generics.GenericAPIView):
    """
    Complete user onboarding
    POST /api/v1/auth/onboarding/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from users.serializers import OnboardingSerializer
        from leaves.models import LeaveBalance
        from datetime import date

        user = request.user

        # Check if onboarding already completed
        if user.has_completed_onboarding:
            return Response({
                'message': 'Onboarding already completed',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'role': user.role,
                    'status': user.status,
                    'entity': str(user.entity.id) if user.entity else None,
                    'entity_name': user.entity.name if user.entity else None,
                    'location': str(user.location.id) if user.location else None,
                    'location_name': f"{user.location.name}, {user.location.city}" if user.location else None,
                    'department': str(user.department.id) if user.department else None,
                    'department_name': user.department.name if user.department else None,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }, status=status.HTTP_200_OK)

        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)

        # Create initial leave balance (default 21 days = 168 hours)
        LeaveBalance.objects.get_or_create(
            user=user,
            year=date.today().year,
            defaults={
                'allocated_hours': 168,
                'used_hours': 0,
                'adjusted_hours': 0,
            }
        )

        # Refresh user from DB to get related objects
        user.refresh_from_db()

        return Response({
            'message': 'Onboarding completed successfully',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'role': user.role,
                'status': user.status,
                'entity': str(user.entity.id) if user.entity else None,
                'entity_name': user.entity.name if user.entity else None,
                'location': str(user.location.id) if user.location else None,
                'location_name': f"{user.location.name}, {user.location.city}" if user.location else None,
                'department': str(user.department.id) if user.department else None,
                'department_name': user.department.name if user.department else None,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """List all users with filters (HR/Admin only)"""
    permission_classes = [IsHROrAdmin]

    def get(self, request, *args, **kwargs):
        from users.serializers import UserListSerializer

        queryset = User.objects.all()

        # Filters
        role = request.query_params.get('role')
        department_id = request.query_params.get('department_id')
        status_param = request.query_params.get('status')

        if role:
            queryset = queryset.filter(role=role)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if status_param:
            queryset = queryset.filter(status=status_param)

        serializer = UserListSerializer(queryset, many=True)
        return Response(serializer.data)


class UserDetailView(generics.RetrieveAPIView):
    """Get user details (HR/Admin only)"""
    permission_classes = [IsHROrAdmin]

    def get(self, request, *args, **kwargs):
        from users.serializers import UserDetailSerializer

        user_id = kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsHROrAdmin])
def setup_user(request, user_id):
    """
    POST /api/v1/users/{id}/setup/
    Setup user: assign department, role, join_date, and create initial leave balance
    """
    from leaves.models import LeaveBalance
    from users.serializers import UserDetailSerializer

    user = get_object_or_404(User, id=user_id)

    # Update user fields
    user.department_id = request.data.get('department_id')
    user.role = request.data.get('role', 'EMPLOYEE')
    user.join_date = request.data.get('join_date')
    user.save()

    # Create or update leave balance
    year = timezone.now().year
    allocated = Decimal(str(request.data.get('allocated_hours', 96)))

    balance, created = LeaveBalance.objects.update_or_create(
        user=user,
        year=year,
        defaults={'allocated_hours': allocated}
    )

    serializer = UserDetailSerializer(user)
    return Response({
        'user': serializer.data,
        'balance': {
            'year': balance.year,
            'allocated_hours': float(balance.allocated_hours),
            'remaining_hours': float(balance.remaining_hours),
        }
    })


@api_view(['POST'])
@permission_classes([IsHROrAdmin])
def adjust_balance(request, user_id):
    """
    POST /api/v1/users/{id}/balance/adjust/
    Adjust user's leave balance (allocated_hours or adjustment_hours)
    """
    from leaves.models import LeaveBalance, LeaveRequest

    year = request.data.get('year', timezone.now().year)
    balance = get_object_or_404(LeaveBalance, user_id=user_id, year=year)

    reason = request.data.get('reason', '')
    if not reason:
        return Response({'error': 'Reason required for adjustment'}, status=status.HTTP_400_BAD_REQUEST)

    # Adjust allocated hours if provided
    if 'allocated_hours' in request.data:
        balance.allocated_hours = Decimal(str(request.data['allocated_hours']))

    # Add adjustment hours if provided
    if 'adjustment_hours' in request.data:
        balance.adjusted_hours += Decimal(str(request.data['adjustment_hours']))

    balance.save()

    # Create notification (if Notification model exists)
    try:
        from core.models import Notification
        Notification.objects.create(
            user_id=user_id,
            type='BALANCE_ADJUSTED',
            title='Leave Balance Adjusted',
            message=f'Your leave balance has been adjusted. Reason: {reason}',
            link='/leaves/balance'
        )
    except:
        pass  # Notification model may not exist yet

    return Response({
        'id': str(balance.id),
        'year': balance.year,
        'allocated_hours': float(balance.allocated_hours),
        'used_hours': float(balance.used_hours),
        'adjusted_hours': float(balance.adjusted_hours),
        'remaining_hours': float(balance.remaining_hours),
    })


@api_view(['POST'])
@permission_classes([IsHROrAdmin])
def create_user(request):
    """
    POST /api/v1/users/create/
    Create a new user (HR/Admin only)
    """
    from users.serializers import UserDetailSerializer

    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    # Create user with temporary password
    user = User.objects.create_user(
        email=email,
        password=request.data.get('password', 'TempPass123!'),  # Should be changed on first login
        first_name=request.data.get('first_name', ''),
        last_name=request.data.get('last_name', ''),
        role=request.data.get('role', 'EMPLOYEE'),
        status='ACTIVE',
    )

    serializer = UserDetailSerializer(user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_entity_options(request):
    """
    GET /admin/get-entity-options/?entity_id=xxx
    Returns locations and departments for a given entity (for admin cascading dropdowns)
    """
    from organizations.models import Entity, Location, Department

    entity_id = request.GET.get('entity_id')
    if not entity_id:
        return Response({'locations': [], 'departments': []})

    try:
        entity = Entity.objects.get(id=entity_id)
        locations = [
            {'id': str(loc.id), 'name': f"{loc.name} ({loc.city})"}
            for loc in entity.locations.filter(is_active=True)
        ]
        departments = [
            {'id': str(dept.id), 'name': dept.name}
            for dept in entity.departments.filter(is_active=True)
        ]
        return Response({'locations': locations, 'departments': departments})
    except Entity.DoesNotExist:
        return Response({'locations': [], 'departments': []})
