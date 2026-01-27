"""
Leave Management API URLs
"""
from django.urls import path
from .views import (
    TeamCalendarView,
    LeaveCategoryListView,
    LeaveBalanceMeView,
    LeaveBalanceListView,
    LeaveBalanceAdjustView,
    LeaveRequestListView,
    LeaveRequestMyView,
    LeaveRequestDetailView,
    LeaveRequestApproveView,
    LeaveRequestRejectView,
    LeaveRequestCancelView,
    PublicHolidayListView,
    PublicHolidayDetailView,
    LeaveReportsView,
)

urlpatterns = [
    # Team Calendar
    path('calendar/', TeamCalendarView.as_view(), name='team_calendar'),

    # Leave Categories
    path('categories/', LeaveCategoryListView.as_view(), name='leave_category_list'),

    # Leave Balances
    path('balance/my/', LeaveBalanceMeView.as_view(), name='leave_balance_my'),
    path('balances/me/', LeaveBalanceMeView.as_view(), name='leave_balance_me'),
    path('balances/', LeaveBalanceListView.as_view(), name='leave_balance_list'),
    path('balances/<uuid:user_id>/adjust/', LeaveBalanceAdjustView.as_view(), name='leave_balance_adjust'),

    # Leave Requests
    path('requests/', LeaveRequestListView.as_view(), name='leave_request_list'),
    path('requests/my/', LeaveRequestMyView.as_view(), name='leave_request_my'),
    path('requests/<uuid:pk>/', LeaveRequestDetailView.as_view(), name='leave_request_detail'),
    path('requests/<uuid:pk>/approve/', LeaveRequestApproveView.as_view(), name='leave_request_approve'),
    path('requests/<uuid:pk>/reject/', LeaveRequestRejectView.as_view(), name='leave_request_reject'),
    path('requests/<uuid:pk>/cancel/', LeaveRequestCancelView.as_view(), name='leave_request_cancel'),

    # Public Holidays
    path('holidays/', PublicHolidayListView.as_view(), name='public_holiday_list'),
    path('holidays/<uuid:pk>/', PublicHolidayDetailView.as_view(), name='public_holiday_detail'),

    # Reports (HR/Admin)
    path('reports/', LeaveReportsView.as_view(), name='leave_reports'),
]
