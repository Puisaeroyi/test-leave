"""Export approved leave requests to Excel."""
from datetime import date
from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from leaves.models import LeaveRequest
from users.permissions import IsHROrAdmin


class ExportApprovedLeavesView(APIView):
    """Export approved leave requests within a date range to .xlsx."""

    permission_classes = [IsAuthenticated, IsHROrAdmin]

    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not start_date or not end_date:
            return HttpResponse(
                "start_date and end_date query params required.",
                status=400,
            )

        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError:
            return HttpResponse(
                "Invalid date format. Use YYYY-MM-DD.", status=400
            )

        # Build query filters - HR and ADMIN both have global access for export
        filters = {
            "status": "APPROVED",
            "start_date__gte": start,
            "start_date__lte": end,
        }

        queryset = (
            LeaveRequest.objects.filter(**filters)
            .select_related(
                "user",
                "leave_category",
                "approved_by",
                "user__entity",
                "user__location",
                "user__department",
            )
            .order_by("start_date", "user__last_name")
        )

        # Cap at 10,000 rows to prevent OOM
        MAX_EXPORT_ROWS = 10000
        total = queryset.count()
        if total > MAX_EXPORT_ROWS:
            return HttpResponse(
                f"Export too large ({total} rows). Max {MAX_EXPORT_ROWS}. Narrow the date range.",
                status=400,
            )
        queryset = queryset[:MAX_EXPORT_ROWS]

        wb = Workbook()
        ws = wb.active
        ws.title = "Approved Leaves"

        headers = [
            "Employee Code",
            "Employee Name",
            "Email",
            "Department",
            "Location",
            "Entity",
            "Leave Type",
            "Exempt Type",
            "Start Date",
            "End Date",
            "Total Hours",
            "Total Days",
            "Status",
            "Approved By",
            "Approved Date",
            "Reason",
        ]

        # Header styling
        header_fill = PatternFill(
            start_color="4F81BD", end_color="4F81BD", fill_type="solid"
        )
        header_font = Font(color="FFFFFF", bold=True)
        header_align = Alignment(horizontal="center")

        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_align

        # Data rows
        for row_idx, lr in enumerate(queryset, 2):
            user = lr.user
            ws.cell(row=row_idx, column=1, value=user.employee_code or "")
            ws.cell(
                row=row_idx,
                column=2,
                value=f"{user.first_name} {user.last_name}".strip(),
            )
            ws.cell(row=row_idx, column=3, value=user.email)
            ws.cell(
                row=row_idx,
                column=4,
                value=getattr(user.department, "department_name", "") or "",
            )
            ws.cell(
                row=row_idx,
                column=5,
                value=getattr(user.location, "location_name", "") or "",
            )
            ws.cell(
                row=row_idx,
                column=6,
                value=getattr(user.entity, "entity_name", "") or "",
            )
            ws.cell(
                row=row_idx,
                column=7,
                value=getattr(lr.leave_category, "category_name", "") or "",
            )
            ws.cell(row=row_idx, column=8, value=lr.exempt_type)
            ws.cell(
                row=row_idx, column=9, value=lr.start_date.isoformat()
            )
            ws.cell(
                row=row_idx, column=10, value=lr.end_date.isoformat()
            )
            hours = float(lr.total_hours)
            ws.cell(row=row_idx, column=11, value=hours)
            ws.cell(row=row_idx, column=12, value=round(hours / 8, 2))
            ws.cell(row=row_idx, column=13, value=lr.status)
            ws.cell(
                row=row_idx,
                column=14,
                value=(
                    f"{lr.approved_by.first_name} {lr.approved_by.last_name}".strip()
                    if lr.approved_by
                    else ""
                ),
            )
            ws.cell(
                row=row_idx,
                column=15,
                value=(
                    lr.approved_at.strftime("%Y-%m-%d %H:%M")
                    if lr.approved_at
                    else ""
                ),
            )
            ws.cell(row=row_idx, column=16, value=lr.reason or "")

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val = str(cell.value) if cell.value else ""
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = min(max_len + 2, 50)

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)

        filename = f"approved_leaves_{start_date}_to_{end_date}.xlsx"
        response = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
