from datetime import time

from django.db import migrations, models


def set_us_office_lunch_break(apps, schema_editor):
    WorkShift = apps.get_model('organizations', 'WorkShift')
    WorkShift.objects.filter(name__iexact='US Office Hours').update(
        break_start_time=time(12, 0),
        break_end_time=time(13, 0),
    )


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0014_normalize_standard_shift_holiday_rules'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshift',
            name='break_end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workshift',
            name='break_start_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.RunPython(
            set_us_office_lunch_break,
            migrations.RunPython.noop,
        ),
    ]
