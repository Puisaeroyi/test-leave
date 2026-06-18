from datetime import time

from django.db import migrations


SOC_CYCLE = [
    {
        'name': 'Morning',
        'start_time': '06:00',
        'end_time': '14:00',
        'is_working': True,
    },
    {
        'name': 'Evening',
        'start_time': '14:00',
        'end_time': '22:00',
        'is_working': True,
    },
    {
        'name': 'Night',
        'start_time': '22:00',
        'end_time': '06:00',
        'is_working': True,
    },
    {
        'name': 'Off',
        'is_working': False,
    },
]


def normalize_standard_work_shifts(apps, schema_editor):
    WorkShift = apps.get_model('organizations', 'WorkShift')

    WorkShift.objects.filter(name__iexact='VN SOC').update(
        pattern_type='ROTATING_CYCLE',
        start_time=time(6, 0),
        end_time=time(14, 0),
        includes_weekends=True,
        cycle_days=SOC_CYCLE,
    )
    WorkShift.objects.filter(name__iexact='VN Night Shift').update(
        pattern_type='FIXED_WEEKLY',
        start_time=time(22, 0),
        end_time=time(6, 0),
        includes_weekends=False,
        cycle_days=[],
    )
    WorkShift.objects.filter(name__iexact='US Office Hours').update(
        pattern_type='FIXED_WEEKLY',
        start_time=time(8, 0),
        end_time=time(17, 0),
        includes_weekends=False,
        cycle_days=[],
    )


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0012_workshift_cycle_days_workshift_pattern_type'),
    ]

    operations = [
        migrations.RunPython(
            normalize_standard_work_shifts,
            migrations.RunPython.noop,
        ),
    ]
