"""Leave request reject view."""

import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction

from ...models import LeaveRequest
from ...serializers import LeaveRequestRejectSerializer
from ...services import LeaveApprovalService
from ...leave_request_updates import LeaveUpdateError, check_action_version
from core.services.notification_service import create_leave_rejected_notification
from core.services.email_service import send_leave_rejected_email

logger = logging.getLogger(__name__)


class LeaveRequestRejectView(generics.GenericAPIView):
    """Reject a leave request (supports both PENDING and APPROVED status)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/reject/"""
        request_id = kwargs.get('pk')

        if 'expected_updated_at' not in request.data:
            return Response(
                {'error': 'expected_updated_at is required', 'code': 'version_required'},
                status=status.HTTP_428_PRECONDITION_REQUIRED,
            )

        serializer = LeaveRequestRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                try:
                    leave_request = LeaveRequest.objects.select_for_update().get(id=request_id)
                except LeaveRequest.DoesNotExist:
                    return Response(
                        {'error': 'Leave request not found'},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Authz before version so 409 never leaks leave detail to non-approvers
                if not LeaveApprovalService.can_manager_approve_request(request.user, leave_request):
                    return Response(
                        {'error': 'You do not have permission to reject this request'},
                        status=status.HTTP_403_FORBIDDEN
                    )

                try:
                    check_action_version(
                        leave_request,
                        serializer.validated_data.get('expected_updated_at'),
                        request.user,
                    )
                except LeaveUpdateError as exc:
                    return Response(exc.payload, status=exc.http_status)

                rejected_request = LeaveApprovalService.reject_leave_request(
                    leave_request,
                    request.user,
                    serializer.validated_data['reason']
                )

            create_leave_rejected_notification(rejected_request)
            send_leave_rejected_email(rejected_request)

            return Response({
                'id': str(rejected_request.id),
                'status': rejected_request.status
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'error': str(e.message) if hasattr(e, 'message') else ' '.join(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
