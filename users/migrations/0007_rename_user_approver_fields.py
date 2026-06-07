from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_final_approver'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='approver',
            new_name='approver_1',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='final_approver',
            new_name='approver_2',
        ),
        migrations.AlterField(
            model_name='user',
            name='approver_1',
            field=models.ForeignKey(
                blank=True,
                help_text='Approver 1 for leave requests. Cross-entity approval supported.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approver_1_for',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='approver_2',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional approver 2 for leave requests.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approver_2_for',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
