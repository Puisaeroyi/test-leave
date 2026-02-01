"""
Django admin configuration for Organization models with import/export support.
"""
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
import tablib

from .models import Entity, Location, Department, DepartmentManager, UnifiedImportPlaceholder
from .resources import (
    EntityResource,
    LocationResource,
    DepartmentResource,
    FlatUnifiedOrganizationResource
)


@admin.register(Entity)
class EntityAdmin(ImportExportModelAdmin):
    """Admin for Entity with import/export support."""
    resource_class = EntityResource
    list_display = ['entity_name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['entity_name', 'code']
    formats = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]


@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    """Admin for Location with import/export support."""
    resource_class = LocationResource
    list_display = ['location_name', 'city', 'country', 'entity', 'is_active']
    list_filter = ['is_active', 'entity']
    search_fields = ['location_name', 'city']
    formats = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    """Admin for Department with import/export support."""
    resource_class = DepartmentResource
    list_display = ['department_name', 'code', 'entity', 'is_active']
    list_filter = ['is_active', 'entity']
    search_fields = ['department_name', 'code']
    formats = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]


@admin.register(DepartmentManager)
class DepartmentManagerAdmin(admin.ModelAdmin):
    """Admin for DepartmentManager."""
    list_display = ['manager', 'entity', 'department', 'location', 'is_active']
    list_filter = ['is_active', 'entity', 'department', 'location']
    search_fields = ['manager__email']


class UnifiedOrganizationImportAdmin(admin.ModelAdmin):
    """
    Custom admin view for unified organization import.
    Handles CSV/XLSX with flat format: Entity_Name, Entity_Code, Location_Name, Location_City,
    Location_State, Location_Country, Location_Timezone, Department_Name, Department_Code
    Includes preview step before confirmation.
    """
    change_list_template = 'admin/organizations/unified_import_changelist.html'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def changelist_view(self, request, extra_context=None):
        """Redirect to unified import page - no database table needed."""
        from django.shortcuts import redirect
        return redirect('./unified-import/')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'unified-import/',
                self.admin_site.admin_view(self.unified_import_view),
                name='organizations_unified_import'
            ),
            path(
                'unified-import/preview/',
                self.admin_site.admin_view(self.unified_import_preview),
                name='organizations_unified_import_preview'
            ),
            path(
                'unified-import/confirm/',
                self.admin_site.admin_view(self.unified_import_confirm),
                name='organizations_unified_import_confirm'
            ),
        ]
        return custom_urls + urls

    def unified_import_view(self, request):
        """Handle unified organization import - shows upload form."""
        if request.method == 'POST' and request.FILES.get('import_file'):
            import_file = request.FILES['import_file']

            try:
                # Determine file format and load dataset
                filename = import_file.name.lower()
                if filename.endswith('.xlsx'):
                    dataset = tablib.Dataset().load(import_file.read(), format='xlsx')
                elif filename.endswith('.csv'):
                    dataset = tablib.Dataset().load(
                        import_file.read().decode('utf-8'),
                        format='csv'
                    )
                else:
                    messages.error(request, 'Unsupported file format. Use CSV or XLSX.')
                    return render(request, 'admin/organizations/unified_import.html', {
                        'title': 'Organization Import',
                    })

                # Run dry run to get preview data
                results = FlatUnifiedOrganizationResource.import_flat_data(
                    dataset,
                    dry_run=True
                )

                # Store dataset as JSON (preserves dict structure)
                import json
                request.session['import_dataset'] = json.loads(json.dumps(dataset.dict))
                request.session['import_results_preview'] = results

                # Redirect to preview page (relative to current unified-import URL)
                return redirect('preview/')

            except Exception as e:
                messages.error(request, f'Import error: {str(e)}')
                return render(request, 'admin/organizations/unified_import.html', {
                    'title': 'Organization Import',
                })

        return render(request, 'admin/organizations/unified_import.html', {
            'title': 'Organization Import',
        })

    def unified_import_preview(self, request):
        """Show preview of what will be imported."""
        # Get preview data from session
        results = request.session.get('import_results_preview')
        dataset = request.session.get('import_dataset')

        if not results or not dataset:
            messages.warning(request, 'No import data found. Please upload a file first.')
            return redirect('../unified-import/')

        # Calculate totals
        total_created = sum(r['created'] for r in results.values())
        total_updated = sum(r['updated'] for r in results.values())
        total_errors = sum(len(r['errors']) for r in results.values())

        # Count rows per type
        entity_rows = sum(1 for row in dataset if row.get('Entity_Name') and row.get('Entity_Code'))
        location_rows = sum(1 for row in dataset if row.get('Location_Name') and row.get('Location_City'))
        department_rows = sum(1 for row in dataset if row.get('Department_Name') and row.get('Department_Code'))

        return render(request, 'admin/organizations/unified_import_preview.html', {
            'title': 'Preview Import',
            'results': results,
            'total_created': total_created,
            'total_updated': total_updated,
            'total_errors': total_errors,
            'dataset': dataset[:10],  # Show first 10 rows
            'total_rows': len(dataset),
            'entity_rows': entity_rows,
            'location_rows': location_rows,
            'department_rows': department_rows,
            'preview_rows': dataset[:10],
        })

    def unified_import_confirm(self, request):
        """Confirm and execute the actual import."""
        # Get dataset from session
        dataset_dict = request.session.get('import_dataset')

        if not dataset_dict:
            messages.warning(request, 'No import data found. Please upload a file first.')
            return redirect('../unified-import/')

        try:
            # Convert back to tablib Dataset with headers
            dataset = tablib.Dataset()
            if dataset_dict:
                # Set headers from first row
                dataset.headers = list(dataset_dict[0].keys())
                # Add rows
                for row in dataset_dict:
                    dataset.append([row.get(h, '') for h in dataset.headers])

            # Run actual import (not dry run)
            results = FlatUnifiedOrganizationResource.import_flat_data(
                dataset,
                dry_run=False
            )

            # Clear session data
            request.session.pop('import_dataset', None)
            request.session.pop('import_results_preview', None)

            # Show results
            total_created = sum(r['created'] for r in results.values())
            total_updated = sum(r['updated'] for r in results.values())
            total_errors = sum(len(r['errors']) for r in results.values())

            if total_errors > 0:
                for model_type, data in results.items():
                    for error in data['errors']:
                        messages.warning(request, f"{model_type}: {error}")

            messages.success(
                request,
                f"Import complete: {total_created} created, {total_updated} updated, "
                f"{total_errors} errors"
            )

        except Exception as e:
            messages.error(request, f'Import error: {str(e)}')

        return redirect('..')


# Register the unified import admin with the placeholder model
admin.site.register(UnifiedImportPlaceholder, UnifiedOrganizationImportAdmin)
