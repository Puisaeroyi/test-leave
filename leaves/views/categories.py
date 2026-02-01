"""Leave category views."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import LeaveCategory


class LeaveCategoryListView(generics.ListAPIView):
    """List leave categories."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/categories/"""
        categories = LeaveCategory.objects.filter(is_active=True).order_by('sort_order')
        data = [
            {
                'id': str(cat.id),
                'name': cat.category_name,
                'code': cat.code,
                'requires_document': cat.requires_document
            }
            for cat in categories
        ]
        return Response(data)
