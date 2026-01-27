"""
Organizations API Views
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Entity, Location, Department


class EntityListView(generics.ListAPIView):
    """List all entities"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        entities = Entity.objects.filter(is_active=True)
        data = [{
            'id': str(e.id),
            'name': e.name,
            'code': e.code,
        } for e in entities]
        return Response({'results': data})


class LocationListView(APIView):
    """List locations filtered by entity"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        locations = Location.objects.filter(is_active=True)

        # Filter by entity if provided
        entity_id = request.query_params.get('entity')
        if entity_id:
            locations = locations.filter(entity_id=entity_id)

        data = [{
            'id': str(loc.id),
            'name': loc.name,
            'city': loc.city,
            'state': loc.state,
            'country': loc.country,
            'timezone': loc.timezone,
            'entity_id': str(loc.entity_id),
        } for loc in locations]
        return Response({'results': data})


class DepartmentListView(APIView):
    """List departments filtered by entity"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        departments = Department.objects.filter(is_active=True)

        # Filter by entity if provided
        entity_id = request.query_params.get('entity')
        if entity_id:
            departments = departments.filter(entity_id=entity_id)

        data = [{
            'id': str(dept.id),
            'name': dept.name,
            'code': dept.code,
            'entity_id': str(dept.entity_id),
        } for dept in departments]
        return Response({'results': data})


class DepartmentManagerListView(generics.ListAPIView):
    """List department managers"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({'message': 'Department manager list - coming in Phase 2'}, status=status.HTTP_501_NOT_IMPLEMENTED)
