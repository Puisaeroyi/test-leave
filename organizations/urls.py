"""
Organizations API URLs
"""
from django.urls import path
from .views import (
    EntityListView,
    LocationListView,
    DepartmentListView,
    DepartmentManagerListView,
)

urlpatterns = [
    # Entities
    path('entities/', EntityListView.as_view(), name='entity_list'),

    # Locations
    path('locations/', LocationListView.as_view(), name='location_list'),

    # Departments
    path('departments/', DepartmentListView.as_view(), name='department_list'),

    # Department Managers
    path('managers/', DepartmentManagerListView.as_view(), name='department_manager_list'),
]
