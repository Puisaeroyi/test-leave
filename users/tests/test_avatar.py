from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.response import Response
from rest_framework.test import APIClient

from organizations.models import Department, Entity, Location
from users.models import User


@pytest.mark.django_db
def test_user_avatar_accepts_relative_media_and_absolute_https_urls():
    user = User.objects.create_user(email="avatar-valid@example.com", password="Password123!")

    user.avatar_url = "/media/attachments/avatar.png"
    user.full_clean()

    user.avatar_url = "https://lh3.googleusercontent.com/avatar.png"
    user.full_clean()


@pytest.mark.django_db
def test_user_avatar_rejects_invalid_url_values():
    user = User.objects.create_user(email="avatar-invalid@example.com", password="Password123!")
    user.avatar_url = "javascript:alert(1)"

    with pytest.raises(ValidationError) as exc:
        user.full_clean()

    assert "avatar_url" in exc.value.message_dict


@pytest.mark.django_db
def test_avatar_upload_persists_relative_media_url(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(email="avatar-upload@example.com", password="Password123!")
    client = APIClient()
    client.force_authenticate(user=user)

    file = SimpleUploadedFile(
        "avatar.png",
        b"\x89PNG\r\n\x1a\navatar-data",
        content_type="image/png",
    )
    response = client.post("/api/v1/auth/avatar/", {"file": file}, format="multipart", secure=True)

    assert response.status_code == 200, response.data
    user.refresh_from_db()
    assert user.avatar_url.startswith("/media/attachments/")
    assert response.data["avatar_url"] == user.avatar_url


@pytest.mark.django_db
def test_avatar_upload_returns_400_when_saved_url_fails_validation():
    user = User.objects.create_user(email="avatar-400@example.com", password="Password123!")
    client = APIClient()
    client.force_authenticate(user=user)

    file = SimpleUploadedFile(
        "avatar.png",
        b"\x89PNG\r\n\x1a\navatar-data",
        content_type="image/png",
    )

    with patch(
        "leaves.views.file_upload.FileUploadView.post",
        return_value=Response({"url": "not-a-url"}, status=201),
    ):
        response = client.post("/api/v1/auth/avatar/", {"file": file}, format="multipart", secure=True)

    assert response.status_code == 400
    assert "avatar_url" in response.data


@pytest.mark.django_db
def test_user_management_patch_invalid_avatar_url_returns_400():
    entity = Entity.objects.create(entity_name="Avatar Admin Co", code="AVADM")
    location = Location.objects.create(
        entity=entity,
        location_name="Avatar Office",
        city="Ho Chi Minh City",
        country="Vietnam",
        timezone="Asia/Ho_Chi_Minh",
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name="People",
        code="PPL",
    )
    admin = User.objects.create_user(
        email="avatar-admin@example.com",
        password="Password123!",
        role=User.Role.ADMIN,
        entity=entity,
        location=location,
        department=department,
    )
    employee = User.objects.create_user(
        email="avatar-employee@example.com",
        password="Password123!",
        entity=entity,
        location=location,
        department=department,
    )
    client = APIClient()
    client.force_authenticate(admin)

    response = client.patch(
        f"/api/v1/auth/users/{employee.id}/",
        {"avatar_url": "not-a-url"},
        format="json",
        secure=True,
    )

    assert response.status_code == 400
    assert "avatar_url" in response.data
