"""Leave request hour preview view."""

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
    ZERO_DEDUCTIBLE_HOURS_MESSAGE,
)


class LeaveRequestPreviewView(APIView):
    """Calculate deductible hours without creating a leave request."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            start_date = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_valid, error = validate_leave_request_dates(start_date, end_date)
        if not is_valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        shift_type = request.data.get('shift_type', LeaveRequest.ShiftType.FULL_DAY)
        if shift_type not in LeaveRequest.ShiftType.values:
            return Response(
                {'error': 'Invalid shift_type. Must be FULL_DAY or CUSTOM_HOURS'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if shift_type == LeaveRequest.ShiftType.FULL_DAY:
                total_hours, leave_breakdown = calculate_full_day_leave_breakdown(
                    request.user,
                    start_date,
                    end_date,
                )
            else:
                start_time = datetime.strptime(
                    request.data.get('start_time'), '%H:%M'
                ).time()
                end_time = datetime.strptime(
                    request.data.get('end_time'), '%H:%M'
                ).time()
                start_day_offset, end_day_offset = infer_custom_hour_offsets(
                    request.user,
                    start_time,
                    end_time,
                )
                total_hours = calculate_leave_hours(
                    request.user,
                    start_date,
                    end_date,
                    shift_type,
                    start_time,
                    end_time,
                    start_day_offset=start_day_offset,
                    end_day_offset=end_day_offset,
                )
                leave_breakdown = []
        except (ValueError, TypeError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'total_hours': float(total_hours),
            'leave_breakdown': leave_breakdown,
            'zero_hours_message': (
                ZERO_DEDUCTIBLE_HOURS_MESSAGE if total_hours <= 0 else None
            ),
        })
