from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0012_delete_workshift"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="department",
            name="holiday_requires_leave",
        ),
    ]
