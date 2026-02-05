"""
Seed initial data for the Leave Management System
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organizations.models import Entity, Location, Department
from leaves.models import LeaveCategory, LeaveBalance, PublicHoliday
from decimal import Decimal
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed initial data for the Leave Management System'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        # Create Entity
        entity, _ = Entity.objects.get_or_create(
            code='MAIN',
            defaults={'entity_name': 'Main Company', 'is_active': True}
        )
        self.stdout.write(f'  Entity: {entity.entity_name}')

        # Create Locations
        locations = [
            {'location_name': 'Headquarters', 'city': 'New York', 'country': 'USA', 'timezone': 'America/New_York', 'departments': ['Engineering', 'HR', 'Finance']},
            {'location_name': 'Remote', 'city': 'Global', 'country': 'Global', 'timezone': 'UTC', 'departments': ['Operations', 'Marketing']},
        ]
        created_locations = []
        for loc_data in locations:
            dept_names = loc_data.pop('departments', [])
            loc, _ = Location.objects.get_or_create(
                entity=entity,
                location_name=loc_data['location_name'],
                defaults={**loc_data, 'is_active': True}
            )
            created_locations.append({'location': loc, 'departments': dept_names})
            self.stdout.write(f'  Location: {loc.location_name}')

        # Create Departments with location assignments
        departments_map = {
            'Engineering': 'ENG',
            'HR': 'HR',
            'Finance': 'FIN',
            'Marketing': 'MKT',
            'Operations': 'OPS'
        }
        created_departments = []

        for loc_data in created_locations:
            for dept_name in loc_data['departments']:
                code = departments_map.get(dept_name, dept_name[:3].upper())
                dept, created = Department.objects.get_or_create(
                    entity=entity,
                    location=loc_data['location'],
                    code=code,
                    defaults={'department_name': dept_name, 'is_active': True}
                )
                if created:
                    self.stdout.write(f'  Department: {dept.department_name} @ {loc_data["location"].location_name}')
                created_departments.append(dept)

        # Create Leave Categories
        categories = [
            {'category_name': 'Vacation', 'code': 'VACATION', 'sort_order': 1},
            {'category_name': 'Sick Leave', 'code': 'SICK', 'sort_order': 2},
        ]
        for cat_data in categories:
            cat, _ = LeaveCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )
            self.stdout.write(f'  Category: {cat.category_name}')

        # Create Public Holidays for 2026
        holidays = [
            {'holiday_name': "New Year's Day", 'date': date(2026, 1, 1), 'is_recurring': True},
            {'holiday_name': 'Independence Day', 'date': date(2026, 7, 4), 'is_recurring': True},
            {'holiday_name': 'Labor Day', 'date': date(2026, 9, 7), 'is_recurring': False},
            {'holiday_name': 'Thanksgiving', 'date': date(2026, 11, 26), 'is_recurring': False},
            {'holiday_name': 'Christmas Day', 'date': date(2026, 12, 25), 'is_recurring': True},
        ]
        for hol_data in holidays:
            hol, _ = PublicHoliday.objects.get_or_create(
                holiday_name=hol_data['holiday_name'],
                start_date=hol_data['date'],
                end_date=hol_data['date'],
                defaults={
                    'year': hol_data['date'].year,
                    'is_recurring': hol_data['is_recurring'],
                    'is_active': True
                }
            )
            self.stdout.write(f'  Holiday: {hol.holiday_name}')

        # Create Admin User
        hq_location = created_locations[0]['location']
        admin, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'username': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'entity': entity,
                'location': hq_location,
                'department': Department.objects.get(entity=entity, location=hq_location, code='HR'),  # HR @ HQ
            }
        )
        if created:
            admin.set_password('Admin123!')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'  Admin: {admin.email} (password: Admin123!)'))
        else:
            self.stdout.write(f'  Admin: {admin.email} (already exists)')

        # Create HR User
        hr_user, created = User.objects.get_or_create(
            email='hr@example.com',
            defaults={
                'username': 'hr@example.com',
                'first_name': 'HR',
                'last_name': 'Manager',
                'role': 'HR',
                'entity': entity,
                'location': hq_location,
                'department': Department.objects.get(entity=entity, location=hq_location, code='HR'),  # HR @ HQ
            }
        )
        if created:
            hr_user.set_password('Hr123456!')
            hr_user.save()
            LeaveBalance.objects.get_or_create(
                user=hr_user,
                year=2026,
                defaults={'allocated_hours': Decimal('96.00')}
            )
            self.stdout.write(self.style.SUCCESS(f'  HR: {hr_user.email} (password: Hr123456!)'))
        else:
            self.stdout.write(f'  HR: {hr_user.email} (already exists)')

        # Create Manager User
        manager, created = User.objects.get_or_create(
            email='manager@example.com',
            defaults={
                'username': 'manager@example.com',
                'first_name': 'Team',
                'last_name': 'Manager',
                'role': 'MANAGER',
                'entity': entity,
                'location': hq_location,
                'department': Department.objects.get(entity=entity, location=hq_location, code='ENG'),  # Engineering @ HQ
            }
        )
        if created:
            manager.set_password('Manager123!')
            manager.save()
            LeaveBalance.objects.get_or_create(
                user=manager,
                year=2026,
                defaults={'allocated_hours': Decimal('96.00')}
            )
            self.stdout.write(self.style.SUCCESS(f'  Manager: {manager.email} (password: Manager123!)'))
        else:
            self.stdout.write(f'  Manager: {manager.email} (already exists)')

        # Create Employee User
        employee, created = User.objects.get_or_create(
            email='employee@example.com',
            defaults={
                'username': 'employee@example.com',
                'first_name': 'John',
                'last_name': 'Employee',
                'role': 'EMPLOYEE',
                'entity': entity,
                'location': hq_location,
                'department': Department.objects.get(entity=entity, location=hq_location, code='ENG'),  # Engineering @ HQ
            }
        )
        if created:
            employee.set_password('Employee123!')
            employee.save()
            LeaveBalance.objects.get_or_create(
                user=employee,
                year=2026,
                defaults={'allocated_hours': Decimal('96.00')}
            )
            self.stdout.write(self.style.SUCCESS(f'  Employee: {employee.email} (password: Employee123!)'))
        else:
            self.stdout.write(f'  Employee: {employee.email} (already exists)')

        self.stdout.write(self.style.SUCCESS('\nSeed data completed!'))
