"""
Organizations API Views
"""
import uuid

from django.db import transaction
from datetime import time
from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsHRAdmin
from users.models import User
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


def _parse_cycle_days(value):
    if value in (None, ''):
        return []
    if isinstance(value, list):
        return value
    return []


def _parse_optional_time(value):
    if not value:
        return None
    hour, minute = map(int, value.split(':'))
    return time(hour, minute)


def _serialize_shift(shift):
    return {
        'id': str(shift.id),
        'management_group_id': str(shift.management_group_id),
        'department_id': str(shift.department_id),
        'department_name': shift.department.department_name,
        'entity_id': str(shift.department.entity_id),
        'entity_name': shift.department.entity.entity_name,
        'location_name': shift.department.location.location_name if shift.department.location else 'Entity-wide',
        'name': shift.name,
        'pattern_type': shift.pattern_type,
        'start_time': shift.start_time.strftime('%H:%M'),
        'end_time': shift.end_time.strftime('%H:%M'),
        'break_start_time': (
            shift.break_start_time.strftime('%H:%M')
            if shift.break_start_time else None
        ),
        'break_end_time': (
            shift.break_end_time.strftime('%H:%M')
            if shift.break_end_time else None
        ),
        'includes_weekends': shift.includes_weekends,
        'cycle_days': shift.cycle_days,
    }


def _department_queryset(user):
    departments = Department.objects.filter(is_active=True).select_related('entity', 'location')
    if user.role == User.Role.HR:
        departments = departments.filter(entity_id=user.entity_id)
    return departments


def _assign_shift_to_unassigned_users(shift):
    users = User.objects.filter(
        department=shift.department,
        work_shift__isnull=True,
    )
    if shift.pattern_type == WorkShift.PatternType.ROTATING_CYCLE:
        users = users.filter(shift_cycle_start_date__isnull=False)
    return users.update(work_shift=shift)


def _create_shifts_for_departments(departments, shift_values):
    created = 0
    assigned_users = 0
    skipped = []
    management_group_id = uuid.uuid4()
    with transaction.atomic():
        for department in departments:
            if WorkShift.objects.filter(
                department=department,
                name=shift_values['name'],
            ).exists():
                skipped.append(department.department_name)
                continue
            shift = WorkShift.objects.create(
                department=department,
                management_group_id=management_group_id,
                **shift_values,
            )
            assigned_users += _assign_shift_to_unassigned_users(shift)
            created += 1
    return created, assigned_users, skipped


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
        departments = _department_queryset(request.user)

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
            'entity_name': dept.entity.entity_name,
            'location': str(dept.location_id) if dept.location_id else None,
            'location_name': dept.location.location_name if dept.location_id else None,
            'department_name': dept.department_name,
            'code': dept.code,
            'holiday_requires_leave': dept.holiday_requires_leave,
            'work_shifts': [{
                'id': str(shift.id),
                'name': shift.name,
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'break_start_time': (
                    shift.break_start_time.strftime('%H:%M')
                    if shift.break_start_time else None
                ),
                'break_end_time': (
                    shift.break_end_time.strftime('%H:%M')
                    if shift.break_end_time else None
                ),
                'includes_weekends': shift.includes_weekends,
            } for shift in dept.work_shifts.filter(is_active=True)],
            'is_active': dept.is_active,
        } for dept in departments]
        return Response(data)


class WorkShiftListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def get(self, request):
        shifts = WorkShift.objects.filter(is_active=True).select_related('department__entity')
        if request.user.role == User.Role.HR:
            shifts = shifts.filter(department__entity_id=request.user.entity_id)
        department_id = request.query_params.get('department_id')
        if department_id:
            shifts = shifts.filter(department_id=department_id)
        return Response([_serialize_shift(shift) for shift in shifts])

    def post(self, request):
        try:
            name = request.data['name'].strip()
            if not name:
                return Response({'name': ['Shift name is required.']}, status=status.HTTP_400_BAD_REQUEST)
            start_hour, start_minute = map(int, request.data['start_time'].split(':'))
            end_hour, end_minute = map(int, request.data['end_time'].split(':'))
            start_time_value = time(start_hour, start_minute)
            end_time_value = time(end_hour, end_minute)
            break_start_time = _parse_optional_time(request.data.get('break_start_time'))
            break_end_time = _parse_optional_time(request.data.get('break_end_time'))
        except (KeyError, ValueError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        includes_weekends = _parse_bool(request.data.get('includes_weekends', False))
        pattern_type = request.data.get('pattern_type') or WorkShift.PatternType.FIXED_WEEKLY
        if pattern_type not in WorkShift.PatternType.values:
            return Response({'pattern_type': ['Invalid pattern type.']}, status=status.HTTP_400_BAD_REQUEST)
        cycle_days = _parse_cycle_days(request.data.get('cycle_days'))

        shift_values = {
            'name': name,
            'start_time': start_time_value,
            'end_time': end_time_value,
            'break_start_time': break_start_time,
            'break_end_time': break_end_time,
            'pattern_type': pattern_type,
            'cycle_days': cycle_days,
            'includes_weekends': includes_weekends,
        }

        entity_ids = request.data.get('entity_ids')
        if entity_ids is not None:
            if not isinstance(entity_ids, list) or not entity_ids:
                return Response(
                    {'entity_ids': ['Select at least one entity.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            requested_ids = {str(entity_id) for entity_id in entity_ids}
            try:
                entities = Entity.objects.filter(id__in=requested_ids, is_active=True)
                if request.user.role == User.Role.HR:
                    entities = entities.filter(id=request.user.entity_id)
                selected_ids = {str(entity.id) for entity in entities}
            except (ValidationError, ValueError):
                selected_ids = set()
            if selected_ids != requested_ids:
                return Response({'error': 'Entity not found'}, status=status.HTTP_404_NOT_FOUND)
            departments = list(
                _department_queryset(request.user).filter(entity_id__in=selected_ids)
            )
            if not departments:
                return Response(
                    {'error': 'Selected entities have no active departments'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            created, assigned_users, skipped = _create_shifts_for_departments(
                departments,
                shift_values,
            )
            if not created:
                return Response(
                    {'name': ['A work shift with this name already exists in every department of the selected entities.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    'created': created,
                    'assigned_users': assigned_users,
                    'skipped': skipped,
                },
                status=status.HTTP_201_CREATED,
            )

        if _parse_bool(request.data.get('apply_to_all_departments')):
            entity = Entity.objects.filter(id=request.data.get('entity_id'), is_active=True).first()
            if request.user.role == User.Role.HR and entity and entity.id != request.user.entity_id:
                entity = None
            if not entity:
                return Response({'error': 'Entity not found'}, status=status.HTTP_404_NOT_FOUND)
            departments = list(entity.departments.filter(is_active=True))
            if not departments:
                return Response({'error': 'Entity has no active departments'}, status=status.HTTP_400_BAD_REQUEST)
            created, assigned_users, skipped = _create_shifts_for_departments(
                departments,
                shift_values,
            )
            if not created:
                return Response(
                    {'name': ['A work shift with this name already exists in every department of this entity.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    'created': created,
                    'assigned_users': assigned_users,
                    'skipped': skipped,
                },
                status=status.HTTP_201_CREATED,
            )

        department = _department_queryset(request.user).filter(id=request.data.get('department_id')).first()
        if not department:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)
        if WorkShift.objects.filter(department=department, name=name).exists():
            return Response(
                {'name': ['A work shift with this name already exists in the department.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            shift = WorkShift.objects.create(department=department, **shift_values)
            assigned_users = _assign_shift_to_unassigned_users(shift)
        response_data = _serialize_shift(shift)
        response_data['assigned_users'] = assigned_users
        return Response(response_data, status=status.HTTP_201_CREATED)


class WorkShiftDetailView(APIView):
    permission_classes = [IsAuthenticated, IsHRAdmin]

    def get_shift(self, request, pk):
        return WorkShift.objects.filter(
            id=pk,
            is_active=True,
            department__in=_department_queryset(request.user),
        ).select_related('department__entity', 'department__location').first()

    def get_group(self, request, shift):
        return WorkShift.objects.filter(
            management_group_id=shift.management_group_id,
            is_active=True,
            department__in=_department_queryset(request.user),
        )

    def patch(self, request, pk):
        shift = self.get_shift(request, pk)
        if not shift:
            return Response({'error': 'Work shift not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            if 'name' in request.data:
                shift.name = request.data['name'].strip()
                if not shift.name:
                    return Response({'name': ['Shift name is required.']}, status=status.HTTP_400_BAD_REQUEST)
            if 'start_time' in request.data:
                start_hour, start_minute = map(int, request.data['start_time'].split(':'))
                shift.start_time = time(start_hour, start_minute)
            if 'end_time' in request.data:
                end_hour, end_minute = map(int, request.data['end_time'].split(':'))
                shift.end_time = time(end_hour, end_minute)
            if 'break_start_time' in request.data:
                shift.break_start_time = _parse_optional_time(
                    request.data.get('break_start_time')
                )
            if 'break_end_time' in request.data:
                shift.break_end_time = _parse_optional_time(
                    request.data.get('break_end_time')
                )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        pattern_type = request.data.get('pattern_type')
        if pattern_type:
            if pattern_type not in WorkShift.PatternType.values:
                return Response({'pattern_type': ['Invalid pattern type.']}, status=status.HTTP_400_BAD_REQUEST)
            shift.pattern_type = pattern_type
        if 'cycle_days' in request.data:
            shift.cycle_days = _parse_cycle_days(request.data.get('cycle_days'))
        if 'includes_weekends' in request.data:
            shift.includes_weekends = _parse_bool(request.data.get('includes_weekends'))

        group = self.get_group(request, shift)
        group_ids = list(group.values_list('id', flat=True))
        desired_departments = list(
            _department_queryset(request.user).filter(
                id__in=group.values_list('department_id', flat=True),
            )
        )
        entity_ids = request.data.get('entity_ids')
        if entity_ids is not None:
            if not isinstance(entity_ids, list) or not entity_ids:
                return Response(
                    {'entity_ids': ['Select at least one entity.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            requested_ids = {str(entity_id) for entity_id in entity_ids}
            try:
                entities = Entity.objects.filter(id__in=requested_ids, is_active=True)
                if request.user.role == User.Role.HR:
                    entities = entities.filter(id=request.user.entity_id)
                selected_ids = {str(entity.id) for entity in entities}
            except (ValidationError, ValueError):
                selected_ids = set()
            if selected_ids != requested_ids:
                return Response({'error': 'Entity not found'}, status=status.HTTP_404_NOT_FOUND)
            desired_departments = list(
                _department_queryset(request.user).filter(entity_id__in=selected_ids)
            )
            if not desired_departments:
                return Response(
                    {'error': 'Selected entities have no active departments'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        desired_department_ids = {department.id for department in desired_departments}
        duplicate = WorkShift.objects.filter(
            department_id__in=desired_department_ids,
            name=shift.name,
            is_active=True,
        ).exclude(id__in=group_ids).exists()
        if duplicate:
            return Response(
                {'name': ['A work shift with this name already exists in the department.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        next_group_id = shift.management_group_id
        if WorkShift.objects.filter(
            management_group_id=shift.management_group_id,
            is_active=True,
        ).exclude(id__in=group_ids).exists():
            next_group_id = uuid.uuid4()

        shift_values = {
            'name': shift.name,
            'start_time': shift.start_time,
            'end_time': shift.end_time,
            'break_start_time': shift.break_start_time,
            'break_end_time': shift.break_end_time,
            'pattern_type': shift.pattern_type,
            'cycle_days': shift.cycle_days,
            'includes_weekends': shift.includes_weekends,
        }
        with transaction.atomic():
            members = list(group.select_for_update())
            retained_members = [
                member for member in members
                if member.department_id in desired_department_ids
            ]
            removed_members = [
                member for member in members
                if member.department_id not in desired_department_ids
            ]
            removed_ids = [member.id for member in removed_members]
            unassigned_users = User.objects.filter(
                work_shift_id__in=removed_ids,
            ).update(work_shift=None) if removed_ids else 0
            if removed_ids:
                WorkShift.objects.filter(id__in=removed_ids).update(is_active=False)

            assigned_users = 0
            for member in retained_members:
                member.management_group_id = next_group_id
                for field, value in shift_values.items():
                    setattr(member, field, value)
                member.save()
                assigned_users += _assign_shift_to_unassigned_users(member)

            existing_department_ids = {member.department_id for member in members}
            missing_departments = [
                department for department in desired_departments
                if department.id not in existing_department_ids
            ]
            created_members = []
            for department in missing_departments:
                member = WorkShift.objects.create(
                    department=department,
                    management_group_id=next_group_id,
                    **shift_values,
                )
                assigned_users += _assign_shift_to_unassigned_users(member)
                created_members.append(member)

        active_members = retained_members + created_members
        response_data = _serialize_shift(active_members[0])
        response_data.update({
            'updated': len(active_members),
            'added_departments': len(created_members),
            'removed_departments': len(removed_members),
            'assigned_users': assigned_users,
            'unassigned_users': unassigned_users,
        })
        return Response(response_data)

    def delete(self, request, pk):
        shift = self.get_shift(request, pk)
        if not shift:
            return Response({'error': 'Work shift not found'}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            self.get_group(request, shift).select_for_update().update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
