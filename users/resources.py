"""
Django import-export resources for User model with validation.
Supports CSV/XLSX import with organization references.
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from .models import User
from organizations.models import Entity, Location, Department


class DefaultTrueBooleanWidget(BooleanWidget):
    """Boolean widget that defaults to True when value is empty or missing."""

    def clean(self, value, row=None, **kwargs):
        if value is None or value == '' or str(value).strip() == '':
            return True
        return super().clean(value, row, **kwargs)


class EntityForeignKeyWidget(ForeignKeyWidget):
    """Widget for looking up Entity by code."""

    def __init__(self):
        super().__init__(Entity, field='code')

    def clean(self, value, row=None, **kwargs):
        if not value or str(value).strip() == '':
            return None
        try:
            return Entity.objects.get(code=str(value).strip(), is_active=True)
        except Entity.DoesNotExist:
            raise ValidationError(f"Entity with code '{value}' not found or inactive")


class LocationByNameWidget(ForeignKeyWidget):
    """Widget for looking up Location by name and entity."""

    def __init__(self):
        super().__init__(Location, field='location_name')

    def clean(self, value, row=None, **kwargs):
        if not value or str(value).strip() == '':
            return None
        location_name = str(value).strip()

        # Get entity from row
        entity_code = row.get('Entity_Code') if row else None
        if not entity_code:
            raise ValidationError(f"Entity_Code required when specifying Location_Name")

        try:
            entity = Entity.objects.get(code=str(entity_code).strip(), is_active=True)
        except Entity.DoesNotExist:
            raise ValidationError(f"Entity with code '{entity_code}' not found or inactive")

        try:
            return Location.objects.get(
                entity=entity,
                location_name=location_name,
                is_active=True
            )
        except Location.DoesNotExist:
            raise ValidationError(
                f"Location '{location_name}' not found for Entity '{entity_code}'"
            )


class DepartmentByCodeWidget(ForeignKeyWidget):
    """Widget for looking up Department by code and entity."""

    def __init__(self):
        super().__init__(Department, field='code')

    def clean(self, value, row=None, **kwargs):
        if not value or str(value).strip() == '':
            return None
        department_code = str(value).strip()

        # Get entity from row
        entity_code = row.get('Entity_Code') if row else None
        if not entity_code:
            raise ValidationError(f"Entity_Code required when specifying Department_Code")

        try:
            entity = Entity.objects.get(code=str(entity_code).strip(), is_active=True)
        except Entity.DoesNotExist:
            raise ValidationError(f"Entity with code '{entity_code}' not found or inactive")

        try:
            return Department.objects.get(
                entity=entity,
                code=department_code,
                is_active=True
            )
        except Department.DoesNotExist:
            raise ValidationError(
                f"Department '{department_code}' not found for Entity '{entity_code}'"
            )


class UserResource(resources.ModelResource):
    """Import/export resource for User model with validation."""

    # Map CSV column names (case-sensitive) to model attributes
    email = fields.Field(attribute='email', column_name='Email')
    first_name = fields.Field(attribute='first_name', column_name='First_Name')
    last_name = fields.Field(attribute='last_name', column_name='Last_Name')
    role = fields.Field(attribute='role', column_name='Role')
    status = fields.Field(attribute='status', column_name='Status')
    join_date = fields.Field(attribute='join_date', column_name='Join_Date')

    entity = fields.Field(
        column_name='Entity_Code',
        attribute='entity',
        widget=EntityForeignKeyWidget()
    )
    location = fields.Field(
        column_name='Location_Name',
        attribute='location',
        widget=LocationByNameWidget()
    )
    department = fields.Field(
        column_name='Department_Code',
        attribute='department',
        widget=DepartmentByCodeWidget()
    )
    is_active = fields.Field(
        column_name='is_active',
        attribute='is_active',
        widget=DefaultTrueBooleanWidget(),
        default=True
    )

    class Meta:
        model = User
        import_id_fields = ['email']
        # Use column names (case-sensitive from CSV headers)
        fields = (
            'Email', 'First_Name', 'Last_Name', 'Entity_Code', 'Location_Name',
            'Department_Code', 'Role', 'Status', 'Join_Date', 'is_active'
        )
        export_order = (
            'Email', 'First_Name', 'Last_Name', 'Role', 'Status', 'Entity_Code',
            'Location_Name', 'Department_Code', 'Join_Date', 'is_active'
        )
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Clean up None values and set defaults before import."""
        # Handle None values
        for key, value in row.items():
            if value is None:
                row[key] = ''

        # Set default status if not provided
        if 'status' not in row or not row.get('status'):
            row['status'] = 'ACTIVE'

        # Set default role if not provided
        if 'role' not in row or not row.get('role'):
            row['role'] = 'EMPLOYEE'

    def import_row(self, row, instance_loader, dry_run=False, raise_errors=False, use_transactions=None, **kwargs):
        """Override to collect validation errors properly. Matches django-import-export 4.0+ API."""
        try:
            # Pass extra args as kwargs to parent (which accepts **kwargs)
            return super().import_row(row, instance_loader, dry_run=dry_run, raise_errors=raise_errors, use_transactions=use_transactions, **kwargs)
        except ValidationError as e:
            # Return error result instead of raising
            from import_export.results import RowResult
            result = RowResult()
            result.import_type = RowResult.IMPORT_TYPE_ERROR
            result.errors = [(str(e), row)]
            return result
