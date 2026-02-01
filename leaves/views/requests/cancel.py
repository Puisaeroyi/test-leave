"""Leave request cancel view."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...utils import can_modify_request


class LeaveRequestCancelView(generics.GenericAPIView):
    """Cancel a leave request."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/cancel/"""
        request_id = kwargs.get('pk')
        user = request.user

        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': 'Leave request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check ownership
        if leave_request.user_id != user.id:
            return Response(
                {'error': 'You can only cancel your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if can be cancelled
        can_cancel, error = can_modify_request(leave_request)
        if not can_cancel:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        # Cancel the request
        leave_request.status = 'CANCELLED'
        leave_request.save()

        return Response({
            'id': str(leave_request.id),
            'status': leave_request.status,
            'message': 'Leave request cancelled successfully'
        })
