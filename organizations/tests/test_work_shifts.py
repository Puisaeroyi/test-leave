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
    }, format='json')

    assert response.status_code == 201, response.data
    assert WorkShift.objects.filter(department=department, name='Night Shift').exists()

    response = client.get(
        '/api/v1/organizations/work-shifts/',
        {'department_id': str(department.id)},
    )
    assert response.status_code == 200
    assert response.data[0]['name'] == 'Night Shift'


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
    }, format='json')

    assert response.status_code == 400
    assert 'name' in response.data
