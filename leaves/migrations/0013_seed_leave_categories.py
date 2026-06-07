from django.db import migrations


CATEGORIES = [
    {
        'category_name': 'Vacation',
        'code': 'VACATION',
        'balance_bucket': 'VACATION',
        'sort_order': 1,
    },
    {
        'category_name': 'Sick Leave',
        'code': 'SICK',
        'balance_bucket': 'SICK',
        'sort_order': 2,
    },
    {
        'category_name': 'FMLA Leave',
        'code': 'FMLA',
        'balance_bucket': 'NONE',
        'sort_order': 3,
    },
    {
        'category_name': 'Bereavement Leave',
        'code': 'BEREAVEMENT',
        'balance_bucket': 'NONE',
        'sort_order': 4,
    },
    {
        'category_name': 'Jury Duty Leave',
        'code': 'JURY_DUTY',
        'balance_bucket': 'NONE',
        'sort_order': 5,
    },
    {
        'category_name': 'Kin Care (Family Sick) - CA Only',
        'code': 'KIN_CARE',
        'balance_bucket': 'SICK',
        'sort_order': 6,
    },
    {
        'category_name': 'School Activity Leave - CA Only',
        'code': 'SCHOOL_ACTIVITY',
        'balance_bucket': 'NONE',
        'sort_order': 7,
    },
    {
        'category_name': 'Unpaid Leave',
        'code': 'UNPAID',
        'balance_bucket': 'NONE',
        'sort_order': 8,
    },
]


def seed_leave_categories(apps, schema_editor):
    LeaveCategory = apps.get_model('leaves', 'LeaveCategory')

    for category in CATEGORIES:
        existing = (
            LeaveCategory.objects.filter(code=category['code']).first()
            or LeaveCategory.objects.filter(category_name=category['category_name']).first()
        )
        values = {
            **category,
            'requires_document': False,
            'is_active': True,
        }
        if existing:
            for field, value in values.items():
                setattr(existing, field, value)
            existing.save()
        else:
            LeaveCategory.objects.create(**values)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('leaves', '0012_collapse_balance_types_and_buckets'),
    ]

    operations = [
        migrations.RunPython(seed_leave_categories, noop_reverse),
    ]
