from django.contrib import admin
from .models import LeaveCategory, LeaveBalance, LeaveRequest, PublicHoliday


@admin.register(LeaveCategory)
class LeaveCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'color', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'allocated_hours', 'used_hours', 'adjusted_hours', 'remaining_hours']
    list_filter = ['year']
    search_fields = ['user__email']
    readonly_fields = ['remaining_hours']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'start_date', 'end_date', 'shift_type', 'total_hours', 'status', 'approved_by']
    list_filter = ['status', 'shift_type', 'leave_category', 'start_date']
    search_fields = ['user__email', 'reason']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'year', 'entity', 'location', 'is_recurring', 'is_active']
    list_filter = ['year', 'is_active', 'is_recurring']
    search_fields = ['name']
