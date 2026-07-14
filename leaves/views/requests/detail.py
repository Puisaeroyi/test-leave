"""Leave request detail view with owner PATCH."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...services import LeaveApprovalService
from ...leave_request_updates import LeaveUpdateError, update_leave_request
from ...serializers import LeaveRequestSerializer


class LeaveRequestDetailView(generics.RetrieveAPIView):
    """Leave request detail (GET) and owner edit (PATCH)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/requests/{id}/"""
        request_id = kwargs.get('pk')
        try:
            leave_request = LeaveRequest.objects.select_related(
                'user', 'first_approver', 'final_approver'
            ).get(id=request_id)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_owner = leave_request.user == user
        is_approver = user in {
            leave_request.first_approver or leave_request.user.approver_1,
            leave_request.final_approver or leave_request.user.approver_2,
        }
        is_hr_admin = (
            user.role == 'ADMIN'
            or (
                user.role == 'HR'
                and user.entity_id is not None
                and leave_request.user.entity_id == user.entity_id
            )
        )
        if not (is_owner or is_approver or is_hr_admin):
            return Response(
                {'error': 'You do not have permission to view this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = LeaveApprovalService.get_request_detail_with_conflicts(leave_request)
        # Overlay can_edit for the actor
        ser = LeaveRequestSerializer(
            leave_request, context={'request': request, 'actor': user}
        )
        data['can_edit'] = ser.data.get('can_edit', False)
        data['updated_at'] = ser.data.get('updated_at')
        return Response(data)

    def patch(self, request, *args, **kwargs):
        """PATCH /api/v1/leaves/requests/{id}/ — owner-only edit while fully pending."""
        request_id = kwargs.get('pk')
        try:
            data, http_status = update_leave_request(
                request.user, request_id, request.data
            )
            return Response(data, status=http_status)
        except LeaveUpdateError as exc:
            return Response(exc.payload, status=exc.http_status)
