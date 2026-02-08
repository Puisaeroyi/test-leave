"""
Organization business logic and service functions
"""
from django.db import transaction
from organizations.models import Entity, Location, Department
from users.models import User


def get_entity_delete_impact(entity_id):
    """
    Calculate impact of soft-deleting an Entity
    Returns counts of Locations and Departments that will be deactivated

    Args:
        entity_id: UUID of the entity

    Returns:
        dict with impact counts or None if entity not found
    """
    try:
        entity = Entity.objects.get(id=entity_id, is_active=True)
    except Entity.DoesNotExist:
        return None

    locations_count = entity.locations.filter(is_active=True).count()
    departments_count = entity.departments.filter(is_active=True).count()
    users_count = User.objects.filter(entity=entity, is_active=True).count()

    return {
        'entity_id': str(entity.id),
        'entity_name': entity.entity_name,
        'locations_count': locations_count,
        'departments_count': departments_count,
        'users_count': users_count,
        'total_impact': locations_count + departments_count + users_count
    }


def soft_delete_entity_cascade(entity_id):
    """
    Soft-delete Entity and cascade to all Locations and Departments
    Sets is_active=False for Entity and all related records in a transaction

    Args:
        entity_id: UUID of the entity to soft-delete

    Returns:
        dict with counts of affected records

    Raises:
        Entity.DoesNotExist: if entity not found or already inactive
    """
    with transaction.atomic():
        entity = Entity.objects.get(id=entity_id, is_active=True)

        # Count before update
        locations_count = entity.locations.filter(is_active=True).count()
        departments_count = entity.departments.filter(is_active=True).count()
        users_count = User.objects.filter(entity=entity, is_active=True).count()

        # Cascade soft-delete to children
        entity.locations.filter(is_active=True).update(is_active=False)
        entity.departments.filter(is_active=True).update(is_active=False)

        # Deactivate all users under this entity
        User.objects.filter(entity=entity, is_active=True).update(is_active=False)

        # Soft-delete Entity last
        entity.is_active = False
        entity.save()

        return {
            'entity_id': str(entity.id),
            'entity_name': entity.entity_name,
            'locations_deactivated': locations_count,
            'departments_deactivated': departments_count,
            'users_deactivated': users_count,
            'success': True
        }
