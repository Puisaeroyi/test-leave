from django.contrib import admin
from .models import (
    BusinessTrip,
    HolidayCalendar,
    HolidayTemplate,
    HolidayTemplateDate,
    LeaveBalance,
    LeaveCategory,
    LeaveRequest,
    PublicHoliday,
)


@admin.register(LeaveCategory)
class LeaveCategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'code', 'balance_bucket', 'sort_order', 'is_active']
    list_filter = ['balance_bucket', 'is_active']
    search_fields = ['category_name', 'code']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'balance_type', 'allocated_hours', 'used_hours', 'adjusted_hours', 'remaining_hours']
    list_filter = ['year', 'balance_type']
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
    list_display = ['holiday_name', 'start_date', 'end_date', 'year', 'entity', 'location', 'is_recurring', 'is_active']
    list_filter = ['year', 'is_active', 'is_recurring']
    search_fields = ['holiday_name']


@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):
    list_display = ['name', 'country_code', 'year', 'entity', 'location', 'status']
    list_filter = ['country_code', 'year', 'status']
    search_fields = ['name', 'entity__entity_name', 'location__location_name']


class HolidayTemplateDateInline(admin.TabularInline):
    model = HolidayTemplateDate
    extra = 0


@admin.register(HolidayTemplate)
class HolidayTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'country_code', 'year', 'version', 'source_name']
    list_filter = ['country_code', 'year']
    inlines = [HolidayTemplateDateInline]


@admin.register(BusinessTrip)
class BusinessTripAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'start_date', 'end_date']
    list_filter = ['start_date', 'country']
    search_fields = ['user__email', 'city', 'country', 'note']
    readonly_fields = ['created_at', 'updated_at']
