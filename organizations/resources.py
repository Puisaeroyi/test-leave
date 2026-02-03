"""
Django import-export resources for Organization models.
Supports CSV/XLSX import with flat unified format (Entity + Location + Department in one row).
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from .models import Entity, Location, Department


class DefaultTrueBooleanWidget(BooleanWidget):
    """Boolean widget that defaults to True when value is empty or missing."""

    def clean(self, value, row=None, **kwargs):
        if value is None or value == '' or str(value).strip() == '':
            return True
        return super().clean(value, row, **kwargs)


class EntityResource(resources.ModelResource):
    """Import/export resource for Entity model."""
    is_active = fields.Field(
        column_name='is_active',
        attribute='is_active',
        widget=DefaultTrueBooleanWidget(),
        default=True
    )

    class Meta:
        model = Entity
        import_id_fields = ['code']
        fields = ('entity_name', 'code', 'is_active')
        export_order = ('entity_name', 'code', 'is_active')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Ensure is_active defaults to True if not provided."""
        if 'is_active' not in row or row.get('is_active') in [None, '', 'None']:
            row['is_active'] = True


class LocationResource(resources.ModelResource):
    """Import/export resource for Location model."""
    entity = fields.Field(
        column_name='Entity_Code',
        attribute='entity',
        widget=ForeignKeyWidget(Entity, field='code')
    )
    is_active = fields.Field(
        column_name='is_active',
        attribute='is_active',
        widget=DefaultTrueBooleanWidget(),
        default=True
    )

    class Meta:
        model = Location
        import_id_fields = ['entity', 'location_name']
        fields = ('location_name', 'Entity_Code', 'city', 'state', 'country', 'timezone', 'is_active')
        export_order = ('location_name', 'Entity_Code', 'city', 'state', 'country', 'timezone', 'is_active')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Ensure is_active defaults to True if not provided."""
        if 'is_active' not in row or row.get('is_active') in [None, '', 'None']:
            row['is_active'] = True


class DepartmentResource(resources.ModelResource):
    """Import/export resource for Department model."""
    entity = fields.Field(
        column_name='Entity_Code',
        attribute='entity',
        widget=ForeignKeyWidget(Entity, field='code')
    )
    location = fields.Field(
        column_name='Location_Name',
        attribute='location',
        widget=ForeignKeyWidget(Location, field='location_name')
    )
    is_active = fields.Field(
        column_name='is_active',
        attribute='is_active',
        widget=DefaultTrueBooleanWidget(),
        default=True
    )

    class Meta:
        model = Department
        import_id_fields = ['entity', 'location', 'code']
        fields = ('department_name', 'code', 'Entity_Code', 'Location_Name', 'is_active')
        export_order = ('department_name', 'code', 'Entity_Code', 'Location_Name', 'is_active')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        """Ensure is_active defaults to True if not provided."""
        if 'is_active' not in row or row.get('is_active') in [None, '', 'None']:
            row['is_active'] = True


class FlatUnifiedOrganizationResource:
    """
    Import resource for flat CSV/XLSX format with Entity + Location + Department in one row.
    Format: Entity_Name, Entity_Code, Location_Name, Location_City, Location_State, Location_Country,
            Location_Timezone, Department_Name, Department_Code
    """

    @classmethod
    def import_flat_data(cls, dataset, dry_run=False):
        """
        Process flat CSV/XLSX data with Entity, Location, Department in each row.
        Returns dict with results for each model type.
        """
        results = {
            'entities': {'created': 0, 'updated': 0, 'errors': []},
            'locations': {'created': 0, 'updated': 0, 'errors': []},
            'departments': {'created': 0, 'updated': 0, 'errors': []},
        }

        # Track created entities to avoid duplicates
        entities_cache = {}
        locations_cache = {}

        # Process each row
        for row in dataset.dict:
            try:
                # Skip completely empty rows (trailing newlines in CSV)
                if not row or all(v is None or str(v).strip() == '' for v in row.values()):
                    continue

                # Extract Entity data - handle None values from empty rows
                entity_name = (row.get('Entity_Name') or '').strip()
                entity_code = (row.get('Entity_Code') or '').strip()

                if not entity_name or not entity_code:
                    results['entities']['errors'].append('Missing Entity_Name or Entity_Code')
                    continue

                # Create or get Entity
                if entity_code not in entities_cache:
                    entity, created = Entity.objects.get_or_create(
                        code=entity_code,
                        defaults={'entity_name': entity_name, 'is_active': True}
                    )
                    entities_cache[entity_code] = entity
                    if not dry_run:
                        if created:
                            results['entities']['created'] += 1
                        else:
                            results['entities']['updated'] += 1
                else:
                    entity = entities_cache[entity_code]

                # Extract Location data - handle None values
                location_name = (row.get('Location_Name') or '').strip()
                location_city = (row.get('Location_City') or '').strip()
                location_state = (row.get('Location_State') or '').strip()
                location_country = (row.get('Location_Country') or '').strip()
                location_timezone = (row.get('Location_Timezone') or '').strip()

                if not location_name or not location_city or not location_country:
                    results['locations']['errors'].append(f'Missing required location fields for row: {row}')
                    continue

                # Create unique key for location
                location_key = f"{entity_code}:{location_name}"

                if location_key not in locations_cache:
                    location, created = Location.objects.get_or_create(
                        entity=entity,
                        location_name=location_name,
                        defaults={
                            'city': location_city,
                            'state': location_state,
                            'country': location_country,
                            'timezone': location_timezone,
                            'is_active': True
                        }
                    )
                    locations_cache[location_key] = location
                    if not dry_run:
                        if created:
                            results['locations']['created'] += 1
                        else:
                            results['locations']['updated'] += 1
                else:
                    location = locations_cache[location_key]

                # Extract Department data - handle None values
                department_name = (row.get('Department_Name') or '').strip()
                department_code = (row.get('Department_Code') or '').strip()

                if not department_name or not department_code:
                    results['departments']['errors'].append(f'Missing Department_Name or Department_Code for row: {row}')
                    continue

                # Create Department with location
                department, created = Department.objects.update_or_create(
                    entity=entity,
                    location=location,
                    code=department_code,
                    defaults={
                        'department_name': department_name,
                        'is_active': True
                    }
                )
                if not dry_run:
                    if created:
                        results['departments']['created'] += 1
                    else:
                        results['departments']['updated'] += 1

            except Exception as e:
                results['entities']['errors'].append(f"Row processing error: {str(e)}")

        return results


# Legacy support for old unified format
class UnifiedOrganizationResource(resources.ModelResource):
    """
    Legacy import resource for CSV with format: type,name,code,parent_code,address,is_active.
    This is kept for backward compatibility with old templates.
    """

    class Meta:
        model = Entity  # Base model, but we handle multiple types
        fields = ('type', 'name', 'code', 'parent_code', 'address', 'is_active')

    @classmethod
    def import_unified_data(cls, dataset, dry_run=False):
        """
        Process unified CSV/XLSX data with type column.
        Returns dict with results for each model type.
        """
        results = {
            'entities': {'created': 0, 'updated': 0, 'errors': []},
            'locations': {'created': 0, 'updated': 0, 'errors': []},
            'departments': {'created': 0, 'updated': 0, 'errors': []},
        }

        # First pass: Create entities
        for row in dataset.dict:
            row_type = str(row.get('type', '')).lower().strip()
            if row_type != 'entity':
                continue

            try:
                is_active = cls._parse_is_active(row.get('is_active'))
                entity, created = Entity.objects.update_or_create(
                    code=row.get('code'),
                    defaults={
                        'entity_name': row.get('name'),
                        'is_active': is_active
                    }
                )
                if not dry_run:
                    if created:
                        results['entities']['created'] += 1
                    else:
                        results['entities']['updated'] += 1
            except Exception as e:
                results['entities']['errors'].append(f"Entity {row.get('code')}: {str(e)}")

        # Second pass: Create locations (need entities first)
        for row in dataset.dict:
            row_type = str(row.get('type', '')).lower().strip()
            if row_type != 'location':
                continue

            try:
                parent_code = row.get('parent_code')
                entity = Entity.objects.get(code=parent_code)
                is_active = cls._parse_is_active(row.get('is_active'))

                # Parse address into city (simplified - stores in city field)
                address = row.get('address', '')
                city = address.split(',')[-1].strip() if address else 'Unknown'

                location, created = Location.objects.update_or_create(
                    entity=entity,
                    location_name=row.get('name'),
                    defaults={
                        'city': city,
                        'country': 'Thailand',  # Default country
                        'timezone': 'Asia/Bangkok',  # Default timezone
                        'is_active': is_active
                    }
                )
                if not dry_run:
                    if created:
                        results['locations']['created'] += 1
                    else:
                        results['locations']['updated'] += 1
            except Entity.DoesNotExist:
                results['locations']['errors'].append(
                    f"Location {row.get('name')}: Entity '{parent_code}' not found"
                )
            except Exception as e:
                results['locations']['errors'].append(f"Location {row.get('name')}: {str(e)}")

        # Third pass: Create departments (need entities first)
        for row in dataset.dict:
            row_type = str(row.get('type', '')).lower().strip()
            if row_type != 'department':
                continue

            try:
                parent_code = row.get('parent_code')
                entity = Entity.objects.get(code=parent_code)
                is_active = cls._parse_is_active(row.get('is_active'))

                department, created = Department.objects.update_or_create(
                    entity=entity,
                    code=row.get('code'),
                    defaults={
                        'department_name': row.get('name'),
                        'is_active': is_active
                    }
                )
                if not dry_run:
                    if created:
                        results['departments']['created'] += 1
                    else:
                        results['departments']['updated'] += 1
            except Entity.DoesNotExist:
                results['departments']['errors'].append(
                    f"Department {row.get('code')}: Entity '{parent_code}' not found"
                )
            except Exception as e:
                results['departments']['errors'].append(f"Department {row.get('code')}: {str(e)}")

        return results

    @staticmethod
    def _parse_is_active(value):
        """Parse is_active value, defaulting to True."""
        if value is None or value == '' or str(value).strip() == '':
            return True
        if isinstance(value, bool):
            return value
        str_val = str(value).lower().strip()
        return str_val in ('true', '1', 'yes', 'on', 't', 'y')
