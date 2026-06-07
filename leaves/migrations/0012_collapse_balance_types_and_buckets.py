from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaves', '0011_leaverequest_current_approval_step_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='leavecategory',
            name='balance_bucket',
            field=models.CharField(
                choices=[
                    ('VACATION', 'Vacation'),
                    ('SICK', 'Sick'),
                    ('NONE', 'None'),
                ],
                default='NONE',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='balance_type',
            field=models.CharField(
                choices=[
                    ('VACATION', 'Vacation'),
                    ('SICK', 'Sick Leave'),
                ],
                default='VACATION',
                max_length=30,
            ),
        ),
        migrations.RemoveField(
            model_name='leaverequest',
            name='exempt_type',
        ),
    ]
