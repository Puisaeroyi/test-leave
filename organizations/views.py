"""
Organizations API Views
"""
from django.db import models
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Entity, Location, Department


class EntityListView(generics.ListAPIView):
    """List all entities - public for registration"""
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        entities = Entity.objects.filter(is_active=True)
        data = [{
            'id': str(e.id),
            'entity_name': e.entity_name,
            'code': e.code,
            'is_active': e.is_active,
        } for e in entities]
        return Response(data)


class LocationListView(APIView):
    """List locations filtered by entity - public for registration"""
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        locations = Location.objects.filter(is_active=True)

        # Filter by entity if provided
        entity_id = request.query_params.get('entity_id')
        if entity_id:
            locations = locations.filter(entity_id=entity_id)

        data = [{
            'id': str(loc.id),
            'entity': str(loc.entity_id),
            'location_name': loc.location_name,
            'city': loc.city,
            'country': loc.country,
            'is_active': loc.is_active,
        } for loc in locations]
        return Response(data)


class DepartmentListView(APIView):
    """List departments filtered by entity and/or location - public for registration"""
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        departments = Department.objects.filter(is_active=True)

        # Filter by entity if provided
        entity_id = request.query_params.get('entity_id')
        if entity_id:
            departments = departments.filter(entity_id=entity_id)

        # Filter by location if provided - ONLY location-specific departments
        location_id = request.query_params.get('location_id')
        if location_id:
            departments = departments.filter(location_id=location_id)

        data = [{
            'id': str(dept.id),
            'entity': str(dept.entity_id),
            'location': str(dept.location_id) if dept.location_id else None,
            'department_name': dept.department_name,
            'code': dept.code,
            'is_active': dept.is_active,
        } for dept in departments]
        return Response(data)


class DepartmentManagerListView(generics.ListAPIView):
    """List department managers"""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({'message': 'Department manager list - coming in Phase 2'}, status=status.HTTP_501_NOT_IMPLEMENTED)
