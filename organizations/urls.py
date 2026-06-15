"""
Organizations API URLs
"""
from django.urls import path
from .views import (
    EntityListView,
    LocationListView,
    DepartmentListView,
    EntityCreateView,
    EntityUpdateView,
    EntitySoftDeleteView,
    EntityDeleteImpactView,
    WorkShiftListCreateView,
    WorkShiftDetailView,
)

urlpatterns = [
    # Entities - List
    path('entities/', EntityListView.as_view(), name='entity_list'),

    # Entities - CRUD operations
    path('entities/create/', EntityCreateView.as_view(), name='entity_create'),
    path('entities/<uuid:pk>/update/', EntityUpdateView.as_view(), name='entity_update'),
    path('entities/<uuid:pk>/soft-delete/', EntitySoftDeleteView.as_view(), name='entity_soft_delete'),
    path('entities/<uuid:pk>/delete-impact/', EntityDeleteImpactView.as_view(), name='entity_delete_impact'),

    # Locations
    path('locations/', LocationListView.as_view(), name='location_list'),

    # Departments
    path('departments/', DepartmentListView.as_view(), name='department_list'),
    path('work-shifts/', WorkShiftListCreateView.as_view(), name='work_shift_list'),
    path('work-shifts/<uuid:pk>/', WorkShiftDetailView.as_view(), name='work_shift_detail'),
]
