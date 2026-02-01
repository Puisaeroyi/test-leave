"""
Leave Management API URLs
"""
from django.urls import path
from .views import (
    TeamCalendarView,
    LeaveCategoryListView,
    LeaveBalanceMeView,
    LeaveRequestListView,
    LeaveRequestMyView,
    LeaveRequestDetailView,
    LeaveRequestApproveView,
    LeaveRequestRejectView,
    LeaveRequestCancelView,
    PublicHolidayListView,
    BusinessTripListCreateView,
    BusinessTripDetailView,
    BusinessTripCancelView,
)

urlpatterns = [
    # Team Calendar
    path('calendar/', TeamCalendarView.as_view(), name='team_calendar'),

    # Leave Categories
    path('categories/', LeaveCategoryListView.as_view(), name='leave_category_list'),

    # Leave Balances (user's own balance only)
    path('balances/me/', LeaveBalanceMeView.as_view(), name='leave_balance_me'),

    # Leave Requests
    path('requests/', LeaveRequestListView.as_view(), name='leave_request_list'),
    path('requests/my/', LeaveRequestMyView.as_view(), name='leave_request_my'),
    path('requests/<uuid:pk>/', LeaveRequestDetailView.as_view(), name='leave_request_detail'),
    path('requests/<uuid:pk>/approve/', LeaveRequestApproveView.as_view(), name='leave_request_approve'),
    path('requests/<uuid:pk>/reject/', LeaveRequestRejectView.as_view(), name='leave_request_reject'),
    path('requests/<uuid:pk>/cancel/', LeaveRequestCancelView.as_view(), name='leave_request_cancel'),

    # Public Holidays (read-only)
    path('holidays/', PublicHolidayListView.as_view(), name='public_holiday_list'),

    # Business Trips (auto-approved, no balance deduction)
    path('business-trips/', BusinessTripListCreateView.as_view(), name='business_trip_list'),
    path('business-trips/<uuid:pk>/', BusinessTripDetailView.as_view(), name='business_trip_detail'),
    path('business-trips/<uuid:pk>/cancel/', BusinessTripCancelView.as_view(), name='business_trip_cancel'),
]
