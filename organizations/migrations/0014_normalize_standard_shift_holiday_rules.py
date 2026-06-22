from django.db import migrations


def normalize_standard_shift_holiday_rules(apps, schema_editor):
    Department = apps.get_model('organizations', 'Department')

    Department.objects.filter(work_shifts__name__iexact='VN SOC').update(
        holiday_requires_leave=True,
    )
    Department.objects.filter(
        work_shifts__name__iexact='VN Night Shift',
    ).update(
        holiday_requires_leave=False,
    )
    Department.objects.filter(
        work_shifts__name__iexact='US Office Hours',
    ).update(
        holiday_requires_leave=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0013_normalize_standard_work_shifts'),
    ]

    operations = [
        migrations.RunPython(
            normalize_standard_shift_holiday_rules,
            migrations.RunPython.noop,
        ),
    ]
