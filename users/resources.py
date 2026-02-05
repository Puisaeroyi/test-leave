"""
Django import-export resources for User model with validation.
Supports CSV/XLSX import with organization references.
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, BooleanWidget, Widget
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from datetime import datetime, date
from .models import User
from organizations.models import Entity, Location, Department


class NullableDateWidget(Widget):
    """Widget that handles nullable date fields."""

    def clean(self, value, row=None, **kwargs):
        if value is None or value == '' or str(value).strip() == '':
            return None
        # Handle datetime objects from Excel
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        # Parse string dates
        parsed = parse_date(str(value))
        if parsed:
            return parsed
        raise ValidationError(f"Invalid date format: '{value}'. Expected YYYY-MM-DD.")

    def render(self, value, obj=None):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d') if value else ''


class NullableCharWidget(Widget):
    """Widget that handles nullable char fields - converts empty string to None."""

    def clean(self, value, row=None, **kwargs):
        if value is None or value == '' or str(value).strip() == '':
            return None
        return str(value)


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
    """Widget for looking up Department by code, entity, and location."""

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

        # Get location from row to match department at specific location
        location_name = row.get('Location_Name') if row else None
        location = None
        if location_name and str(location_name).strip():
            try:
                location = Location.objects.get(
                    entity=entity,
                    location_name=str(location_name).strip(),
                    is_active=True
                )
            except Location.DoesNotExist:
                raise ValidationError(
                    f"Location '{location_name}' not found for Entity '{entity_code}'"
                )

        # Try to find department with location first, fall back to entity-wide (location=null)
        try:
            return Department.objects.get(
                entity=entity,
                location=location,
                code=department_code,
                is_active=True
            )
        except Department.DoesNotExist:
            # If no location-specific department found, try entity-wide (location=null)
            if location:
                try:
                    return Department.objects.get(
                        entity=entity,
                        location__isnull=True,
                        code=department_code,
                        is_active=True
                    )
                except Department.DoesNotExist:
                    pass
            raise ValidationError(
                f"Department '{department_code}' not found for Entity '{entity_code}' at Location '{location_name}'"
            )


class ApproverByEmailWidget(ForeignKeyWidget):
    """Widget for looking up Approver (User) by email."""

    def __init__(self):
        super().__init__(User, field='email')

    def clean(self, value, row=None, **kwargs):
        if not value or str(value).strip() == '':
            return None
        email = str(value).strip()

        try:
            return User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            raise ValidationError(f"Approver with email '{value}' not found or inactive")


DEFAULT_IMPORT_PASSWORD = 'Timpl.com'


class PasswordWidget(Widget):
    """Widget that returns password value or default. Not saved directly — handled in after_save_instance."""

    def clean(self, value, row=None, **kwargs):
        if value and str(value).strip():
            return str(value).strip()
        return DEFAULT_IMPORT_PASSWORD

    def render(self, value, obj=None):
        # Never export actual passwords
        return ''


class UserResource(resources.ModelResource):
    """Import/export resource for User model with validation."""

    # Map CSV column names (case-sensitive) to model attributes
    email = fields.Field(attribute='email', column_name='Email')
    first_name = fields.Field(attribute='first_name', column_name='First_Name')
    last_name = fields.Field(attribute='last_name', column_name='Last_Name')
    employee_code = fields.Field(attribute='employee_code', column_name='Employee_Code', widget=NullableCharWidget())
    role = fields.Field(attribute='role', column_name='Role')
    status = fields.Field(attribute='status', column_name='Status')
    join_date = fields.Field(attribute='join_date', column_name='Join_Date', widget=NullableDateWidget())
    # Password column — optional, defaults to DEFAULT_IMPORT_PASSWORD
    password = fields.Field(column_name='Password', widget=PasswordWidget())

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
    approver = fields.Field(
        column_name='Approver_Email',
        attribute='approver',
        widget=ApproverByEmailWidget()
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
            'Email', 'First_Name', 'Last_Name', 'Employee_Code', 'Entity_Code', 'Location_Name',
            'Department_Code', 'Role', 'Status', 'Approver_Email', 'Join_Date', 'is_active', 'Password'
        )
        export_order = (
            'Email', 'First_Name', 'Last_Name', 'Employee_Code', 'Role', 'Status', 'Entity_Code',
            'Location_Name', 'Department_Code', 'Approver_Email', 'Join_Date', 'is_active'
        )
        skip_unchanged = True
        report_skipped = True

    def after_save_instance(self, instance, row, **kwargs):
        """Hash password and ensure first_login after save."""
        # Get password from row (cleaned by PasswordWidget)
        raw_password = row.get('Password', '').strip() or DEFAULT_IMPORT_PASSWORD
        # set_password hashes properly — Model.save() stores plain text
        instance.set_password(raw_password)
        instance.first_login = True
        instance.save(update_fields=['password', 'first_login'])

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
