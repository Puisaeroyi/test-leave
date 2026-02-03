from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from .models import User
from organizations.models import Entity, Location, Department
from .resources import UserResource


class UserAdminForm(forms.ModelForm):
    """Custom form with cascading dropdowns for entity/location/department"""

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show ALL locations and departments, but with data-entity attributes
        # for JavaScript filtering
        self.fields['location'].queryset = Location.objects.filter(is_active=True)
        self.fields['location'].required = False
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].required = False

        # Add data-entity attributes to location options
        if self.instance.pk:
            self.fields['location'].initial = self.instance.location_id
            self.fields['department'].initial = self.instance.department_id

    def clean(self):
        cleaned_data = super().clean()
        entity = cleaned_data.get('entity')
        location = cleaned_data.get('location')
        department = cleaned_data.get('department')

        # Validate entity consistency
        if entity and location and location.entity != entity:
            raise forms.ValidationError({
                'location': f"Location '{location}' belongs to '{location.entity.name}', not '{entity.name}'"
            })
        if entity and department and department.entity != entity:
            raise forms.ValidationError({
                'department': f"Department '{department}' belongs to '{department.entity.name}', not '{entity.name}'"
            })

        return cleaned_data


@admin.register(User)
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    form = UserAdminForm
    resource_class = UserResource
    list_display = ['employee_code', 'email', 'first_name', 'last_name', 'role', 'status', 'entity', 'location', 'department']
    list_filter = ['role', 'status', 'entity', 'location', 'department']
    search_fields = ['email', 'first_name', 'last_name', 'employee_code']
    ordering = ['-date_joined']
    formats = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]

    fieldsets = (
        (None, {'fields': ('employee_code', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'avatar_url')}),
        ('Role & Status', {'fields': ('role', 'status')}),
        ('Organization', {'fields': ('entity', 'location', 'department', 'join_date')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )

    class Media:
        css = {
            'all': ('css/admin_cascading_dropdowns.css',)
        }
        js = ('js/admin_cascading_dropdowns.js',)

    def get_form(self, request, obj=None, **kwargs):
        """Inject custom widget with data-entity attributes"""
        form = super().get_form(request, obj, **kwargs)

        # Override widget rendering for location field
        if 'location' in form.base_fields:
            class LocationWidget(forms.Select):
                def render_options(self, *args, **kwargs):
                    output = ['<option value="">---------</option>']

                    for location in Location.objects.filter(is_active=True):
                        selected_choices = kwargs.get('selected_choices', [])
                        selected = ' selected' if str(location.id) in selected_choices else ''
                        output.append(
                            f'<option value="{location.id}" data-entity="{location.entity_id}"{selected}>'
                            f'{location.name} ({location.city})</option>'
                        )

                    return mark_safe(''.join(output))

            form.base_fields['location'].widget = LocationWidget()

        # Override widget rendering for department field
        if 'department' in form.base_fields:
            class DepartmentWidget(forms.Select):
                def render_options(self, *args, **kwargs):
                    output = ['<option value="">---------</option>']

                    for department in Department.objects.filter(is_active=True):
                        selected_choices = kwargs.get('selected_choices', [])
                        selected = ' selected' if str(department.id) in selected_choices else ''
                        output.append(
                            f'<option value="{department.id}" data-entity="{department.entity_id}"{selected}>'
                            f'{department.name}</option>'
                        )

                    return mark_safe(''.join(output))

            form.base_fields['department'].widget = DepartmentWidget()

        return form
