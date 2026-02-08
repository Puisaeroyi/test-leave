"""Leave request detail view."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...services import LeaveApprovalService


class LeaveRequestDetailView(generics.RetrieveAPIView):
    """Leave request detail view (read-only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/requests/{id}/"""
        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.select_related('user').get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        # Permission check: owner, assigned approver, or HR/ADMIN
        user = request.user
        is_owner = leave_request.user == user
        is_approver = leave_request.user.approver == user
        is_hr_admin = user.role in ['HR', 'ADMIN']
        if not (is_owner or is_approver or is_hr_admin):
            return Response(
                {'error': 'You do not have permission to view this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = LeaveApprovalService.get_request_detail_with_conflicts(leave_request)
        return Response(data)
