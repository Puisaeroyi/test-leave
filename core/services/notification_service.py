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
BALANCE_ADJUSTED = "BALANCE_ADJUSTED"


def create_notification(user, notification_type, title, message, link=""):
    """
    Create a notification for a user.

    Args:
        user: User instance to notify
        notification_type: Type of notification (LEAVE_PENDING, LEAVE_APPROVED, etc.)
        title: Notification title
        message: Notification message
        link: Optional link to related resource

    Returns:
        Notification instance
    """
    return Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        link=link,
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
