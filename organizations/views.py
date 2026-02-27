"""
Organizations API Views
"""
from django.db import models
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsHRAdmin
from .models import Entity, Location, Department
from .serializers import (
    EntitySerializer,
    EntityCreateSerializer,
    EntityUpdateSerializer
)
from .services import (
    get_entity_delete_impact,
    soft_delete_entity_cascade
)


class EntityListView(generics.ListAPIView):
    """List all entities"""
    permission_classes = [IsAuthenticated]
    serializer_class = EntitySerializer

    def get_queryset(self):
        return Entity.objects.filter(is_active=True)


class LocationListView(APIView):
    """List locations filtered by entity"""
    permission_classes = [IsAuthenticated]

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
    """List departments filtered by entity and/or location"""
    permission_classes = [IsAuthenticated]

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


class EntityCreateView(generics.GenericAPIView):
    """Create new Entity (HR/Admin only)"""
    permission_classes = [IsAuthenticated, IsHRAdmin]
    serializer_class = EntityCreateSerializer

    def post(self, request, *args, **kwargs):
        import json

        # Store locations and entity_wide_departments before serializer processes request.data
        locations = request.data.get('locations', [])
        entity_wide_departments = request.data.get('entity_wide_departments', [])

        # If locations/departments are strings (JSON), parse them
        if isinstance(locations, str):
            locations = json.loads(locations)
        if isinstance(entity_wide_departments, str):
            entity_wide_departments = json.loads(entity_wide_departments)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.save()

        # Track created locations for department assignment
        created_locations = []

        # Handle locations with their departments
        for location in locations:
            if location and isinstance(location, dict) and location.get('name') and location.get('name').strip():
                loc = Location.objects.create(
                    entity=entity,
                    location_name=location['name'].strip(),
                    city=location.get('city', 'HQ').strip(),
                    country=location.get('country', 'USA').strip(),
                    timezone=location.get('timezone', 'America/New_York'),
                    is_active=True
                )
                created_locations.append(loc)

                # Handle departments for this location
                location_departments = location.get('departments', [])
                for department in location_departments:
                    if department and isinstance(department, dict) and department.get('name') and department.get('name').strip():
                        dept_code = department.get('code', '').strip().upper()
                        if not dept_code:
                            dept_code = department['name'].strip()[:4].upper()
                        Department.objects.create(
                            entity=entity,
                            department_name=department['name'].strip(),
                            code=dept_code,
                            location=loc,
                            is_active=True
                        )

        # Handle entity-wide departments (no location assignment)
        for department in entity_wide_departments:
            if department and isinstance(department, dict) and department.get('name') and department.get('name').strip():
                dept_code = department.get('code', '').strip().upper()
                if not dept_code:
                    dept_code = department['name'].strip()[:4].upper()
                Department.objects.create(
                    entity=entity,
                    department_name=department['name'].strip(),
                    code=dept_code,
                    location=None,
                    is_active=True
                )

        # Return full entity data
        response_serializer = EntitySerializer(entity)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class EntityUpdateView(generics.GenericAPIView):
    """Update Entity (HR/Admin only)"""
    permission_classes = [IsAuthenticated, IsHRAdmin]
    serializer_class = EntityUpdateSerializer

    def patch(self, request, *args, **kwargs):
        import json

        entity_id = kwargs.get('pk')
        try:
            entity = Entity.objects.get(id=entity_id)
        except Entity.DoesNotExist:
            return Response(
                {'error': 'Entity not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Store locations and entity_wide_departments before serializer processes request.data
        locations = request.data.get('locations', [])
        entity_wide_departments = request.data.get('entity_wide_departments', [])

        # If locations/departments are strings (JSON), parse them
        if isinstance(locations, str):
            locations = json.loads(locations)
        if isinstance(entity_wide_departments, str):
            entity_wide_departments = json.loads(entity_wide_departments)

        serializer = self.get_serializer(entity, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        entity = serializer.save()

        # Track location IDs for department assignment
        location_id_map = {}  # Maps index (1-based) to location ID

        # Handle locations with their departments
        for idx, location in enumerate(locations, start=1):
            if location and isinstance(location, dict) and location.get('name') and location.get('name').strip():
                loc_id = location.get('id')

                if loc_id:
                    # Update existing location
                    try:
                        loc = Location.objects.get(id=loc_id, entity=entity)
                        loc.location_name = location['name'].strip()
                        loc.city = location.get('city', 'HQ').strip()
                        loc.country = location.get('country', 'USA').strip()
                        loc.timezone = location.get('timezone', 'America/New_York')
                        loc.save()
                        location_id_map[idx] = loc
                    except Location.DoesNotExist:
                        # ID doesn't exist, create new
                        loc = Location.objects.create(
                            entity=entity,
                            location_name=location['name'].strip(),
                            city=location.get('city', 'HQ').strip(),
                            country=location.get('country', 'USA').strip(),
                            timezone=location.get('timezone', 'America/New_York'),
                            is_active=True
                        )
                        location_id_map[idx] = loc
                else:
                    # Create new location
                    loc = Location.objects.create(
                        entity=entity,
                        location_name=location['name'].strip(),
                        city=location.get('city', 'HQ').strip(),
                        country=location.get('country', 'USA').strip(),
                        timezone=location.get('timezone', 'America/New_York'),
                        is_active=True
                    )
                    location_id_map[idx] = loc

                # Handle departments for this location
                location_departments = location.get('departments', [])
                for department in location_departments:
                    if department and isinstance(department, dict) and department.get('name') and department.get('name').strip():
                        dept_code = department.get('code', '').strip().upper()
                        if not dept_code:
                            dept_code = department['name'].strip()[:4].upper()
                        Department.objects.create(
                            entity=entity,
                            department_name=department['name'].strip(),
                            code=dept_code,
                            location=location_id_map[idx],
                            is_active=True
                        )

        # Handle entity-wide departments (no location assignment)
        for department in entity_wide_departments:
            if department and isinstance(department, dict) and department.get('name') and department.get('name').strip():
                dept_code = department.get('code', '').strip().upper()
                if not dept_code:
                    dept_code = department['name'].strip()[:4].upper()
                Department.objects.create(
                    entity=entity,
                    department_name=department['name'].strip(),
                    code=dept_code,
                    location=None,
                    is_active=True
                )

        # Return full entity data
        response_serializer = EntitySerializer(entity)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class EntitySoftDeleteView(APIView):
    """Soft-delete Entity and cascade to Locations/Departments (HR/Admin only)"""
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def patch(self, request, *args, **kwargs):
        entity_id = kwargs.get('pk')

        try:
            result = soft_delete_entity_cascade(entity_id)
            return Response(result, status=status.HTTP_200_OK)
        except Entity.DoesNotExist:
            return Response(
                {'error': 'Entity not found or already inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class EntityDeleteImpactView(APIView):
    """Get deletion impact counts (HR/Admin only)"""
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def get(self, request, *args, **kwargs):
        entity_id = kwargs.get('pk')

        impact = get_entity_delete_impact(entity_id)
        if impact is None:
            return Response(
                {'error': 'Entity not found or already inactive'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(impact, status=status.HTTP_200_OK)
