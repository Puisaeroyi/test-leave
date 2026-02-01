"""Serializer validation utilities."""

from rest_framework import serializers


def validate_active_relationship(model_class, value, field_name):
    """Validate model instance exists and is active.

    Args:
        model_class: Django model class to query
        value: ID to look up
        field_name: Field name for error message

    Returns:
        Model instance if valid

    Raises:
        ValidationError: If instance not found or inactive
    """
    try:
        instance = model_class.objects.get(id=value, is_active=True)
        return instance
    except model_class.DoesNotExist:
        raise serializers.ValidationError(
            f"Invalid or inactive {field_name} selected."
        )
