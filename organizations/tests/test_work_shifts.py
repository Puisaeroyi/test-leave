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
