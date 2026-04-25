"""
Email service for leave request lifecycle notifications via SMTP.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

PENDING_PATH = "/manager"
MY_REQUESTS_PATH = "/dashboard"


def _send(subject, body, recipient):
    if not recipient:
        logger.warning("Email skipped: empty recipient (subject=%s)", subject)
        return
    try:
        send_mail(
            subject,
            body,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as e:
        logger.warning("Email send failed (subject=%s): %s", subject, e)


def send_leave_pending_email(approver, leave_request):
    """Email the approver when a leave request is submitted."""
    if not approver or not leave_request:
        return
    requester = leave_request.user
    requester_name = requester.get_full_name() or requester.email
    category = (
        leave_request.leave_category.category_name
        if leave_request.leave_category
        else "Leave"
    )
    subject = f"New Leave Request from {requester_name}"
    body = (
        f"A new leave request has been submitted:\n\n"
        f"Employee: {requester_name}\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n\n"
        f"View pending requests: {settings.FRONTEND_BASE_URL}{PENDING_PATH}"
    )
    _send(subject, body, approver.email)


def send_leave_approved_email(leave_request):
    """Email the requester when their leave request is approved."""
    if not leave_request:
        return
    user = leave_request.user
    category = (
        leave_request.leave_category.category_name
        if leave_request.leave_category
        else "Leave"
    )
    approver_name = (
        leave_request.approved_by.get_full_name()
        if leave_request.approved_by
        else "Your approver"
    )
    subject = "Leave Request Approved"
    body = (
        f"Your leave request has been approved:\n\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n"
        f"Approved by: {approver_name}\n\n"
        f"View your requests: {settings.FRONTEND_BASE_URL}{MY_REQUESTS_PATH}"
    )
    _send(subject, body, user.email)


def send_leave_rejected_email(leave_request):
    """Email the requester when their leave request is rejected."""
    if not leave_request:
        return
    user = leave_request.user
    category = (
        leave_request.leave_category.category_name
        if leave_request.leave_category
        else "Leave"
    )
    reason = (
        f"\nReason: {leave_request.rejection_reason}"
        if leave_request.rejection_reason
        else ""
    )
    subject = "Leave Request Rejected"
    body = (
        f"Your leave request has been rejected:\n\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}{reason}\n\n"
        f"View your requests: {settings.FRONTEND_BASE_URL}{MY_REQUESTS_PATH}"
    )
    _send(subject, body, user.email)
