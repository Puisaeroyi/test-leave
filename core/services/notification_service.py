"""
Notification service for creating notifications in the system.
Centralized notification creation logic.
"""
from django.urls import reverse
from core.models import Notification


# Notification types
LEAVE_PENDING = "LEAVE_PENDING"
LEAVE_APPROVED = "LEAVE_APPROVED"
LEAVE_REJECTED = "LEAVE_REJECTED"
LEAVE_CANCELLED = "LEAVE_CANCELLED"
LEAVE_UPDATED = "LEAVE_UPDATED"
BALANCE_ADJUSTED = "BALANCE_ADJUSTED"


def create_notification(user, notification_type, title, message, link="", related_object_id=None):
    """
    Create a notification for a user.

    Args:
        user: User instance to notify
        notification_type: Type of notification (LEAVE_PENDING, LEAVE_APPROVED, etc.)
        title: Notification title
        message: Notification message
        link: Optional link to related resource
        related_object_id: Optional ID of related object (e.g., leave_request.id)

    Returns:
        Notification instance
    """
    return Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        link=link,
        related_object_id=related_object_id,
    )


def create_leave_pending_notification(manager, leave_request):
    """Notify manager of new pending leave request from their team member."""
    user_name = leave_request.user.get_full_name() or leave_request.user.email
    category_name = leave_request.leave_category.category_name if leave_request.leave_category else "Leave"
    message = (
        f"{user_name} has requested {category_name} "
        f"from {leave_request.start_date} to {leave_request.end_date}"
    )
    # Link to pending requests page
    link = "/pending-requests"  # Frontend route
    return create_notification(
        user=manager,
        notification_type=LEAVE_PENDING,
        title="New Leave Request Pending Approval",
        message=message,
        link=link,
        related_object_id=leave_request.id,
    )


def create_leave_approved_notification(leave_request):
    """Notify employee that their leave request was approved."""
    category_name = leave_request.leave_category.category_name if leave_request.leave_category else "Leave"
    message = (
        f"Your {category_name} request "
        f"from {leave_request.start_date} to {leave_request.end_date} has been approved"
    )
    return create_notification(
        user=leave_request.user,
        notification_type=LEAVE_APPROVED,
        title="Leave Request Approved",
        message=message,
        link=f"/leave-requests/{leave_request.id}",
        related_object_id=leave_request.id,
    )


def create_leave_rejected_notification(leave_request):
    """Notify employee that their leave request was rejected."""
    category_name = leave_request.leave_category.category_name if leave_request.leave_category else "Leave"
    reason = f". Reason: {leave_request.rejection_reason}" if leave_request.rejection_reason else ""
    message = (
        f"Your {category_name} request "
        f"from {leave_request.start_date} to {leave_request.end_date} has been rejected{reason}"
    )
    return create_notification(
        user=leave_request.user,
        notification_type=LEAVE_REJECTED,
        title="Leave Request Rejected",
        message=message,
        link=f"/leave-requests/{leave_request.id}",
        related_object_id=leave_request.id,
    )


def create_leave_cancelled_notification(leave_request):
    """Notify that a leave request was cancelled."""
    category_name = leave_request.leave_category.category_name if leave_request.leave_category else "Leave"
    # If was approved, notify the manager who approved it
    if leave_request.approved_by:
        message = (
            f"{leave_request.user.get_full_name() or leave_request.user.email} "
            f"has cancelled their approved {category_name} request "
            f"from {leave_request.start_date} to {leave_request.end_date}"
        )
        return create_notification(
            user=leave_request.approved_by,
            notification_type=LEAVE_CANCELLED,
            title="Leave Request Cancelled",
            message=message,
            link=f"/leave-requests/{leave_request.id}",
            related_object_id=leave_request.id,
        )
    else:
        # Notify the employee their pending request was cancelled
        message = (
            f"Your {category_name} request "
            f"from {leave_request.start_date} to {leave_request.end_date} has been cancelled"
        )
        return create_notification(
            user=leave_request.user,
            notification_type=LEAVE_CANCELLED,
            title="Leave Request Cancelled",
            message=message,
            link=f"/leave-requests/{leave_request.id}",
            related_object_id=leave_request.id,
        )


def create_balance_adjusted_notification(user, adjustment_amount, year):
    """Notify user that their leave balance was adjusted."""
    action = "increased" if adjustment_amount > 0 else "decreased"
    message = (
        f"Your leave balance for {year} has been {action} by {abs(adjustment_amount)} hours"
    )
    return create_notification(
        user=user,
        notification_type=BALANCE_ADJUSTED,
        title="Leave Balance Adjusted",
        message=message,
        link=f"/balance?year={year}",
    )


FRIENDLY_LEAVE_FIELD_LABELS = {
    'leave_category': 'Leave type',
    'start_date': 'Start date',
    'end_date': 'End date',
    'shift_type': 'Shift type',
    'start_time': 'Start time',
    'end_time': 'End time',
    'start_day_offset': 'Start day offset',
    'end_day_offset': 'End day offset',
    'total_hours': 'Total hours',
    'reason': 'Reason',
    'attachment_url': 'Attachment',
}


def create_leave_updated_notification(approver, leave_request, changed_fields):
    """Notify a snapshotted approver that a pending leave request was updated."""
    if not approver or not leave_request:
        return None
    user_name = leave_request.user.get_full_name() or leave_request.user.email
    category_name = (
        leave_request.leave_category.category_name
        if leave_request.leave_category
        else "Leave"
    )
    field_labels = [
        FRIENDLY_LEAVE_FIELD_LABELS.get(f, f.replace('_', ' ').title())
        for f in changed_fields
        if f != 'total_hours'
    ]
    changed_text = ', '.join(field_labels) if field_labels else 'details'
    message = (
        f"{user_name} updated their {category_name} request "
        f"({leave_request.start_date} to {leave_request.end_date}): {changed_text}"
    )
    return create_notification(
        user=approver,
        notification_type=LEAVE_UPDATED,
        title="Leave Request Updated",
        message=message,
        link="/manager",
        related_object_id=leave_request.id,
    )
