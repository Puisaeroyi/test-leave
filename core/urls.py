"""
Core API URLs (Notifications)
"""
from django.urls import path
from .views import (
    AnnouncementDetailView,
    AnnouncementListCreateView,
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationDismissAllView,
    NotificationUnreadCountView,
)

urlpatterns = [
    # Announcements
    path('announcements/', AnnouncementListCreateView.as_view(), name='announcement_list_create'),
    path('announcements/<uuid:pk>/', AnnouncementDetailView.as_view(), name='announcement_detail'),

    # Notifications
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<uuid:pk>/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('dismiss-all/', NotificationDismissAllView.as_view(), name='notification_dismiss_all'),
    path('unread-count/', NotificationUnreadCountView.as_view(), name='notification_unread_count'),
]
