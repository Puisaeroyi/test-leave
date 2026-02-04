"""Leave request approve view."""

import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...services import LeaveApprovalService
from core.services.notification_service import create_leave_approved_notification

logger = logging.getLogger(__name__)


class LeaveRequestApproveView(generics.GenericAPIView):
    """Approve a leave request (no comment required)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/approve/"""
        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user can approve this request
        if not LeaveApprovalService.can_manager_approve_request(request.user, leave_request):
            return Response(
                {'error': 'You do not have permission to approve this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Approve the request (no comment needed)
            approved_request = LeaveApprovalService.approve_leave_request(
                leave_request,
                request.user
            )

            # Create notification for employee
            create_leave_approved_notification(approved_request)

            return Response({
                'id': str(approved_request.id),
                'status': approved_request.status
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
