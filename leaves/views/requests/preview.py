"""Leave request hours preview view.

Read-only endpoint that returns the deductible hours + per-day breakdown for a
prospective leave request. Reuses the exact calculation utilities the create
path uses so the preview can never disagree with the persisted deduction.
"""

from datetime import datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import LeaveRequest
from ...utils import (
    calculate_full_day_leave_breakdown,
    calculate_leave_hours,
    infer_custom_hour_offsets,
    validate_leave_request_dates,
)


class LeaveRequestPreviewView(APIView):
    """POST /api/v1/leaves/requests/preview/ - compute hours without persisting."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        # Parse dates (mirror create endpoint)
        try:
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_valid, error = validate_leave_request_dates(start_date, end_date)
        if not is_valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        shift_type = data.get('shift_type', 'FULL_DAY')
        if shift_type not in LeaveRequest.ShiftType.values:
            return Response(
                {'error': 'Invalid shift_type. Must be FULL_DAY or CUSTOM_HOURS'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_time = None
        end_time = None
        start_day_offset = 0
        end_day_offset = 0

        if shift_type == 'CUSTOM_HOURS':
            try:
                start_time = datetime.strptime(data.get('start_time'), '%H:%M').time()
                end_time = datetime.strptime(data.get('end_time'), '%H:%M').time()
                if user.work_shift_id:
                    start_day_offset, end_day_offset = infer_custom_hour_offsets(
                        user, start_time, end_time
                    )
                else:
                    start_day_offset = int(data.get('start_day_offset', 0))
                    end_day_offset = int(data.get('end_day_offset', 0))
            except (ValueError, TypeError):
                return Response(
                    {'error': 'start_time and end_time required for CUSTOM_HOURS (format: HH:MM)'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Compute hours by reusing the create-path utilities (single source of truth)
        try:
            if shift_type == 'FULL_DAY':
                total_hours, breakdown = calculate_full_day_leave_breakdown(
                    user, start_date, end_date,
                )
            else:
                total_hours = calculate_leave_hours(
                    user, start_date, end_date, shift_type, start_time, end_time,
                    start_day_offset=start_day_offset, end_day_offset=end_day_offset,
                )
                breakdown = []
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'total_hours': float(total_hours),
            'breakdown': breakdown,
        })
