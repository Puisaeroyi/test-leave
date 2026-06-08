"""
Core API Views (Notifications)
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from html.parser import HTMLParser
from html import escape
from .models import Announcement, Notification


class RichTextSanitizer(HTMLParser):
    """Small allow-list sanitizer for admin-authored announcement HTML."""
    allowed_tags = {
        'a', 'blockquote', 'br', 'div', 'em', 'figcaption', 'figure', 'h1', 'h2', 'h3', 'h4', 'hr', 'img',
        'li', 'ol', 'p', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr',
        'u', 'ul',
    }
    allowed_attrs = {
        'a': {'href', 'target', 'rel'},
        'img': {'src', 'alt'},
    }
    allowed_styles = {
        'color', 'background-color', 'font-weight', 'font-style', 'text-align',
        'text-decoration', 'margin-left', 'padding-left',
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag not in self.allowed_tags:
            return

        clean_attrs = []
        allowed_attrs = self.allowed_attrs.get(tag, set())
        for name, value in attrs:
            if value is None:
                continue
            if name == 'style':
                style = self.clean_style(value)
                if style:
                    clean_attrs.append((name, style))
            elif name in allowed_attrs and self.is_safe_attr(tag, name, value):
                clean_attrs.append((name, value))

        if tag == 'a' and not any(name == 'rel' for name, _ in clean_attrs):
            clean_attrs.append(('rel', 'noopener noreferrer'))

        attr_text = ''.join(f' {name}="{escape(value, quote=True)}"' for name, value in clean_attrs)
        self.output.append(f'<{tag}{attr_text}>')

    def handle_endtag(self, tag):
        if tag in {'script', 'style'} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in self.allowed_tags and tag not in {'br', 'hr', 'img'}:
            self.output.append(f'</{tag}>')

    def handle_data(self, data):
        if self.skip_depth:
            return
        self.output.append(escape(data))

    def clean_style(self, value):
        declarations = []
        for part in value.split(';'):
            if ':' not in part:
                continue
            prop, raw_val = part.split(':', 1)
            prop = prop.strip().lower()
            raw_val = raw_val.strip()
            if prop in self.allowed_styles and 'javascript:' not in raw_val.lower():
                declarations.append(f'{prop}: {raw_val}')
        return '; '.join(declarations)

    def is_safe_attr(self, tag, name, value):
        lowered = value.lower().strip()
        if name == 'href':
            return lowered.startswith(('http://', 'https://', 'mailto:', '/'))
        if tag == 'img' and name == 'src':
            return lowered.startswith(('data:image/', 'http://', 'https://', '/media/'))
        return True

    def get_html(self):
        return ''.join(self.output)


def sanitize_rich_text(value):
    sanitizer = RichTextSanitizer()
    sanitizer.feed(value or '')
    sanitizer.close()
    return sanitizer.get_html()


def serialize_announcement(announcement):
    """Return announcement fields used by the SPA."""
    now = timezone.now()
    is_expired = bool(announcement.expires_at and announcement.expires_at <= now)
    is_scheduled = bool(announcement.starts_at and announcement.starts_at > now)
    effective_is_active = announcement.is_active and not is_expired
    created_by_name = None
    if announcement.created_by:
        created_by_name = (
            f"{announcement.created_by.first_name or ''} {announcement.created_by.last_name or ''}".strip()
            or announcement.created_by.email
        )
    return {
        'id': str(announcement.id),
        'title': announcement.title,
        'body': announcement.body,
        'body_html': announcement.body_html,
        'is_active': effective_is_active,
        'starts_at': announcement.starts_at.isoformat() if announcement.starts_at else None,
        'expires_at': announcement.expires_at.isoformat() if announcement.expires_at else None,
        'is_expired': is_expired,
        'is_scheduled': is_scheduled,
        'created_by': announcement.created_by.email if announcement.created_by else None,
        'created_by_name': created_by_name,
        'created_at': announcement.created_at.isoformat(),
        'updated_at': announcement.updated_at.isoformat(),
    }


def is_admin(user):
    return user and user.is_authenticated and getattr(user, 'role', None) == 'ADMIN'


class AnnouncementListCreateView(generics.GenericAPIView):
    """List active announcements for users; allow admins to manage all."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        self.deactivate_expired_announcements()
        queryset = Announcement.objects.select_related('created_by').order_by('-created_at')
        include_inactive = str(
            self.request.query_params.get('include_inactive', '')
        ).lower() in {'1', 'true', 'yes'}
        if is_admin(self.request.user) and include_inactive:
            return queryset
        now = timezone.now()
        return queryset.filter(
            is_active=True,
        ).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now),
        )

    def deactivate_expired_announcements(self):
        Announcement.objects.filter(
            is_active=True,
            expires_at__isnull=False,
            expires_at__lte=timezone.now(),
        ).update(is_active=False)

    def get(self, request, *args, **kwargs):
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', 10))))
        except (ValueError, TypeError):
            page = 1
            page_size = 10

        paginator = Paginator(self.get_queryset(), page_size)
        page_obj = paginator.get_page(page)
        announcements = [serialize_announcement(item) for item in page_obj]
        return Response({
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': announcements,
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response(
                {'error': 'Only Admin can create announcements.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        title = str(request.data.get('title', '')).strip()
        body = str(request.data.get('body', '')).strip()
        body_html = sanitize_rich_text(str(request.data.get('body_html', '')).strip())
        is_active_value = request.data.get('is_active', True)
        starts_at = self.parse_datetime_value(request.data.get('starts_at'))
        expires_at = self.parse_datetime_value(request.data.get('expires_at'))
        if not title:
            return Response({'title': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if not body:
            return Response({'body': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if expires_at and starts_at and expires_at <= starts_at:
            return Response({'expires_at': ['End time must be after start time.']}, status=status.HTTP_400_BAD_REQUEST)

        announcement = Announcement.objects.create(
            title=title,
            body=body,
            body_html=body_html,
            is_active=bool(is_active_value),
            starts_at=starts_at,
            expires_at=expires_at,
            created_by=request.user,
        )
        return Response(serialize_announcement(announcement), status=status.HTTP_201_CREATED)

    def parse_datetime_value(self, value):
        if not value:
            return None
        parsed = timezone.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed


class AnnouncementDetailView(generics.GenericAPIView):
    """Admin-only update/delete for announcements."""
    permission_classes = [IsAuthenticated]

    def get_announcement(self, pk):
        try:
            return Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return None

    def patch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response(
                {'error': 'Only Admin can update announcements.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        announcement = self.get_announcement(kwargs.get('pk'))
        if not announcement:
            return Response({'error': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)

        if 'title' in request.data:
            title = str(request.data.get('title', '')).strip()
            if not title:
                return Response({'title': ['This field may not be blank.']}, status=status.HTTP_400_BAD_REQUEST)
            announcement.title = title
        if 'body' in request.data:
            body = str(request.data.get('body', '')).strip()
            if not body:
                return Response({'body': ['This field may not be blank.']}, status=status.HTTP_400_BAD_REQUEST)
            announcement.body = body
        if 'body_html' in request.data:
            announcement.body_html = sanitize_rich_text(str(request.data.get('body_html', '')).strip())
        if 'starts_at' in request.data:
            announcement.starts_at = self.parse_datetime_value(request.data.get('starts_at'))
        if 'expires_at' in request.data:
            announcement.expires_at = self.parse_datetime_value(request.data.get('expires_at'))
        if announcement.expires_at and announcement.starts_at and announcement.expires_at <= announcement.starts_at:
            return Response({'expires_at': ['End time must be after start time.']}, status=status.HTTP_400_BAD_REQUEST)
        if 'is_active' in request.data:
            announcement.is_active = bool(request.data.get('is_active'))
        announcement.save()

        return Response(serialize_announcement(announcement), status=status.HTTP_200_OK)

    def parse_datetime_value(self, value):
        if not value:
            return None
        parsed = timezone.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

    def delete(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response(
                {'error': 'Only Admin can delete announcements.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        announcement = self.get_announcement(kwargs.get('pk'))
        if not announcement:
            return Response({'error': 'Announcement not found'}, status=status.HTTP_404_NOT_FOUND)

        announcement.delete()
        return Response({'deleted': True}, status=status.HTTP_200_OK)


class NotificationListView(generics.GenericAPIView):
    """List user notifications with pagination"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Return paginated list of user's notifications"""
        # Get query parameters with safe parsing
        is_read = request.query_params.get('is_read')
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
        except (ValueError, TypeError):
            page = 1
            page_size = 20

        # Get base queryset
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

        # Filter by read status if provided
        if is_read is not None:
            notifications = notifications.filter(is_read=is_read.lower() == 'true')

        # Paginate
        paginator = Paginator(notifications, page_size)
        page_obj = paginator.get_page(page)

        # Count unread
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        # Serialize results
        results = []
        for notification in page_obj:
            results.append({
                'id': str(notification.id),
                'type': notification.type,
                'title': notification.title,
                'message': notification.message,
                'link': notification.link,
                'related_object_id': str(notification.related_object_id) if notification.related_object_id else None,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat()
            })

        return Response({
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'unread_count': unread_count,
            'results': results
        }, status=status.HTTP_200_OK)


class NotificationMarkReadView(generics.GenericAPIView):
    """Mark a notification as read or delete it"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        """Mark specific notification as read"""
        notification_id = kwargs.get('pk')

        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()

            return Response({
                'id': str(notification.id),
                'is_read': True
            }, status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response({
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        """Delete a specific notification"""
        notification_id = kwargs.get('pk')

        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.delete()

            return Response({
                'deleted': True
            }, status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response({
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)


class NotificationMarkAllReadView(generics.GenericAPIView):
    """Mark all notifications as read"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Mark all unread notifications as read for current user"""
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)


class NotificationDismissAllView(generics.GenericAPIView):
    """Delete all notifications for current user"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        """Delete all notifications for current user"""
        deleted_count, _ = Notification.objects.filter(user=request.user).delete()

        return Response({
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)


class NotificationUnreadCountView(generics.GenericAPIView):
    """Get unread notification count"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Return count of unread notifications"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({
            'count': count
        }, status=status.HTTP_200_OK)
