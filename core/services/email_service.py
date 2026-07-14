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


def _display_name(user):
    if not user:
        return ""
    return user.get_full_name() or user.email


def _branch_name(leave_request):
    if not leave_request or not leave_request.user.entity_id:
        return "Unknown Branch"
    entity_model = leave_request.user._meta.get_field("entity").remote_field.model
    return (
        entity_model.objects.filter(pk=leave_request.user.entity_id)
        .values_list("entity_name", flat=True)
        .first()
        or "Unknown Branch"
    )


def _category_name(leave_request):
    return (
        leave_request.leave_category.category_name
        if leave_request.leave_category
        else "Leave"
    )


def _leave_subject(leave_request, title, person=None):
    person_name = _display_name(person or leave_request.user)
    return f"[{_branch_name(leave_request)}] {title} - {person_name}"


def _review_required_subject(leave_request):
    requester_name = _display_name(leave_request.user)
    return f"[{_branch_name(leave_request)}] Review required: Leave request from {requester_name}"


def _approved_subject(leave_request):
    approvers = (
        leave_request.first_approver or leave_request.user.approver_1,
        leave_request.final_approver or leave_request.user.approver_2,
    )
    approver_names = [_display_name(approver) for approver in approvers if approver]
    return (
        f"[{_branch_name(leave_request)}] Leave request approved by "
        f"{' and '.join(approver_names)}"
    )


def _approval_progress(leave_request):
    steps = []
    step_definitions = (
        (
            leave_request.first_approver or leave_request.user.approver_1,
            leave_request.first_approval_status,
            leave_request.first_approval_comment,
        ),
        (
            leave_request.final_approver or leave_request.user.approver_2,
            leave_request.final_approval_status,
            leave_request.final_approval_comment,
        ),
    )
    for approver, status, comment in step_definitions:
        if not approver:
            continue
        if leave_request.status == "REJECTED" and status == "PENDING":
            status = "NOT_REQUIRED"
        display_status = {
            "APPROVED": "Approved",
            "REJECTED": "Declined",
            "PENDING": "Pending",
            "NOT_REQUIRED": "Not required",
        }.get(status, status.title() if status else "Pending")
        steps.append({
            "approver_name": _display_name(approver),
            "status": display_status,
            "comment": comment,
        })
    return steps


def _approved_by_names(approval_progress):
    return [
        step["approver_name"]
        for step in approval_progress
        if step["status"] == "Approved"
    ]


def _progress_text(approval_progress):
    lines = []
    for step in approval_progress:
        note = f" - Note: {step['comment']}" if step["comment"] else ""
        lines.append(
            f"{step['approver_name']} - {step['status']}{note}"
        )
    return "\n".join(lines)


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
        logger.info(
            "Email sent (subject=%s, recipient=%s)",
            subject,
            recipient,
        )
    except Exception as e:
        logger.warning("Email send failed (subject=%s): %s", subject, e)


def send_leave_pending_email(approver, leave_request):
    """Email the approver when a leave request is submitted."""
    if not approver or not leave_request:
        return
    requester = leave_request.user
    requester_name = _display_name(requester)
    category = _category_name(leave_request)
    pending_url = f"{settings.FRONTEND_BASE_URL}{PENDING_PATH}"

    subject = _review_required_subject(leave_request)
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


def send_leave_submitted_email(leave_request):
    """Email the requester after their leave request is submitted."""
    if not leave_request:
        return
    user = leave_request.user
    category = _category_name(leave_request)
    dashboard_url = f"{settings.FRONTEND_BASE_URL}{MY_REQUESTS_PATH}"

    subject = _leave_subject(leave_request, "Leave request submitted successfully")
    text_body = (
        f"Your leave request has been submitted successfully:\n\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n"
        f"Reason: {leave_request.reason or 'Not provided'}\n"
        f"Status: {leave_request.status}\n\n"
        f"View your requests: {dashboard_url}"
    )
    html_body = render_to_string("email/leave_submitted.html", {
        "employee_name": _display_name(user),
        "category": category,
        "start_date": leave_request.start_date,
        "end_date": leave_request.end_date,
        "reason": leave_request.reason,
        "status": leave_request.status,
        "dashboard_url": dashboard_url,
    })
    _send(subject, text_body, html_body, user.email)


def send_leave_approved_email(leave_request):
    """Email the requester when their leave request is approved."""
    if not leave_request:
        return
    user = leave_request.user
    category = _category_name(leave_request)
    approval_progress = _approval_progress(leave_request)
    approved_by_names = _approved_by_names(approval_progress)
    approved_by = " and ".join(approved_by_names) or "Your approver"
    progress_text = _progress_text(approval_progress)
    dashboard_url = f"{settings.FRONTEND_BASE_URL}{MY_REQUESTS_PATH}"

    subject = _approved_subject(leave_request)
    text_body = (
        f"Your leave request has been approved:\n\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n"
        f"Approved by: {approved_by}\n\n"
        f"Approval progress:\n{progress_text}\n\n"
        f"View your requests: {dashboard_url}"
    )
    html_body = render_to_string("email/leave_approved.html", {
        "category": category,
        "start_date": leave_request.start_date,
        "end_date": leave_request.end_date,
        "approved_by": approved_by,
        "approval_progress": approval_progress,
        "dashboard_url": dashboard_url,
    })
    _send(subject, text_body, html_body, user.email)


def send_leave_rejected_email(leave_request):
    """Email the requester when their leave request is rejected."""
    if not leave_request:
        return
    user = leave_request.user
    category = _category_name(leave_request)
    rejected_by_name = (
        _display_name(leave_request.approved_by)
        if leave_request.approved_by
        else "Your manager"
    )
    rejection_reason = (
        leave_request.rejection_reason
        if leave_request.rejection_reason
        else ""
    )
    dashboard_url = f"{settings.FRONTEND_BASE_URL}{MY_REQUESTS_PATH}"
    approval_progress = _approval_progress(leave_request)
    progress_text = _progress_text(approval_progress)

    subject = (
        f"[{_branch_name(leave_request)}] Leave request denied by "
        f"{rejected_by_name}"
    )
    reason_text = f"\nReason: {rejection_reason}" if rejection_reason else ""
    text_body = (
        f"Your leave request has been rejected:\n\n"
        f"Type: {category}\n"
        f"From: {leave_request.start_date}\n"
        f"To: {leave_request.end_date}\n"
        f"Rejected by: {rejected_by_name}{reason_text}\n\n"
        f"Approval progress:\n{progress_text}\n\n"
        f"View your requests: {dashboard_url}"
    )
    html_body = render_to_string("email/leave_rejected.html", {
        "category": category,
        "start_date": leave_request.start_date,
        "end_date": leave_request.end_date,
        "rejected_by_name": rejected_by_name,
        "rejection_reason": rejection_reason,
        "approval_progress": approval_progress,
        "dashboard_url": dashboard_url,
    })
    _send(subject, text_body, html_body, user.email)


def send_leave_updated_email(approver, request_snapshot, change_rows):
    """
    Email an approver after a material leave update.

    request_snapshot: immutable dict with employee_name, category, start_date,
    end_date, recipient_email (not ORM).
    change_rows: list of {field, before, after} display strings.
    """
    if not approver and not (request_snapshot or {}).get('recipient_email'):
        return
    recipient = (
        getattr(approver, 'email', None)
        if approver is not None
        else None
    ) or (request_snapshot or {}).get('recipient_email')
    if not recipient:
        logger.warning("Leave updated email skipped: empty recipient")
        return

    snapshot = request_snapshot or {}
    employee_name = snapshot.get('employee_name', 'Employee')
    category = snapshot.get('category', 'Leave')
    start_date = snapshot.get('start_date', '')
    end_date = snapshot.get('end_date', '')
    pending_url = f"{settings.FRONTEND_BASE_URL}{PENDING_PATH}"
    rows = change_rows or []

    subject = f"Leave Request Updated — {employee_name}"
    lines = [
        f"{employee_name} updated a leave request awaiting your approval.",
        f"Type: {category}",
        f"From: {start_date}",
        f"To: {end_date}",
        "",
        "Changed fields:",
    ]
    for row in rows:
        lines.append(f"- {row.get('field')}: {row.get('before')} → {row.get('after')}")
    lines.extend(["", f"View pending requests: {pending_url}"])
    text_body = "\n".join(lines)

    try:
        html_body = render_to_string("email/leave_updated.html", {
            "employee_name": employee_name,
            "category": category,
            "start_date": start_date,
            "end_date": end_date,
            "change_rows": rows,
            "pending_url": pending_url,
        })
    except Exception as e:
        logger.warning("Leave updated email template failed: %s", e)
        return

    _send(subject, text_body, html_body, recipient)


def send_leave_updated_email_safe(approver, request_snapshot, change_rows):
    """Callback-safe wrapper: never raise from post-commit email delivery."""
    try:
        send_leave_updated_email(approver, request_snapshot, change_rows)
    except Exception as e:
        logger.warning("Leave updated email callback failed: %s", e)
