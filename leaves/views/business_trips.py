"""
Business trip views - separate from leaves, no approval workflow, no balance impact
"""
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import BusinessTrip
from ..serializers import BusinessTripSerializer, BusinessTripCreateSerializer
from ..constants import DEFAULT_PAGE_SIZE
from ..utils import validate_leave_request_dates, check_overlapping_business_trips


class BusinessTripListCreateView(generics.ListCreateAPIView):
    """List and create business trips"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/business-trips/ - List user's business trips"""
        user = request.user
        queryset = BusinessTrip.objects.filter(
            user=user
        ).order_by('-created_at')

        # Pagination with DoS protection
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))))
        except (ValueError, TypeError):
            page = 1
            page_size = DEFAULT_PAGE_SIZE
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
        """POST /api/v1/leaves/business-trips/ - Create business trip (no approval needed)"""
        user = request.user
        serializer = BusinessTripCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        start_date = data['start_date']
        end_date = data['end_date']

        # Validate dates
        is_valid, error = validate_leave_request_dates(start_date, end_date)
        if not is_valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Check for overlapping business trips
        overlapping = check_overlapping_business_trips(user, start_date, end_date)
        if overlapping.exists():
            return Response(
                {'error': 'You have an overlapping business trip for these dates'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create business trip (no approval workflow, no balance impact)
        trip = BusinessTrip.objects.create(
            user=user,
            city=data['city'],
            country=data['country'],
            start_date=start_date,
            end_date=end_date,
            note=data.get('note', ''),
            attachment_url=data.get('attachment_url', '')
        )

        return Response(BusinessTripSerializer(trip).data, status=status.HTTP_201_CREATED)


class BusinessTripDetailView(generics.RetrieveAPIView):
    """Get business trip detail"""
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessTripSerializer

    def get_queryset(self):
        return BusinessTrip.objects.filter(user=self.request.user)


class BusinessTripCancelView(generics.GenericAPIView):
    """Cancel a business trip (no balance restoration needed - trips don't affect balance)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """POST /api/v1/leaves/business-trips/<pk>/cancel/"""
        try:
            trip = BusinessTrip.objects.get(
                pk=pk,
                user=request.user
            )
        except BusinessTrip.DoesNotExist:
            return Response({'error': 'Business trip not found'}, status=status.HTTP_404_NOT_FOUND)

        # Simply delete - no status field, no balance restoration
        trip.delete()

        return Response({'message': 'Business trip cancelled successfully'}, status=status.HTTP_200_OK)
