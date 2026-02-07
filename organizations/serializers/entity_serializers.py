"""
Entity serializers for CRUD operations
"""
from rest_framework import serializers
from organizations.models import Entity, Location, Department


class EntitySerializer(serializers.ModelSerializer):
    """Read-only serializer with related counts"""
    locations_count = serializers.SerializerMethodField()
    departments_count = serializers.SerializerMethodField()

    class Meta:
        model = Entity
        fields = ['id', 'entity_name', 'code', 'is_active', 'created_at',
                  'locations_count', 'departments_count']
        read_only_fields = ['id', 'created_at']

    def get_locations_count(self, obj):
        """Count active locations for this entity"""
        return obj.locations.filter(is_active=True).count()

    def get_departments_count(self, obj):
        """Count active departments for this entity"""
        return obj.departments.filter(is_active=True).count()


class EntityCreateSerializer(serializers.ModelSerializer):
    """Create new Entity with validation"""

    class Meta:
        model = Entity
        fields = ['entity_name', 'code', 'is_active']

    def validate_entity_name(self, value):
        """Check entity_name uniqueness (case-insensitive)"""
        if Entity.objects.filter(entity_name__iexact=value).exists():
            raise serializers.ValidationError("Entity with this name already exists.")
        return value

    def validate_code(self, value):
        """Check code uniqueness (case-insensitive) and normalize to uppercase"""
        if Entity.objects.filter(code__iexact=value).exists():
            raise serializers.ValidationError("Entity with this code already exists.")
        return value.upper()


class EntityUpdateSerializer(serializers.ModelSerializer):
    """Update existing Entity with validation"""

    class Meta:
        model = Entity
        fields = ['entity_name', 'code', 'is_active']

    def validate_entity_name(self, value):
        """Check entity_name uniqueness excluding current instance"""
        if self.instance:
            if Entity.objects.filter(entity_name__iexact=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Entity with this name already exists.")
        return value

    def validate_code(self, value):
        """Check code uniqueness excluding current instance and normalize to uppercase"""
        if self.instance:
            if Entity.objects.filter(code__iexact=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Entity with this code already exists.")
        return value.upper()
