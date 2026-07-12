import json
import uuid

from django.db import migrations, models


def group_matching_work_shifts(apps, schema_editor):
    WorkShift = apps.get_model('organizations', 'WorkShift')
    group_ids_by_signature = {}
    shifts = WorkShift.objects.all().order_by('id')

    for shift in shifts.iterator():
        signature = (
            shift.name,
            shift.pattern_type,
            shift.start_time,
            shift.end_time,
            shift.break_start_time,
            shift.break_end_time,
            json.dumps(shift.cycle_days, sort_keys=True),
            shift.includes_weekends,
        )
        shift.management_group_id = group_ids_by_signature.setdefault(
            signature,
            uuid.uuid4(),
        )
        shift.save(update_fields=['management_group_id'])


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0016_hr_vn_holidays_require_leave'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshift',
            name='management_group_id',
            field=models.UUIDField(db_index=True, editable=False, null=True),
        ),
        migrations.RunPython(
            group_matching_work_shifts,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='workshift',
            name='management_group_id',
            field=models.UUIDField(default=uuid.uuid4, db_index=True, editable=False),
        ),
    ]
