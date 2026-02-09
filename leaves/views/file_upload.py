"""File upload views for attachments."""

import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import parsers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# Allowed file types and their MIME types
ALLOWED_EXTENSIONS = {
    'application/pdf': '.pdf',
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class FileUploadView(APIView):
    """Handle file uploads for leave request attachments."""

    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser]

    def post(self, request, *args, **kwargs):
        """Upload a file and return its URL.

        Validates:
        - File size (max 5MB)
        - File type (PDF, JPG, PNG, GIF, WebP)
        - Sanitizes filename
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=400
            )

        uploaded_file = request.FILES['file']

        # Validate file size
        if uploaded_file.size > MAX_FILE_SIZE:
            return Response(
                {'error': f'File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'},
                status=400
            )

        # Validate file type by checking MIME type
        file_type = uploaded_file.content_type
        if file_type not in ALLOWED_EXTENSIONS:
            allowed = ', '.join(ALLOWED_EXTENSIONS.keys())
            return Response(
                {'error': f'Invalid file type. Allowed: {allowed}'},
                status=400
            )

        # Validate magic bytes to prevent spoofed Content-Type
        MAGIC_BYTES = {
            b'%PDF': '.pdf',
            b'\xff\xd8\xff': '.jpg',
            b'\x89PNG': '.png',
            b'GIF87a': '.gif',
            b'GIF89a': '.gif',
        }

        # Read first 12 bytes to check magic bytes (WebP needs 12)
        file_header = uploaded_file.read(12)
        uploaded_file.seek(0)  # Reset file pointer

        valid_magic = False
        # WebP: RIFF????WEBP (bytes 0-3 = RIFF, bytes 8-11 = WEBP)
        if file_header[:4] == b'RIFF' and file_header[8:12] == b'WEBP':
            valid_magic = True
        else:
            for magic, ext in MAGIC_BYTES.items():
                if file_header.startswith(magic):
                    valid_magic = True
                    break

        if not valid_magic:
            return Response({'error': 'File content does not match declared type'}, status=400)

        # Get file extension from MIME type
        extension = ALLOWED_EXTENSIONS[file_type]

        # Generate unique filename to prevent conflicts
        unique_filename = f"{uuid.uuid4()}{extension}"

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'attachments')
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join('attachments', unique_filename)
        saved_path = default_storage.save(file_path, uploaded_file)

        # Return relative URL - reverse proxy provides the correct domain
        file_url = settings.MEDIA_URL + saved_path

        return Response({
            'url': file_url,
            'filename': uploaded_file.name,
            'size': uploaded_file.size,
            'type': file_type
        }, status=201)
