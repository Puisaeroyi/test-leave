"""
Core API Views (Notifications)
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
