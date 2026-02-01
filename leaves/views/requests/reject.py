"""Leave request reject view."""

import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...serializers import LeaveRequestRejectSerializer
from ...services import LeaveApprovalService
from core.models import Notification

logger = logging.getLogger(__name__)


class LeaveRequestRejectView(generics.GenericAPIView):
    """Reject a leave request."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/reject/"""
        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user can approve this request
        if not LeaveApprovalService.can_manager_approve_request(request.user, leave_request):
            return Response(
                {'error': 'You do not have permission to reject this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate request
        serializer = LeaveRequestRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Reject the request
            rejected_request = LeaveApprovalService.reject_leave_request(
                leave_request,
                request.user,
                serializer.validated_data['reason']
            )

            # Create notification
            Notification.objects.create(
                user=leave_request.user,
                type='LEAVE_REJECTED',
                title='Leave Request Rejected',
                message=f'Your leave request for {leave_request.start_date} was rejected.',
                link=f'/leaves/{leave_request.id}'
            )

            return Response({
                'id': str(rejected_request.id),
                'status': rejected_request.status
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
