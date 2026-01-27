from django.contrib import admin
from .models import Entity, Location, Department, DepartmentManager


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'entity', 'is_active']
    list_filter = ['is_active', 'entity']
    search_fields = ['name', 'city']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'entity', 'is_active']
    list_filter = ['is_active', 'entity']
    search_fields = ['name', 'code']


@admin.register(DepartmentManager)
class DepartmentManagerAdmin(admin.ModelAdmin):
    list_display = ['manager', 'entity', 'department', 'location', 'is_active']
    list_filter = ['is_active', 'entity', 'department', 'location']
    search_fields = ['manager__email']
