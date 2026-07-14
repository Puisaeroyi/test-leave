"""Leave request cancel view."""

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import LeaveRequest
from ...utils import can_modify_request
from core.services.notification_service import create_leave_cancelled_notification


class LeaveRequestCancelView(generics.GenericAPIView):
    """Cancel a leave request."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/cancel/"""
        request_id = kwargs.get('pk')
        user = request.user

        try:
            with transaction.atomic():
                try:
                    leave_request = LeaveRequest.objects.select_for_update().get(
                        id=request_id, user=user
                    )
                except LeaveRequest.DoesNotExist:
                    # Owner-scoped: missing or non-owned → 404 / 403 distinction
                    if LeaveRequest.objects.filter(id=request_id).exists():
                        return Response(
                            {'error': 'You can only cancel your own requests'},
                            status=status.HTTP_403_FORBIDDEN,
                        )
                    return Response(
                        {'error': 'Leave request not found'},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                can_cancel, error = can_modify_request(leave_request)
                if not can_cancel:
                    return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

                leave_request.status = 'CANCELLED'
                leave_request.save()

            # Fail-soft after commit
            try:
                create_leave_cancelled_notification(leave_request)
            except Exception:
                pass

            return Response({
                'id': str(leave_request.id),
                'status': leave_request.status,
                'message': 'Leave request cancelled successfully'
            })
        except Exception:
            return Response(
                {'error': 'Failed to cancel leave request'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
