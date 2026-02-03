# Generated manually 2026-02-03

from django.db import migrations, models


def copy_date_to_range(apps, schema_editor):
    """Copy date field to start_date and end_date"""
    PublicHoliday = apps.get_model('leaves', 'PublicHoliday')
    for holiday in PublicHoliday.objects.all():
        holiday.start_date = holiday.date
        holiday.end_date = holiday.date
        holiday.save(update_fields=['start_date', 'end_date'])


def reverse_copy_date_to_range(apps, schema_editor):
    """Reverse: copy start_date back to date"""
    PublicHoliday = apps.get_model('leaves', 'PublicHoliday')
    for holiday in PublicHoliday.objects.all():
        holiday.date = holiday.start_date
        holiday.save(update_fields=['date'])


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0001_initial'),
        ('leaves', '0007_attachment_url_allow_null'),
    ]

    operations = [
        # Step 1: Add new fields as nullable
        migrations.AddField(
            model_name='publicholiday',
            name='start_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='publicholiday',
            name='end_date',
            field=models.DateField(null=True),
        ),
        # Step 2: Copy data from date to start_date/end_date
        migrations.RunPython(copy_date_to_range, reverse_copy_date_to_range),
        # Step 3: Make new fields not null
        migrations.AlterField(
            model_name='publicholiday',
            name='start_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='publicholiday',
            name='end_date',
            field=models.DateField(),
        ),
        # Step 4: Drop old unique_together constraint
        migrations.AlterUniqueTogether(
            name='publicholiday',
            unique_together=set(),  # Clear old constraint
        ),
        # Step 5: Remove old date field
        migrations.RemoveField(
            model_name='publicholiday',
            name='date',
        ),
        # Step 6: Add new unique_together constraint
        migrations.AlterUniqueTogether(
            name='publicholiday',
            unique_together={('entity', 'location', 'start_date')},
        ),
        # Step 7: Add index for date range queries
        migrations.AddIndex(
            model_name='publicholiday',
            index=models.Index(fields=['start_date', 'end_date'], name='leaves_holiday_date_idx'),
        ),
    ]
