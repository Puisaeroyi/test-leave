"""Pending manager review count view."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...services import LeaveApprovalService


class LeaveRequestPendingReviewCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'count': LeaveApprovalService.get_pending_review_count(request.user),
        })
