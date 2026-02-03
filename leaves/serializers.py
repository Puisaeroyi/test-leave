"""
Leave Management Serializers
"""
from rest_framework import serializers
from decimal import Decimal
from .models import LeaveCategory, LeaveBalance, LeaveRequest, PublicHoliday, BusinessTrip


class LeaveCategorySerializer(serializers.ModelSerializer):
    """Serializer for LeaveCategory"""

    class Meta:
        model = LeaveCategory
        fields = ['id', 'category_name', 'code', 'requires_document', 'sort_order', 'is_active']
        read_only_fields = ['id']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for LeaveBalance"""
    remaining_hours = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'user', 'year', 'allocated_hours', 'used_hours',
            'adjusted_hours', 'remaining_hours', 'remaining_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_remaining_hours(self, obj):
        """Calculate remaining hours"""
        return float(obj.remaining_hours)

    def get_remaining_days(self, obj):
        """Calculate remaining days (8 hours per day)"""
        return float(obj.remaining_hours) / 8


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for LeaveRequest (read/list)"""
    category = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_timezone = serializers.SerializerMethodField()
    user_location_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    total_hours = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'user', 'user_name', 'user_email', 'user_timezone', 'user_location_name',
            'department_name', 'leave_category', 'category', 'start_date', 'end_date', 'shift_type',
            'start_time', 'end_time', 'total_hours', 'reason',
            'attachment_url', 'status', 'approved_by', 'approved_by_name',
            'approved_at', 'rejection_reason', 'approver_comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_hours', 'approved_by', 'approved_at', 'created_at', 'updated_at']

    def get_total_hours(self, obj):
        """Return total hours as float"""
        return float(obj.total_hours)

    def get_category(self, obj):
        """Get category details"""
        if obj.leave_category:
            return {
                'id': str(obj.leave_category.id),
                'name': obj.leave_category.category_name,
                'code': obj.leave_category.code
            }
        return None

    def get_user_name(self, obj):
        """Get user full name"""
        return f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip() or obj.user.email

    def get_user_email(self, obj):
        """Get user email"""
        return obj.user.email

    def get_user_timezone(self, obj):
        """Get user's location timezone as GMT offset label (e.g., GMT+9)"""
        if obj.user.location and obj.user.location.timezone:
            from datetime import datetime
            import zoneinfo
            try:
                tz = zoneinfo.ZoneInfo(obj.user.location.timezone)
                # Get current offset
                offset = datetime.now(tz).strftime('%z')  # e.g., +0900
                hours = int(offset[:3])
                mins = int(offset[0] + offset[3:5]) if offset[3:5] != '00' else 0
                if mins:
                    return f"GMT{hours:+d}:{abs(mins):02d}"
                return f"GMT{hours:+d}"
            except Exception:
                return None
        return None

    def get_user_location_name(self, obj):
        """Get user's location name"""
        if obj.user.location:
            return obj.user.location.location_name
        return None

    def get_department_name(self, obj):
        """Get user's department name"""
        if obj.user.department:
            return obj.user.department.department_name
        return None

    def get_approved_by_name(self, obj):
        """Get approver name"""
        if obj.approved_by:
            return f"{obj.approved_by.first_name or ''} {obj.approved_by.last_name or ''}".strip() or obj.approved_by.email
        return None


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating LeaveRequest"""
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'leave_category', 'category_name', 'start_date', 'end_date',
            'shift_type', 'start_time', 'end_time', 'reason', 'attachment_url'
        ]

    def get_category_name(self, obj):
        """Get category name"""
        if obj.leave_category:
            return obj.leave_category.category_name
        return None


class LeaveRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating LeaveRequest"""

    class Meta:
        model = LeaveRequest
        fields = [
            'leave_category', 'start_date', 'end_date', 'shift_type',
            'start_time', 'end_time', 'reason', 'attachment_url'
        ]


class PublicHolidaySerializer(serializers.ModelSerializer):
    """Serializer for PublicHoliday (supports multi-day holidays)"""
    entity_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = PublicHoliday
        fields = [
            'id', 'entity', 'entity_name', 'location', 'location_name',
            'holiday_name', 'start_date', 'end_date', 'is_recurring', 'year', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_entity_name(self, obj):
        """Get entity name"""
        return obj.entity.entity_name if obj.entity else None

    def get_location_name(self, obj):
        """Get location name"""
        return obj.location.location_name if obj.location else None


class LeaveRequestApproveSerializer(serializers.Serializer):
    """Serializer for approve action"""
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class LeaveRequestRejectSerializer(serializers.Serializer):
    """Serializer for reject action"""
    reason = serializers.CharField(
        required=True,
        min_length=10,
        max_length=1000,
        error_messages={'min_length': 'Rejection reason must be at least 10 characters'}
    )


class BusinessTripSerializer(serializers.ModelSerializer):
    """Serializer for BusinessTrip (read)"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = BusinessTrip
        fields = [
            'id', 'user', 'user_name', 'user_email', 'city', 'country',
            'start_date', 'end_date', 'note', 'attachment_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        """Get user full name"""
        return f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip() or obj.user.email

    def get_user_email(self, obj):
        """Get user email"""
        return obj.user.email


class BusinessTripCreateSerializer(serializers.Serializer):
    """Serializer for creating business trip"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    city = serializers.CharField(
        required=True,
        max_length=100,
        error_messages={'required': 'City is required'}
    )
    country = serializers.CharField(
        required=True,
        max_length=100,
        error_messages={'required': 'Country is required'}
    )
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    attachment_url = serializers.URLField(required=False, allow_blank=True, max_length=500)
