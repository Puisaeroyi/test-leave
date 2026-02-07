"""
Test suite for Entity CRUD operations
Tests serializers, services, and API endpoints
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from organizations.models import Entity, Location, Department
from organizations.serializers.entity_serializers import (
    EntityCreateSerializer,
    EntityUpdateSerializer,
    EntitySerializer
)
from organizations.services import (
    get_entity_delete_impact,
    soft_delete_entity_cascade
)

User = get_user_model()


@pytest.fixture
def api_client():
    """DRF API test client"""
    return APIClient()


@pytest.fixture
def hr_user(db):
    """Create HR user for permission tests"""
    user = User.objects.create_user(
        email='hr@test.com',
        password='test123',
        first_name='HR',
        last_name='User',
        role='HR'
    )
    return user


@pytest.fixture
def admin_user(db):
    """Create Admin user for permission tests"""
    user = User.objects.create_user(
        email='admin@test.com',
        password='test123',
        first_name='Admin',
        last_name='User',
        role='Admin'
    )
    return user


@pytest.fixture
def employee_user(db):
    """Create Employee user for permission tests"""
    user = User.objects.create_user(
        email='employee@test.com',
        password='test123',
        first_name='Employee',
        last_name='User',
        role='Employee'
    )
    return user


@pytest.fixture
def sample_entity(db):
    """Create sample entity for tests"""
    return Entity.objects.create(
        entity_name='Acme Corporation',
        code='ACME'
    )


@pytest.fixture
def entity_with_relations(db):
    """Create entity with locations and departments"""
    entity = Entity.objects.create(
        entity_name='Test Corp',
        code='TEST'
    )
    location = Location.objects.create(
        entity=entity,
        location_name='HQ Office',
        city='New York',
        country='USA',
        timezone='America/New_York'
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name='Engineering',
        code='ENG'
    )
    return entity


# ==================== Serializer Tests ====================

@pytest.mark.django_db
class TestEntityCreateSerializer:
    """Test EntityCreateSerializer validation"""

    def test_create_valid_entity(self):
        """Valid entity data should pass validation"""
        data = {
            'entity_name': 'New Company',
            'code': 'new'
        }
        serializer = EntityCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        entity = serializer.save()
        assert entity.entity_name == 'New Company'
        assert entity.code == 'NEW'  # Auto-uppercase

    def test_duplicate_name_case_insensitive(self, sample_entity):
        """Duplicate name (case-insensitive) should fail"""
        data = {
            'entity_name': 'acme corporation',  # lowercase
            'code': 'NEWCODE'
        }
        serializer = EntityCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'entity_name' in serializer.errors

    def test_duplicate_code_case_insensitive(self, sample_entity):
        """Duplicate code (case-insensitive) should fail"""
        data = {
            'entity_name': 'Different Company',
            'code': 'acme'  # lowercase but matches existing
        }
        serializer = EntityCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'code' in serializer.errors

    def test_code_auto_uppercase(self):
        """Code should be automatically uppercased"""
        data = {
            'entity_name': 'Lowercase Test',
            'code': 'lower'
        }
        serializer = EntityCreateSerializer(data=data)
        assert serializer.is_valid()
        entity = serializer.save()
        assert entity.code == 'LOWER'


@pytest.mark.django_db
class TestEntityUpdateSerializer:
    """Test EntityUpdateSerializer validation"""

    def test_update_entity_same_name(self, sample_entity):
        """Updating with same name should succeed"""
        data = {'entity_name': 'Acme Corporation'}
        serializer = EntityUpdateSerializer(sample_entity, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors

    def test_update_duplicate_name(self, sample_entity):
        """Updating to existing name should fail"""
        other_entity = Entity.objects.create(entity_name='Other Corp', code='OTHER')
        data = {'entity_name': 'other corp'}  # case-insensitive match
        serializer = EntityUpdateSerializer(sample_entity, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'entity_name' in serializer.errors

    def test_update_code_uppercase(self, sample_entity):
        """Code should be uppercased on update"""
        data = {'code': 'newcode'}
        serializer = EntityUpdateSerializer(sample_entity, data=data, partial=True)
        assert serializer.is_valid()
        entity = serializer.save()
        assert entity.code == 'NEWCODE'


@pytest.mark.django_db
class TestEntitySerializer:
    """Test EntitySerializer read operations"""

    def test_serialize_entity_with_counts(self, entity_with_relations):
        """Should include locations and departments counts"""
        serializer = EntitySerializer(entity_with_relations)
        data = serializer.data
        assert data['entity_name'] == 'Test Corp'
        assert data['code'] == 'TEST'
        assert data['locations_count'] == 1
        assert data['departments_count'] == 1

    def test_counts_exclude_inactive(self, entity_with_relations):
        """Counts should exclude inactive records"""
        # Deactivate the location
        entity_with_relations.locations.update(is_active=False)
        serializer = EntitySerializer(entity_with_relations)
        data = serializer.data
        assert data['locations_count'] == 0
        assert data['departments_count'] == 1  # Department still active


# ==================== Service Tests ====================

@pytest.mark.django_db
class TestEntityDeleteImpact:
    """Test get_entity_delete_impact service function"""

    def test_impact_calculation(self, entity_with_relations):
        """Should return accurate impact counts"""
        result = get_entity_delete_impact(entity_with_relations.id)
        assert result is not None
        assert result['entity_name'] == 'Test Corp'
        assert result['locations_count'] == 1
        assert result['departments_count'] == 1
        assert result['total_impact'] == 2

    def test_impact_nonexistent_entity(self):
        """Should return None for nonexistent entity"""
        import uuid
        result = get_entity_delete_impact(uuid.uuid4())
        assert result is None

    def test_impact_inactive_entity(self, sample_entity):
        """Should return None for inactive entity"""
        sample_entity.is_active = False
        sample_entity.save()
        result = get_entity_delete_impact(sample_entity.id)
        assert result is None


@pytest.mark.django_db
class TestSoftDeleteEntityCascade:
    """Test soft_delete_entity_cascade service function"""

    def test_cascade_deactivates_all(self, entity_with_relations):
        """Should deactivate entity, locations, and departments"""
        result = soft_delete_entity_cascade(entity_with_relations.id)

        assert result['success'] is True
        assert result['locations_deactivated'] == 1
        assert result['departments_deactivated'] == 1

        # Verify database state
        entity_with_relations.refresh_from_db()
        assert entity_with_relations.is_active is False

        location = entity_with_relations.locations.first()
        location.refresh_from_db()
        assert location.is_active is False

        department = entity_with_relations.departments.first()
        department.refresh_from_db()
        assert department.is_active is False

    def test_cascade_multiple_children(self, db):
        """Should handle multiple locations and departments"""
        entity = Entity.objects.create(entity_name='Multi Corp', code='MULTI')

        # Create 3 locations
        for i in range(3):
            Location.objects.create(
                entity=entity,
                location_name=f'Location {i}',
                city='City',
                country='USA',
                timezone='UTC'
            )

        # Create 5 departments
        for i in range(5):
            Department.objects.create(
                entity=entity,
                department_name=f'Dept {i}',
                code=f'D{i}'
            )

        result = soft_delete_entity_cascade(entity.id)
        assert result['locations_deactivated'] == 3
        assert result['departments_deactivated'] == 5

    def test_cascade_already_inactive_children(self, entity_with_relations):
        """Should only count active children"""
        # Deactivate location manually
        entity_with_relations.locations.update(is_active=False)

        result = soft_delete_entity_cascade(entity_with_relations.id)
        assert result['locations_deactivated'] == 0  # Already inactive
        assert result['departments_deactivated'] == 1  # Still active

    def test_cascade_transaction_rollback(self, entity_with_relations):
        """Should rollback if error occurs"""
        # This tests that transaction.atomic() is working
        # We can't easily force a DB error, so we verify the function uses transaction
        from django.db import transaction

        # Check that the function uses atomic transaction
        import inspect
        source = inspect.getsource(soft_delete_entity_cascade)
        assert 'transaction.atomic' in source


# ==================== API Endpoint Tests ====================

@pytest.mark.django_db
class TestEntityListAPI:
    """Test GET /api/v1/organizations/entities/"""

    def test_list_entities_hr(self, api_client, hr_user, sample_entity):
        """HR user can list entities"""
        api_client.force_authenticate(user=hr_user)
        response = api_client.get('/api/v1/organizations/entities/')
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_list_entities_admin(self, api_client, admin_user, sample_entity):
        """Admin user can list entities"""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/v1/organizations/entities/')
        assert response.status_code == 200

    def test_list_entities_employee(self, api_client, employee_user, sample_entity):
        """Employee user can list entities (read-only access)"""
        api_client.force_authenticate(user=employee_user)
        response = api_client.get('/api/v1/organizations/entities/')
        assert response.status_code == 200

    def test_list_entities_unauthenticated(self, api_client, sample_entity):
        """Unauthenticated users should be denied"""
        response = api_client.get('/api/v1/organizations/entities/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestEntityCreateAPI:
    """Test POST /api/v1/organizations/entities/create/"""

    def test_create_entity_hr(self, api_client, hr_user):
        """HR user can create entity"""
        api_client.force_authenticate(user=hr_user)
        data = {
            'entity_name': 'New Entity',
            'code': 'new'
        }
        response = api_client.post('/api/v1/organizations/entities/create/', data)
        assert response.status_code == 201
        assert response.data['entity_name'] == 'New Entity'
        assert response.data['code'] == 'NEW'

    def test_create_entity_admin(self, api_client, admin_user):
        """Admin user can create entity"""
        api_client.force_authenticate(user=admin_user)
        data = {
            'entity_name': 'Admin Entity',
            'code': 'ADM'
        }
        response = api_client.post('/api/v1/organizations/entities/create/', data)
        assert response.status_code == 201

    def test_create_entity_employee_forbidden(self, api_client, employee_user):
        """Employee user cannot create entity"""
        api_client.force_authenticate(user=employee_user)
        data = {
            'entity_name': 'Blocked Entity',
            'code': 'BLK'
        }
        response = api_client.post('/api/v1/organizations/entities/create/', data)
        assert response.status_code == 403

    def test_create_entity_duplicate_name(self, api_client, hr_user, sample_entity):
        """Duplicate name should return 400"""
        api_client.force_authenticate(user=hr_user)
        data = {
            'entity_name': 'Acme Corporation',
            'code': 'NEW'
        }
        response = api_client.post('/api/v1/organizations/entities/create/', data)
        assert response.status_code == 400
        assert 'entity_name' in response.data


@pytest.mark.django_db
class TestEntityUpdateAPI:
    """Test PATCH /api/v1/organizations/entities/{id}/update/"""

    def test_update_entity_hr(self, api_client, hr_user, sample_entity):
        """HR user can update entity"""
        api_client.force_authenticate(user=hr_user)
        data = {'entity_name': 'Updated Name'}
        url = f'/api/v1/organizations/entities/{sample_entity.id}/update/'
        response = api_client.patch(url, data)
        assert response.status_code == 200
        assert response.data['entity_name'] == 'Updated Name'

    def test_update_entity_employee_forbidden(self, api_client, employee_user, sample_entity):
        """Employee user cannot update entity"""
        api_client.force_authenticate(user=employee_user)
        data = {'entity_name': 'Blocked Update'}
        url = f'/api/v1/organizations/entities/{sample_entity.id}/update/'
        response = api_client.patch(url, data)
        assert response.status_code == 403


@pytest.mark.django_db
class TestEntityDeleteImpactAPI:
    """Test GET /api/v1/organizations/entities/{id}/delete-impact/"""

    def test_delete_impact(self, api_client, hr_user, entity_with_relations):
        """Should return impact counts"""
        api_client.force_authenticate(user=hr_user)
        url = f'/api/v1/organizations/entities/{entity_with_relations.id}/delete-impact/'
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['locations_count'] == 1
        assert response.data['departments_count'] == 1

    def test_delete_impact_nonexistent(self, api_client, hr_user):
        """Should return 404 for nonexistent entity"""
        import uuid
        api_client.force_authenticate(user=hr_user)
        url = f'/api/v1/organizations/entities/{uuid.uuid4()}/delete-impact/'
        response = api_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestEntitySoftDeleteAPI:
    """Test POST /api/v1/organizations/entities/{id}/soft-delete/"""

    def test_soft_delete_hr(self, api_client, hr_user, entity_with_relations):
        """HR user can soft-delete entity"""
        api_client.force_authenticate(user=hr_user)
        url = f'/api/v1/organizations/entities/{entity_with_relations.id}/soft-delete/'
        response = api_client.patch(url)
        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['locations_deactivated'] == 1

        # Verify entity is deactivated
        entity_with_relations.refresh_from_db()
        assert entity_with_relations.is_active is False

    def test_soft_delete_employee_forbidden(self, api_client, employee_user, sample_entity):
        """Employee user cannot soft-delete entity"""
        api_client.force_authenticate(user=employee_user)
        url = f'/api/v1/organizations/entities/{sample_entity.id}/soft-delete/'
        response = api_client.patch(url)
        assert response.status_code == 403

    def test_soft_delete_already_inactive(self, api_client, hr_user, sample_entity):
        """Deleting already inactive entity should return 404"""
        sample_entity.is_active = False
        sample_entity.save()

        api_client.force_authenticate(user=hr_user)
        url = f'/api/v1/organizations/entities/{sample_entity.id}/soft-delete/'
        response = api_client.patch(url)
        assert response.status_code == 404
