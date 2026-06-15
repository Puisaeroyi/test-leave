from django.db import migrations, models


def backfill_balance_type_snapshot(apps, schema_editor):
    LeaveRequest = apps.get_model("leaves", "LeaveRequest")

    for balance_type in ("VACATION", "SICK", "NONE"):
        LeaveRequest.objects.filter(
            balance_type_snapshot__isnull=True,
            leave_category__balance_bucket=balance_type,
        ).update(balance_type_snapshot=balance_type)

    LeaveRequest.objects.filter(balance_type_snapshot__isnull=True).update(
        balance_type_snapshot="NONE"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("leaves", "0016_leaverequest_end_day_offset_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaverequest",
            name="balance_type_snapshot",
            field=models.CharField(
                blank=True,
                choices=[
                    ("VACATION", "Vacation"),
                    ("SICK", "Sick"),
                    ("NONE", "None"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_balance_type_snapshot, migrations.RunPython.noop),
    ]
