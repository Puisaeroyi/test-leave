"""
Email service for leave request lifecycle notifications via SMTP.
"""
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

PENDING_PATH = "/manager"
MY_REQUESTS_PATH = "/dashboard"


def _send(subject, text_body, html_body, recipient):
    if not recipient:
        logger.warning("Email skipped: empty recipient (subject=%s)", subject)
        return
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
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
    pending_url = f"{settings.FRONTEND_BASE_URL}{PENDING_PATH}"

    subject = f"New Leave Request from {requester_name}"
    text_body = (
        f"A new leave request has been submitted:\n\n"
        f"Employee: {requester_name}\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n\n"
        f"View pending requests: {pending_url}"
    )
    html_body = render_to_string("email/leave_pending.html", {
        "employee_name": requester_name,
        "category": category,
        "start_date": leave_request.start_date,
        "end_date": leave_request.end_date,
        "pending_url": pending_url,
    })
    _send(subject, text_body, html_body, approver.email)


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
    dashboard_url = f"{settings.FRONTEND_BASE_URL}{MY_REQUESTS_PATH}"

    subject = "Leave Request Approved"
    text_body = (
        f"Your leave request has been approved:\n\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n"
        f"Approved by: {approver_name}\n\n"
        f"View your requests: {dashboard_url}"
    )
    html_body = render_to_string("email/leave_approved.html", {
        "category": category,
        "start_date": leave_request.start_date,
        "end_date": leave_request.end_date,
        "approver_name": approver_name,
        "dashboard_url": dashboard_url,
    })
    _send(subject, text_body, html_body, user.email)


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
    rejected_by_name = (
        leave_request.approved_by.get_full_name()
        if leave_request.approved_by
        else "Your manager"
    )
    rejection_reason = (
        leave_request.rejection_reason
        if leave_request.rejection_reason
        else ""
    )
    dashboard_url = f"{settings.FRONTEND_BASE_URL}{MY_REQUESTS_PATH}"

    subject = "Leave Request Rejected"
    reason_text = f"\nReason: {rejection_reason}" if rejection_reason else ""
    text_body = (
        f"Your leave request has been rejected:\n\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n"
        f"Rejected by: {rejected_by_name}{reason_text}\n\n"
        f"View your requests: {dashboard_url}"
    )
    html_body = render_to_string("email/leave_rejected.html", {
        "category": category,
        "start_date": leave_request.start_date,
        "end_date": leave_request.end_date,
        "rejected_by_name": rejected_by_name,
        "rejection_reason": rejection_reason,
        "dashboard_url": dashboard_url,
    })
    _send(subject, text_body, html_body, user.email)
