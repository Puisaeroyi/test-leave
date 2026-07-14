"""Leave request approve view."""

import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from ...models import LeaveRequest
from ...serializers import LeaveRequestApproveSerializer
from ...services import LeaveApprovalService
from ...leave_request_updates import LeaveUpdateError, check_action_version
from core.services.notification_service import (
    create_leave_approved_notification,
)
from core.services.email_service import send_leave_approved_email

logger = logging.getLogger(__name__)


class LeaveRequestApproveView(generics.GenericAPIView):
    """Approve a leave request with optional comment."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/requests/{id}/approve/"""
        request_id = kwargs.get('pk')

        if 'expected_updated_at' not in request.data:
            return Response(
                {'error': 'expected_updated_at is required', 'code': 'version_required'},
                status=status.HTTP_428_PRECONDITION_REQUIRED,
            )

        serializer = LeaveRequestApproveSerializer(data=request.data)
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
                        {'error': 'You do not have permission to approve this request'},
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

                comment = serializer.validated_data.get('comment', '')
                approved_request = LeaveApprovalService.approve_leave_request(
                    leave_request,
                    request.user,
                    comment=comment
                )

            if approved_request.status == LeaveRequest.Status.APPROVED:
                create_leave_approved_notification(approved_request)
                send_leave_approved_email(approved_request)

            return Response({
                'id': str(approved_request.id),
                'status': approved_request.status,
                'current_approval_step': approved_request.current_approval_step,
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
