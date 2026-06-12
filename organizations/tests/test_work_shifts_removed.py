import pytest
from rest_framework.test import APIClient

from users.models import User


@pytest.mark.django_db
def test_work_shift_endpoint_is_removed():
    admin = User.objects.create_user(
        email='workshift-removed-admin@example.com',
        password='AdminPass123!',
        role=User.Role.ADMIN,
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get('/api/v1/organizations/work-shifts/')

    assert response.status_code == 404
