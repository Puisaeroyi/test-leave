"""User management views."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_entity_options(request):
    """
    GET /admin/get-entity-options/?entity_id=xxx
    Returns locations and departments for a given entity (for admin cascading dropdowns)
    """
    from organizations.models import Entity

    entity_id = request.GET.get('entity_id')
    if not entity_id:
        return Response({'locations': [], 'departments': []})

    try:
        entity = Entity.objects.get(id=entity_id)
        locations = [
            {'id': str(loc.id), 'name': f"{loc.location_name} ({loc.city})"}
            for loc in entity.locations.filter(is_active=True)
        ]
        departments = [
            {'id': str(dept.id), 'name': dept.department_name}
            for dept in entity.departments.filter(is_active=True)
        ]
        return Response({'locations': locations, 'departments': departments})
    except Entity.DoesNotExist:
        return Response({'locations': [], 'departments': []})
    except Exception as e:
        return Response({'error': str(e), 'locations': [], 'departments': []}, status=400)
