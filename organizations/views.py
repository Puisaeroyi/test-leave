"""
Organizations API Views
"""
from django.db import models, transaction
from datetime import time
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsHRAdmin
from .models import Entity, Location, Department, WorkShift
from .serializers import (
    EntitySerializer,
    EntityCreateSerializer,
    EntityUpdateSerializer
)
from .services import (
    get_entity_delete_impact,
    soft_delete_entity_cascade
)


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


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
            'holiday_requires_leave': dept.holiday_requires_leave,
            'work_shifts': [{
                'id': str(shift.id),
                'name': shift.name,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'includes_weekends': shift.includes_weekends,
            } for shift in dept.work_shifts.filter(is_active=True)],
            'is_active': dept.is_active,
        } for dept in departments]
        return Response(data)


class WorkShiftListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def get(self, request):
        shifts = WorkShift.objects.filter(is_active=True).select_related('department__entity')
        department_id = request.query_params.get('department_id')
        if department_id:
            shifts = shifts.filter(department_id=department_id)
        return Response([{
            'id': str(shift.id),
            'department_id': str(shift.department_id),
            'department_name': shift.department.department_name,
            'entity_name': shift.department.entity.entity_name,
            'name': shift.name,
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'includes_weekends': shift.includes_weekends,
        } for shift in shifts])

    def post(self, request):
        try:
            name = request.data['name'].strip()
            if not name:
                return Response({'name': ['Shift name is required.']}, status=status.HTTP_400_BAD_REQUEST)
            start_hour, start_minute = map(int, request.data['start_time'].split(':'))
            end_hour, end_minute = map(int, request.data['end_time'].split(':'))
            start_time = time(start_hour, start_minute)
            end_time = time(end_hour, end_minute)
        except (KeyError, ValueError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        includes_weekends = _parse_bool(request.data.get('includes_weekends', False))

        if _parse_bool(request.data.get('apply_to_all_departments')):
            entity = Entity.objects.filter(id=request.data.get('entity_id'), is_active=True).first()
            if not entity:
                return Response({'error': 'Entity not found'}, status=status.HTTP_404_NOT_FOUND)
            departments = list(entity.departments.filter(is_active=True))
            if not departments:
                return Response({'error': 'Entity has no active departments'}, status=status.HTTP_400_BAD_REQUEST)
            created, skipped = 0, []
            with transaction.atomic():
                for department in departments:
                    # Skip departments that already define this shift name instead of failing the batch
                    if WorkShift.objects.filter(department=department, name=name).exists():
                        skipped.append(department.department_name)
                        continue
                    WorkShift.objects.create(
                        department=department,
                        name=name,
                        start_time=start_time,
                        end_time=end_time,
                        includes_weekends=includes_weekends,
                    )
                    created += 1
            if not created:
                return Response(
                    {'name': ['A work shift with this name already exists in every department of this entity.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response({'created': created, 'skipped': skipped}, status=status.HTTP_201_CREATED)

        department = Department.objects.filter(id=request.data.get('department_id'), is_active=True).first()
        if not department:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)
        if WorkShift.objects.filter(department=department, name=name).exists():
            return Response(
                {'name': ['A work shift with this name already exists in the department.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        shift = WorkShift.objects.create(
            department=department,
            name=name,
            start_time=start_time,
            end_time=end_time,
            includes_weekends=includes_weekends,
        )
        return Response({'id': str(shift.id)}, status=status.HTTP_201_CREATED)


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
                            holiday_requires_leave=bool(department.get('holiday_requires_leave', False)),
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
                    holiday_requires_leave=bool(department.get('holiday_requires_leave', False)),
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
                        dept = Department.objects.filter(
                            id=department.get('id'), entity=entity
                        ).first() if department.get('id') else None
                        if dept:
                            dept.department_name = department['name'].strip()
                            dept.code = dept_code
                            dept.location = location_id_map[idx]
                            dept.holiday_requires_leave = bool(department.get('holiday_requires_leave', False))
                            dept.is_active = True
                            dept.save()
                        else:
                            Department.objects.create(
                                entity=entity,
                                department_name=department['name'].strip(),
                                code=dept_code,
                                location=location_id_map[idx],
                                holiday_requires_leave=bool(department.get('holiday_requires_leave', False)),
                                is_active=True
                            )

        # Handle entity-wide departments (no location assignment)
        for department in entity_wide_departments:
            if department and isinstance(department, dict) and department.get('name') and department.get('name').strip():
                dept_code = department.get('code', '').strip().upper()
                if not dept_code:
                    dept_code = department['name'].strip()[:4].upper()
                dept = Department.objects.filter(
                    id=department.get('id'), entity=entity
                ).first() if department.get('id') else None
                if dept:
                    dept.department_name = department['name'].strip()
                    dept.code = dept_code
                    dept.location = None
                    dept.holiday_requires_leave = bool(department.get('holiday_requires_leave', False))
                    dept.is_active = True
                    dept.save()
                else:
                    Department.objects.create(
                        entity=entity,
                        department_name=department['name'].strip(),
                        code=dept_code,
                        location=None,
                        holiday_requires_leave=bool(department.get('holiday_requires_leave', False)),
                        is_active=True
                    )

        from leaves.holiday_management import split_future_entity_calendars
        split_future_entity_calendars(entity, actor=request.user)

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
