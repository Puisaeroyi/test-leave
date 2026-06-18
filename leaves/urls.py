"""
Leave Management API URLs
"""
from django.urls import path
from .views import (
    TeamCalendarView,
    LeaveCategoryListView,
    LeaveBalanceMeView,
    LeaveRequestListView,
    LeaveRequestPreviewView,
    LeaveRequestMyView,
    LeaveRequestDetailView,
    LeaveRequestApproveView,
    LeaveRequestRejectView,
    LeaveRequestCancelView,
    PublicHolidayListView,
    HolidayCalendarListView,
    HolidayCalendarGenerateView,
    HolidayCalendarDetailView,
    HolidayCalendarPublishView,
    HolidayCalendarUnpublishView,
    HolidayCalendarHolidayCreateView,
    HolidayDetailView,
    BusinessTripListCreateView,
    BusinessTripDetailView,
    BusinessTripCancelView,
    BusinessTripTeamListView,
    FileUploadView,
    ExportApprovedLeavesView,
)

urlpatterns = [
    # File Upload
    path('upload/', FileUploadView.as_view(), name='file_upload'),

    # Export
    path('export/approved/', ExportApprovedLeavesView.as_view(), name='export_approved_leaves'),

    # Team Calendar
    path('calendar/', TeamCalendarView.as_view(), name='team_calendar'),

    # Leave Categories
    path('categories/', LeaveCategoryListView.as_view(), name='leave_category_list'),

    # Leave Balances (user's own balance only)
    path('balances/me/', LeaveBalanceMeView.as_view(), name='leave_balance_me'),

    # Leave Requests
    path('requests/', LeaveRequestListView.as_view(), name='leave_request_list'),
    path('requests/preview/', LeaveRequestPreviewView.as_view(), name='leave_request_preview'),
    path('requests/my/', LeaveRequestMyView.as_view(), name='leave_request_my'),
    path('requests/<uuid:pk>/', LeaveRequestDetailView.as_view(), name='leave_request_detail'),
    path('requests/<uuid:pk>/approve/', LeaveRequestApproveView.as_view(), name='leave_request_approve'),
    path('requests/<uuid:pk>/reject/', LeaveRequestRejectView.as_view(), name='leave_request_reject'),
    path('requests/<uuid:pk>/cancel/', LeaveRequestCancelView.as_view(), name='leave_request_cancel'),

    # Holiday administration (specific paths before generic holiday detail)
    path('holiday-calendars/', HolidayCalendarListView.as_view(), name='holiday_calendar_list'),
    path('holiday-calendars/generate/', HolidayCalendarGenerateView.as_view(), name='holiday_calendar_generate'),
    path('holiday-calendars/<uuid:pk>/publish/', HolidayCalendarPublishView.as_view(), name='holiday_calendar_publish'),
    path('holiday-calendars/<uuid:pk>/unpublish/', HolidayCalendarUnpublishView.as_view(), name='holiday_calendar_unpublish'),
    path('holiday-calendars/<uuid:pk>/holidays/', HolidayCalendarHolidayCreateView.as_view(), name='holiday_calendar_holiday_create'),
    path('holiday-calendars/<uuid:pk>/', HolidayCalendarDetailView.as_view(), name='holiday_calendar_detail'),

    # Public Holidays
    path('holidays/', PublicHolidayListView.as_view(), name='public_holiday_list'),
    path('holidays/<uuid:pk>/', HolidayDetailView.as_view(), name='holiday_detail'),

    # Business Trips (auto-approved, no balance deduction)
    # IMPORTANT: More specific patterns must come before generic ones
    path('business-trips/team/', BusinessTripTeamListView.as_view(), name='business_trip_team_list'),
    path('business-trips/<uuid:pk>/cancel/', BusinessTripCancelView.as_view(), name='business_trip_cancel'),
    path('business-trips/<uuid:pk>/', BusinessTripDetailView.as_view(), name='business_trip_detail'),
    path('business-trips/', BusinessTripListCreateView.as_view(), name='business_trip_list'),
]
