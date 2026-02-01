"""Leave request detail view."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...services import LeaveApprovalService


class LeaveRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Leave request detail view."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/requests/{id}/"""
        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        data = LeaveApprovalService.get_request_detail_with_conflicts(leave_request)
        return Response(data)
