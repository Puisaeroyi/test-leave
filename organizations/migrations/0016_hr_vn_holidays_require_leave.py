from django.db import migrations


def enable_hr_vn_holiday_leave(apps, schema_editor):
    Department = apps.get_model('organizations', 'Department')

    Department.objects.filter(
        work_shifts__name__iexact='VN Night Shift',
    ).update(
        holiday_requires_leave=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0015_workshift_break_times'),
    ]

    operations = [
        migrations.RunPython(
            enable_hr_vn_holiday_leave,
            migrations.RunPython.noop,
        ),
    ]
