"""
Core API Views (Notifications, Audit Logs)
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from .models import Notification


class NotificationListView(generics.GenericAPIView):
    """List user notifications with pagination"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Return paginated list of user's notifications"""
        # Get query parameters
        is_read = request.query_params.get('is_read')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

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
    """Mark a notification as read"""
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


class NotificationUnreadCountView(generics.GenericAPIView):
    """Get unread notification count"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Return count of unread notifications"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({
            'count': count
        }, status=status.HTTP_200_OK)


class AuditLogListView(generics.ListAPIView):
    """List audit logs (Admin only)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/notifications/audit-logs/?entity_type=LeaveRequest"""
        from .models import AuditLog

        # Check Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can view audit logs'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get filters
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')
        user_id = request.query_params.get('user_id')
        action = request.query_params.get('action')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))

        # Build queryset
        queryset = AuditLog.objects.all().order_by('-created_at')

        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)

        queryset = queryset.select_related('user')

        # Paginate
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = queryset[start:end]

        results = [
            {
                'id': str(log.id),
                'user_id': str(log.user_id),
                'user_email': log.user.email,
                'action': log.action,
                'entity_type': log.entity_type,
                'entity_id': str(log.entity_id),
                'old_values': log.old_values,
                'new_values': log.new_values,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat()
            }
            for log in items
        ]

        return Response({
            'count': total,
            'next': page + 1 if end < total else None,
            'previous': page - 1 if page > 1 else None,
            'results': results
        })
