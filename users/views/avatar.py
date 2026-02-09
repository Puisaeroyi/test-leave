"""Avatar upload view for users to update their profile picture."""

from rest_framework import parsers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import User


# Allowed image types for avatars
ALLOWED_AVATAR_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
}

MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


class AvatarUpdateView(APIView):
    """
    Update current user's avatar.

    POST /api/v1/auth/avatar/
    Content-Type: multipart/form-data

    Body:
        file: image file (max 2MB, jpg/png/gif/webp)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser]

    def post(self, request, *args, **kwargs):
        """Upload and set user's avatar."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']

        # Validate file size
        if uploaded_file.size > MAX_AVATAR_SIZE:
            return Response(
                {'error': f'File size exceeds {MAX_AVATAR_SIZE // (1024*1024)}MB limit'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        file_type = uploaded_file.content_type
        if file_type not in ALLOWED_AVATAR_TYPES:
            allowed = ', '.join(ALLOWED_AVATAR_TYPES.keys())
            return Response(
                {'error': f'Invalid file type. Allowed: {allowed}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate magic bytes to prevent spoofed Content-Type
        MAGIC_BYTES = {
            b'\xff\xd8\xff': '.jpg',
            b'\x89PNG': '.png',
            b'GIF87a': '.gif',
            b'GIF89a': '.gif',
        }

        file_header = uploaded_file.read(12)
        uploaded_file.seek(0)

        valid_magic = False
        # WebP: RIFF????WEBP
        if file_header[:4] == b'RIFF' and file_header[8:12] == b'WEBP':
            valid_magic = True
        else:
            for magic, ext in MAGIC_BYTES.items():
                if file_header.startswith(magic):
                    valid_magic = True
                    break

        if not valid_magic:
            return Response(
                {'error': 'File content does not match declared type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use the existing file upload endpoint to get the URL
        from leaves.views.file_upload import FileUploadView

        # Create a mock request with the file
        upload_view = FileUploadView()
        upload_view.request = request
        upload_view.format_kwarg = None

        # Get upload response
        upload_response = upload_view.post(request)

        if upload_response.status_code != 201:
            return upload_response

        # Update user's avatar_url
        file_url = upload_response.data.get('url')
        user = request.user
        user.avatar_url = file_url
        user.save(update_fields=['avatar_url'])

        # Return updated user info
        from ..utils import build_user_response
        return Response(build_user_response(user), status=status.HTTP_200_OK)
