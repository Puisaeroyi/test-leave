import pytest
from rest_framework.test import APIClient

from organizations.models import Department, Entity, Location, WorkShift
from users.models import User


@pytest.fixture
def work_shift_context(db):
    entity = Entity.objects.create(entity_name='Shift Company', code='SHIFT')
    location = Location.objects.create(
        entity=entity,
        location_name='Shift Office',
        city='Ho Chi Minh City',
        country='Vietnam',
        timezone='Asia/Ho_Chi_Minh',
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name='Operations',
        code='OPS',
    )
    admin = User.objects.create_user(
        email='shift-admin@example.com',
        password='AdminPass123!',
        role=User.Role.ADMIN,
        entity=entity,
        location=location,
        department=department,
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client, department


@pytest.mark.django_db
def test_create_and_list_work_shift(work_shift_context):
    client, department = work_shift_context

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(department.id),
        'name': 'Night Shift',
        'start_time': '22:00',
        'end_time': '06:00',
        'includes_weekends': True,
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    shift = WorkShift.objects.get(department=department, name='Night Shift')
    assert shift.includes_weekends is True

    response = client.get(
        '/api/v1/organizations/work-shifts/',
        {'department_id': str(department.id)},
        secure=True,
    )
    assert response.status_code == 200
    assert response.data[0]['name'] == 'Night Shift'
    assert response.data[0]['includes_weekends'] is True


@pytest.mark.django_db
def test_create_and_list_work_shift_with_break(work_shift_context):
    client, department = work_shift_context

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(department.id),
        'name': 'US Office',
        'start_time': '08:00',
        'end_time': '17:00',
        'break_start_time': '12:00',
        'break_end_time': '13:00',
        'includes_weekends': False,
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    assert response.data['break_start_time'] == '12:00'
    assert response.data['break_end_time'] == '13:00'
    shift = WorkShift.objects.get(department=department, name='US Office')
    assert shift.break_start_time.strftime('%H:%M') == '12:00'
    assert shift.break_end_time.strftime('%H:%M') == '13:00'


@pytest.mark.django_db
def test_create_and_list_rotating_work_shift(work_shift_context):
    client, department = work_shift_context
    cycle_days = [
        {'name': 'Morning', 'start_time': '06:00', 'end_time': '14:00', 'is_working': True},
        {'name': 'Evening', 'start_time': '14:00', 'end_time': '22:00', 'is_working': True},
        {'name': 'Night', 'start_time': '22:00', 'end_time': '06:00', 'is_working': True},
        {'name': 'Off', 'is_working': False},
    ]

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(department.id),
        'name': 'SOC Rotation',
        'pattern_type': WorkShift.PatternType.ROTATING_CYCLE,
        'start_time': '06:00',
        'end_time': '14:00',
        'includes_weekends': True,
        'cycle_days': cycle_days,
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    assert response.data['pattern_type'] == WorkShift.PatternType.ROTATING_CYCLE
    assert response.data['cycle_days'] == cycle_days
    shift = WorkShift.objects.get(department=department, name='SOC Rotation')
    assert shift.cycle_days == cycle_days


@pytest.mark.django_db
def test_create_work_shift_parses_false_string(work_shift_context):
    client, department = work_shift_context

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(department.id),
        'name': 'Day Shift',
        'start_time': '09:00',
        'end_time': '17:00',
        'includes_weekends': 'false',
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    shift = WorkShift.objects.get(department=department, name='Day Shift')
    assert shift.includes_weekends is False


@pytest.mark.django_db
def test_duplicate_work_shift_returns_validation_error(work_shift_context):
    client, department = work_shift_context
    WorkShift.objects.create(
        department=department,
        name='Night Shift',
        start_time='22:00',
        end_time='06:00',
    )

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(department.id),
        'name': 'Night Shift',
        'start_time': '21:00',
        'end_time': '05:00',
    }, format='json', secure=True)

    assert response.status_code == 400
    assert 'name' in response.data


@pytest.mark.django_db
def test_update_work_shift(work_shift_context):
    client, department = work_shift_context
    shift = WorkShift.objects.create(
        department=department,
        name='Day Shift',
        start_time='09:00',
        end_time='17:00',
    )

    response = client.patch(f'/api/v1/organizations/work-shifts/{shift.id}/', {
        'name': 'HR Night',
        'pattern_type': WorkShift.PatternType.FIXED_WEEKLY,
        'start_time': '22:00',
        'end_time': '06:00',
        'includes_weekends': False,
    }, format='json', secure=True)

    assert response.status_code == 200, response.data
    shift.refresh_from_db()
    assert shift.name == 'HR Night'
    assert shift.start_time.strftime('%H:%M') == '22:00'
    assert shift.end_time.strftime('%H:%M') == '06:00'
    assert response.data['name'] == 'HR Night'


@pytest.mark.django_db
def test_update_rotating_work_shift_cycle_times(work_shift_context):
    client, department = work_shift_context
    shift = WorkShift.objects.create(
        department=department,
        name='SOC Rotation',
        pattern_type=WorkShift.PatternType.ROTATING_CYCLE,
        start_time='06:00',
        end_time='14:00',
        includes_weekends=True,
        cycle_days=[
            {'name': 'Morning', 'start_time': '06:00', 'end_time': '14:00', 'is_working': True},
            {'name': 'Evening', 'start_time': '14:00', 'end_time': '22:00', 'is_working': True},
            {'name': 'Night', 'start_time': '22:00', 'end_time': '06:00', 'is_working': True},
            {'name': 'Off', 'is_working': False},
        ],
    )
    updated_days = [
        {'name': 'Morning', 'start_time': '07:00', 'end_time': '15:00', 'is_working': True},
        {'name': 'Evening', 'start_time': '15:00', 'end_time': '23:00', 'is_working': True},
        {'name': 'Night', 'start_time': '23:00', 'end_time': '07:00', 'is_working': True},
        {'name': 'Off', 'is_working': False},
    ]

    response = client.patch(f'/api/v1/organizations/work-shifts/{shift.id}/', {
        'name': 'SOC Rotation Updated',
        'pattern_type': WorkShift.PatternType.ROTATING_CYCLE,
        'start_time': '07:00',
        'end_time': '15:00',
        'includes_weekends': True,
        'cycle_days': updated_days,
    }, format='json', secure=True)

    assert response.status_code == 200, response.data
    shift.refresh_from_db()
    assert shift.cycle_days == updated_days
    assert response.data['cycle_days'] == updated_days


@pytest.mark.django_db
def test_delete_work_shift_soft_deactivates_and_hides_from_list(work_shift_context):
    client, department = work_shift_context
    shift = WorkShift.objects.create(
        department=department,
        name='Temporary Shift',
        start_time='09:00',
        end_time='17:00',
    )

    response = client.delete(f'/api/v1/organizations/work-shifts/{shift.id}/', secure=True)

    assert response.status_code == 204
    shift.refresh_from_db()
    assert shift.is_active is False

    response = client.get('/api/v1/organizations/work-shifts/', {'department_id': str(department.id)}, secure=True)
    assert response.status_code == 200
    assert all(item['id'] != str(shift.id) for item in response.data)


@pytest.mark.django_db
def test_apply_to_all_departments_creates_shift_entity_wide(work_shift_context):
    client, department = work_shift_context
    entity = department.entity
    unassigned_user = User.objects.create_user(
        email='entity-wide-unassigned@example.com',
        password='UserPass123!',
        entity=entity,
        location=department.location,
        department=department,
    )
    second = Department.objects.create(
        entity=entity,
        location=department.location,
        department_name='SOC',
        code='SOC',
    )
    entity_wide = Department.objects.create(
        entity=entity,
        location=None,
        department_name='Finance',
        code='FIN',
    )
    inactive = Department.objects.create(
        entity=entity,
        location=department.location,
        department_name='Closed',
        code='CLS',
        is_active=False,
    )

    response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_id': str(entity.id),
        'apply_to_all_departments': True,
        'name': '24/7 Coverage',
        'start_time': '00:00',
        'end_time': '23:59',
        'includes_weekends': True,
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    assert response.data['created'] == 3
    assert response.data['skipped'] == []
    for dept in (department, second, entity_wide):
        shift = WorkShift.objects.get(department=dept, name='24/7 Coverage')
        assert shift.includes_weekends is True
    unassigned_user.refresh_from_db()
    assert unassigned_user.work_shift == WorkShift.objects.get(
        department=department,
        name='24/7 Coverage',
    )
    assert not WorkShift.objects.filter(department=inactive).exists()


@pytest.mark.django_db
def test_apply_to_all_skips_departments_with_existing_name(work_shift_context):
    client, department = work_shift_context
    entity = department.entity
    second = Department.objects.create(
        entity=entity,
        location=department.location,
        department_name='SOC',
        code='SOC',
    )
    WorkShift.objects.create(
        department=department,
        name='Night Shift',
        start_time='22:00',
        end_time='06:00',
    )

    response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_id': str(entity.id),
        'apply_to_all_departments': True,
        'name': 'Night Shift',
        'start_time': '22:00',
        'end_time': '06:00',
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    assert response.data['created'] == 1
    assert response.data['skipped'] == ['Operations']
    assert WorkShift.objects.filter(department=second, name='Night Shift').exists()

    # Re-applying when every department already has the shift returns a validation error
    response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_id': str(entity.id),
        'apply_to_all_departments': True,
        'name': 'Night Shift',
        'start_time': '22:00',
        'end_time': '06:00',
    }, format='json', secure=True)
    assert response.status_code == 400
    assert 'name' in response.data


@pytest.mark.django_db
def test_apply_to_all_with_unknown_entity_returns_404(work_shift_context):
    client, _ = work_shift_context

    response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_id': '00000000-0000-0000-0000-000000000000',
        'apply_to_all_departments': True,
        'name': 'Ghost Shift',
        'start_time': '09:00',
        'end_time': '17:00',
    }, format='json', secure=True)

    assert response.status_code == 404


@pytest.mark.django_db
def test_create_work_shift_for_multiple_entities_assigns_only_unassigned_users(work_shift_context):
    client, first_department = work_shift_context
    existing_shift = WorkShift.objects.create(
        department=first_department,
        name='Existing Shift',
        start_time='09:00',
        end_time='17:00',
    )
    admin = User.objects.get(email='shift-admin@example.com')
    admin.work_shift = existing_shift
    admin.save(update_fields=['work_shift'])
    first_unassigned = User.objects.create_user(
        email='first-unassigned@example.com',
        password='UserPass123!',
        entity=first_department.entity,
        location=first_department.location,
        department=first_department,
    )
    first_assigned = User.objects.create_user(
        email='first-assigned@example.com',
        password='UserPass123!',
        entity=first_department.entity,
        location=first_department.location,
        department=first_department,
        work_shift=existing_shift,
    )
    second_entity = Entity.objects.create(entity_name='Second Shift Company', code='SHIFT2')
    second_location = Location.objects.create(
        entity=second_entity,
        location_name='Second Shift Office',
        city='New York',
        country='USA',
        timezone='America/New_York',
    )
    second_department = Department.objects.create(
        entity=second_entity,
        location=second_location,
        department_name='Support',
        code='SUP',
    )
    second_unassigned = User.objects.create_user(
        email='second-unassigned@example.com',
        password='UserPass123!',
        entity=second_entity,
        location=second_location,
        department=second_department,
    )

    response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_ids': [str(first_department.entity_id), str(second_entity.id)],
        'name': 'Shared Shift',
        'start_time': '08:00',
        'end_time': '16:00',
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    assert response.data == {'created': 2, 'assigned_users': 2, 'skipped': []}
    first_created = WorkShift.objects.get(department=first_department, name='Shared Shift')
    second_created = WorkShift.objects.get(department=second_department, name='Shared Shift')
    first_unassigned.refresh_from_db()
    first_assigned.refresh_from_db()
    second_unassigned.refresh_from_db()
    admin.refresh_from_db()
    assert first_unassigned.work_shift == first_created
    assert second_unassigned.work_shift == second_created
    assert first_assigned.work_shift == existing_shift
    assert admin.work_shift == existing_shift

    list_response = client.get('/api/v1/organizations/work-shifts/', secure=True)
    shared_rows = [item for item in list_response.data if item['name'] == 'Shared Shift']
    group_ids = {item.get('management_group_id') for item in shared_rows}
    assert None not in group_ids
    assert len(group_ids) == 1
    assert {item.get('entity_id') for item in shared_rows} == {
        str(first_department.entity_id),
        str(second_entity.id),
    }


@pytest.mark.django_db
def test_editing_one_group_member_updates_every_work_shift_in_group(work_shift_context):
    client, first_department = work_shift_context
    second_entity = Entity.objects.create(entity_name='Group Edit Company', code='GEDT')
    second_department = Department.objects.create(
        entity=second_entity,
        department_name='Support',
        code='SUP',
    )
    create_response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_ids': [str(first_department.entity_id), str(second_entity.id)],
        'name': 'Shared Editable Shift',
        'start_time': '08:00',
        'end_time': '16:00',
    }, format='json', secure=True)
    assert create_response.status_code == 201, create_response.data
    shifts = list(WorkShift.objects.filter(name='Shared Editable Shift'))
    assert {shift.department_id for shift in shifts} == {
        first_department.id,
        second_department.id,
    }

    response = client.patch(
        f'/api/v1/organizations/work-shifts/{shifts[0].id}/',
        {'name': 'Updated Shared Shift', 'start_time': '09:00'},
        format='json',
        secure=True,
    )

    assert response.status_code == 200, response.data
    assert response.data['updated'] == 2
    assert set(
        WorkShift.objects.filter(id__in=[shift.id for shift in shifts])
        .values_list('name', flat=True)
    ) == {'Updated Shared Shift'}


@pytest.mark.django_db
def test_deleting_one_group_member_deactivates_every_work_shift_in_group(work_shift_context):
    client, first_department = work_shift_context
    second_entity = Entity.objects.create(entity_name='Group Delete Company', code='GDEL')
    second_department = Department.objects.create(
        entity=second_entity,
        department_name='Support',
        code='SUP',
    )
    create_response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_ids': [str(first_department.entity_id), str(second_entity.id)],
        'name': 'Shared Deletable Shift',
        'start_time': '08:00',
        'end_time': '16:00',
    }, format='json', secure=True)
    assert create_response.status_code == 201, create_response.data
    shifts = list(WorkShift.objects.filter(name='Shared Deletable Shift'))

    response = client.delete(
        f'/api/v1/organizations/work-shifts/{shifts[0].id}/',
        secure=True,
    )

    assert response.status_code == 204
    assert WorkShift.objects.filter(
        id__in=[shift.id for shift in shifts],
        is_active=True,
    ).count() == 0


@pytest.mark.django_db
def test_group_edit_syncs_entities_and_user_assignments(work_shift_context):
    client, first_department = work_shift_context
    removed_entity = Entity.objects.create(entity_name='Removed Shift Entity', code='RSE')
    removed_department = Department.objects.create(
        entity=removed_entity,
        department_name='Removed Operations',
        code='ROPS',
    )
    removed_user = User.objects.create_user(
        email='removed-shift-user@example.com',
        password='UserPass123!',
        entity=removed_entity,
        department=removed_department,
    )
    added_entity = Entity.objects.create(entity_name='Added Shift Entity', code='ASE')
    added_department = Department.objects.create(
        entity=added_entity,
        department_name='Added Operations',
        code='AOPS',
    )
    added_user = User.objects.create_user(
        email='added-shift-user@example.com',
        password='UserPass123!',
        entity=added_entity,
        department=added_department,
    )
    create_response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_ids': [str(first_department.entity_id), str(removed_entity.id)],
        'name': 'Entity Sync Shift',
        'start_time': '08:00',
        'end_time': '16:00',
    }, format='json', secure=True)
    assert create_response.status_code == 201, create_response.data
    retained_unassigned_user = User.objects.create_user(
        email='retained-unassigned-user@example.com',
        password='UserPass123!',
        entity=first_department.entity,
        location=first_department.location,
        department=first_department,
    )
    retained_shift = WorkShift.objects.get(
        department=first_department,
        name='Entity Sync Shift',
    )
    removed_shift = WorkShift.objects.get(
        department=removed_department,
        name='Entity Sync Shift',
    )
    removed_user.refresh_from_db()
    assert removed_user.work_shift == removed_shift

    response = client.patch(
        f'/api/v1/organizations/work-shifts/{retained_shift.id}/',
        {
            'entity_ids': [str(first_department.entity_id), str(added_entity.id)],
            'name': 'Entity Sync Shift',
        },
        format='json',
        secure=True,
    )

    assert response.status_code == 200, response.data
    assert response.data['updated'] == 2
    assert response.data['added_departments'] == 1
    assert response.data['removed_departments'] == 1
    assert response.data['assigned_users'] == 2
    assert response.data['unassigned_users'] == 1
    removed_shift.refresh_from_db()
    removed_user.refresh_from_db()
    added_user.refresh_from_db()
    retained_unassigned_user.refresh_from_db()
    added_shift = WorkShift.objects.get(
        department=added_department,
        name='Entity Sync Shift',
        is_active=True,
    )
    assert removed_shift.is_active is False
    assert removed_user.work_shift is None
    assert added_user.work_shift == added_shift
    assert retained_unassigned_user.work_shift == retained_shift
    assert added_shift.management_group_id == retained_shift.management_group_id


@pytest.mark.django_db
def test_create_single_department_shift_assigns_unassigned_users(work_shift_context):
    client, department = work_shift_context
    user = User.objects.create_user(
        email='single-department-user@example.com',
        password='UserPass123!',
        entity=department.entity,
        location=department.location,
        department=department,
    )

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(department.id),
        'name': 'Department Shift',
        'start_time': '08:00',
        'end_time': '16:00',
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    user.refresh_from_db()
    assert str(user.work_shift_id) == response.data['id']


@pytest.mark.django_db
def test_rotating_shift_auto_assigns_only_users_with_cycle_start_date(work_shift_context):
    client, department = work_shift_context
    anchored_user = User.objects.create_user(
        email='anchored-rotation-user@example.com',
        password='UserPass123!',
        entity=department.entity,
        location=department.location,
        department=department,
        shift_cycle_start_date='2026-07-11',
    )
    unanchored_user = User.objects.create_user(
        email='unanchored-rotation-user@example.com',
        password='UserPass123!',
        entity=department.entity,
        location=department.location,
        department=department,
    )
    cycle_days = [
        {'name': 'Morning', 'start_time': '06:00', 'end_time': '14:00', 'is_working': True},
        {'name': 'Off', 'is_working': False},
    ]

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(department.id),
        'name': 'Anchored Rotation',
        'pattern_type': WorkShift.PatternType.ROTATING_CYCLE,
        'start_time': '06:00',
        'end_time': '14:00',
        'includes_weekends': True,
        'cycle_days': cycle_days,
    }, format='json', secure=True)

    assert response.status_code == 201, response.data
    assert response.data['assigned_users'] == 1
    anchored_user.refresh_from_db()
    unanchored_user.refresh_from_db()
    assert str(anchored_user.work_shift_id) == response.data['id']
    assert unanchored_user.work_shift_id is None


@pytest.mark.django_db
def test_hr_cannot_create_work_shift_for_multiple_entities():
    own_entity = Entity.objects.create(entity_name='Multi HR Entity', code='MHRE')
    own_department = Department.objects.create(
        entity=own_entity,
        department_name='HR',
        code='HR',
    )
    other_entity = Entity.objects.create(entity_name='Multi Other Entity', code='MOTE')
    other_department = Department.objects.create(
        entity=other_entity,
        department_name='Operations',
        code='OPS',
    )
    hr = User.objects.create_user(
        email='multi-work-shift-hr@example.com',
        password='HrPass123!',
        role=User.Role.HR,
        entity=own_entity,
        department=own_department,
    )
    client = APIClient()
    client.force_authenticate(user=hr)

    response = client.post('/api/v1/organizations/work-shifts/', {
        'entity_ids': [str(own_entity.id), str(other_entity.id)],
        'name': 'Unauthorized Shared Shift',
        'start_time': '08:00',
        'end_time': '16:00',
    }, format='json', secure=True)

    assert response.status_code == 404
    assert not WorkShift.objects.filter(department__in=[own_department, other_department]).exists()


@pytest.mark.django_db
def test_hr_can_only_manage_work_shifts_in_own_entity():
    own_entity = Entity.objects.create(entity_name='HR Entity', code='HRE')
    own_location = Location.objects.create(
        entity=own_entity,
        location_name='HR Office',
        city='Ho Chi Minh City',
        country='Vietnam',
        timezone='Asia/Ho_Chi_Minh',
    )
    own_department = Department.objects.create(
        entity=own_entity,
        location=own_location,
        department_name='HR',
        code='HR',
    )
    other_entity = Entity.objects.create(entity_name='Other Entity', code='OTE')
    other_location = Location.objects.create(
        entity=other_entity,
        location_name='Other Office',
        city='New York',
        country='USA',
        timezone='America/New_York',
    )
    other_department = Department.objects.create(
        entity=other_entity,
        location=other_location,
        department_name='Operations',
        code='OPS',
    )
    own_shift = WorkShift.objects.create(
        department=own_department,
        name='Own Shift',
        start_time='09:00',
        end_time='17:00',
    )
    other_shift = WorkShift.objects.create(
        department=other_department,
        name='Other Shift',
        start_time='08:00',
        end_time='16:00',
    )
    hr = User.objects.create_user(
        email='work-shift-hr@example.com',
        password='HrPass123!',
        role=User.Role.HR,
        entity=own_entity,
        location=own_location,
        department=own_department,
    )
    client = APIClient()
    client.force_authenticate(user=hr)

    list_response = client.get('/api/v1/organizations/work-shifts/')
    create_response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(other_department.id),
        'name': 'Unauthorized Shift',
        'start_time': '10:00',
        'end_time': '18:00',
    }, format='json')
    update_response = client.patch(
        f'/api/v1/organizations/work-shifts/{other_shift.id}/',
        {'name': 'Unauthorized Update'},
        format='json',
    )
    delete_response = client.delete(
        f'/api/v1/organizations/work-shifts/{other_shift.id}/'
    )

    assert list_response.status_code == 200
    assert {item['id'] for item in list_response.data} == {str(own_shift.id)}
    assert create_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    other_shift.refresh_from_db()
    assert other_shift.name == 'Other Shift'
    assert other_shift.is_active is True


@pytest.mark.django_db
def test_hr_group_edit_detaches_own_entity_without_updating_other_entities():
    own_entity = Entity.objects.create(entity_name='Scoped Group HR Entity', code='SGHR')
    own_department = Department.objects.create(
        entity=own_entity,
        department_name='HR',
        code='HR',
    )
    other_entity = Entity.objects.create(entity_name='Scoped Group Other Entity', code='SGOT')
    other_department = Department.objects.create(
        entity=other_entity,
        department_name='Operations',
        code='OPS',
    )
    group_id = WorkShift.objects.create(
        department=own_department,
        name='Shared Scope Shift',
        start_time='08:00',
        end_time='16:00',
    ).management_group_id
    own_shift = WorkShift.objects.get(department=own_department)
    other_shift = WorkShift.objects.create(
        department=other_department,
        management_group_id=group_id,
        name='Shared Scope Shift',
        start_time='08:00',
        end_time='16:00',
    )
    hr = User.objects.create_user(
        email='scoped-group-hr@example.com',
        password='HrPass123!',
        role=User.Role.HR,
        entity=own_entity,
        department=own_department,
    )
    client = APIClient()
    client.force_authenticate(user=hr)

    response = client.patch(
        f'/api/v1/organizations/work-shifts/{own_shift.id}/',
        {'name': 'HR Entity Shift'},
        format='json',
        secure=True,
    )

    assert response.status_code == 200, response.data
    own_shift.refresh_from_db()
    other_shift.refresh_from_db()
    assert own_shift.name == 'HR Entity Shift'
    assert other_shift.name == 'Shared Scope Shift'
    assert own_shift.management_group_id != other_shift.management_group_id


@pytest.mark.django_db
def test_admin_can_manage_work_shifts_across_entities(work_shift_context):
    client, _ = work_shift_context
    other_entity = Entity.objects.create(entity_name='Admin Other Entity', code='AOE')
    other_location = Location.objects.create(
        entity=other_entity,
        location_name='Admin Other Office',
        city='New York',
        country='USA',
        timezone='America/New_York',
    )
    other_department = Department.objects.create(
        entity=other_entity,
        location=other_location,
        department_name='Operations',
        code='OPS',
    )

    response = client.post('/api/v1/organizations/work-shifts/', {
        'department_id': str(other_department.id),
        'name': 'Admin Cross Entity Shift',
        'start_time': '08:00',
        'end_time': '16:00',
    }, format='json')

    assert response.status_code == 201, response.data
    assert WorkShift.objects.filter(
        department=other_department,
        name='Admin Cross Entity Shift',
    ).exists()
