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
