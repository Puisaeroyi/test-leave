"""Validation for backend-to-backend credential verification."""

from rest_framework import serializers


class InternalCredentialSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        max_length=256,
        trim_whitespace=False,
        write_only=True,
    )


class InternalAccountStatusSerializer(serializers.Serializer):
    external_user_id = serializers.UUIDField()


class InternalAccountLookupSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
