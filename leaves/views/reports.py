"""Leave reports view."""

from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import LeaveRequest, LeaveBalance

User = get_user_model()


class LeaveReportsView(generics.GenericAPIView):
    """Leave reports and analytics (HR/Admin only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/reports/?year=2026&department_id=xxx"""
        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can view reports'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get filters
        year = int(request.query_params.get('year', timezone.now().year))
        department_id = request.query_params.get('department_id')
        entity_id = request.query_params.get('entity_id')

        # Build base queryset
        requests_qs = LeaveRequest.objects.filter(start_date__year=year)
        balances_qs = LeaveBalance.objects.filter(year=year)
        users_qs = User.objects.filter(is_active=True)

        if department_id:
            requests_qs = requests_qs.filter(user__department_id=department_id)
            balances_qs = balances_qs.filter(user__department_id=department_id)
            users_qs = users_qs.filter(department_id=department_id)
        if entity_id:
            requests_qs = requests_qs.filter(user__entity_id=entity_id)
            balances_qs = balances_qs.filter(user__entity_id=entity_id)
            users_qs = users_qs.filter(entity_id=entity_id)

        # Summary stats
        total_requests = requests_qs.count()
        approved_requests = requests_qs.filter(status='APPROVED').count()
        pending_requests = requests_qs.filter(status='PENDING').count()
        rejected_requests = requests_qs.filter(status='REJECTED').count()

        total_hours_approved = requests_qs.filter(status='APPROVED').aggregate(
            total=Sum('total_hours')
        )['total'] or 0

        # Balance utilization
        balance_stats = balances_qs.aggregate(
            total_allocated=Sum('allocated_hours'),
            total_used=Sum('used_hours'),
        )

        # Requests by month
        monthly_data = requests_qs.filter(status='APPROVED').annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            count=Count('id'),
            hours=Sum('total_hours')
        ).order_by('month')

        # Requests by category
        category_data = requests_qs.filter(status='APPROVED').values(
            'leave_category__name', 'leave_category__color'
        ).annotate(
            count=Count('id'),
            hours=Sum('total_hours')
        ).order_by('-hours')

        # Top users by leave taken
        top_users = requests_qs.filter(status='APPROVED').values(
            'user__email', 'user__first_name', 'user__last_name'
        ).annotate(
            total_hours=Sum('total_hours'),
            request_count=Count('id')
        ).order_by('-total_hours')[:10]

        return Response({
            'year': year,
            'summary': {
                'total_requests': total_requests,
                'approved': approved_requests,
                'pending': pending_requests,
                'rejected': rejected_requests,
                'total_hours_approved': float(total_hours_approved),
                'total_employees': users_qs.count(),
            },
            'balance_utilization': {
                'total_allocated': float(balance_stats['total_allocated'] or 0),
                'total_used': float(balance_stats['total_used'] or 0),
            },
            'monthly_breakdown': [
                {
                    'month': item['month'].strftime('%Y-%m') if item['month'] else None,
                    'count': item['count'],
                    'hours': float(item['hours'] or 0)
                }
                for item in monthly_data
            ],
            'by_category': [
                {
                    'category': item['leave_category__name'] or 'Uncategorized',
                    'color': item['leave_category__color'] or '#6B7280',
                    'count': item['count'],
                    'hours': float(item['hours'] or 0)
                }
                for item in category_data
            ],
            'top_users': [
                {
                    'email': item['user__email'],
                    'name': f"{item['user__first_name'] or ''} {item['user__last_name'] or ''}".strip(),
                    'total_hours': float(item['total_hours']),
                    'request_count': item['request_count']
                }
                for item in top_users
            ]
        })
