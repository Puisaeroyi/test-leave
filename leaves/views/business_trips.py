"""
Business trip views - auto-approved trips that do NOT deduct from leave balance
"""
from decimal import Decimal
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import LeaveRequest
from ..serializers import BusinessTripSerializer, BusinessTripCreateSerializer
from ..services import BusinessTripService
from ..constants import DEFAULT_PAGE_SIZE, HOURS_PER_DAY
from ..utils import check_overlapping_requests, validate_leave_request_dates, calculate_leave_hours


class BusinessTripListCreateView(generics.ListCreateAPIView):
    """List and create business trips"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/business-trips/ - List user's business trips"""
        user = request.user
        queryset = LeaveRequest.objects.filter(
            user=user,
            request_type='BUSINESS_TRIP'
        ).order_by('-created_at')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        items = queryset[start:end]

        serializer = BusinessTripSerializer(items, many=True)
        return Response({
            'count': total,
            'results': serializer.data
        })

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/business-trips/ - Create and auto-approve"""
        user = request.user
        serializer = BusinessTripCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        start_date = data['start_date']
        end_date = data['end_date']
        reason = data['reason']

        # Validate dates
        is_valid, error = validate_leave_request_dates(start_date, end_date)
        if not is_valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Check overlapping requests (both leaves and business trips)
        overlapping = check_overlapping_requests(user, start_date, end_date)
        if overlapping.exists():
            return Response(
                {'error': 'You have an overlapping request for these dates'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate hours (full days only, using existing utility)
        total_hours = calculate_leave_hours(user, start_date, end_date, 'FULL_DAY')

        if total_hours <= 0:
            return Response(
                {'error': 'No working days in selected date range'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create business trip request (NO balance check - trips don't affect balance)
        trip = LeaveRequest.objects.create(
            user=user,
            request_type='BUSINESS_TRIP',
            start_date=start_date,
            end_date=end_date,
            shift_type='FULL_DAY',
            total_hours=total_hours,
            reason=reason,
            status='PENDING'
        )

        # Auto-approve (NO balance deduction)
        try:
            BusinessTripService.auto_approve_business_trip(trip)
        except ValueError as e:
            trip.delete()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Refresh from DB
        trip.refresh_from_db()

        return Response(BusinessTripSerializer(trip).data, status=status.HTTP_201_CREATED)


class BusinessTripDetailView(generics.RetrieveAPIView):
    """Get business trip detail"""
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessTripSerializer

    def get_queryset(self):
        return LeaveRequest.objects.filter(
            user=self.request.user,
            request_type='BUSINESS_TRIP'
        )


class BusinessTripCancelView(generics.GenericAPIView):
    """Cancel a business trip (no balance restoration needed - trips don't affect balance)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """POST /api/v1/leaves/business-trips/<pk>/cancel/"""
        try:
            trip = LeaveRequest.objects.get(
                pk=pk,
                user=request.user,
                request_type='BUSINESS_TRIP'
            )
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Business trip not found'}, status=status.HTTP_404_NOT_FOUND)

        if trip.status == 'CANCELLED':
            return Response({'error': 'Already cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        # Simply cancel - no balance restoration needed for business trips
        trip.status = 'CANCELLED'
        trip.save()

        return Response(BusinessTripSerializer(trip).data)
