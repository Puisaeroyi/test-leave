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
            defaults={'name': 'Main Company', 'is_active': True}
        )
        self.stdout.write(f'  Entity: {entity.name}')

        # Create Locations
        locations = [
            {'name': 'Headquarters', 'city': 'New York', 'country': 'USA', 'timezone': 'America/New_York'},
            {'name': 'Remote', 'city': 'Global', 'country': 'Global', 'timezone': 'UTC'},
        ]
        created_locations = []
        for loc_data in locations:
            loc, _ = Location.objects.get_or_create(
                entity=entity,
                name=loc_data['name'],
                defaults=loc_data
            )
            created_locations.append(loc)
            self.stdout.write(f'  Location: {loc.name}')

        # Create Departments
        departments = ['Engineering', 'HR', 'Finance', 'Marketing', 'Operations']
        created_departments = []
        for dept_name in departments:
            dept, _ = Department.objects.get_or_create(
                entity=entity,
                name=dept_name,
                defaults={'is_active': True}
            )
            created_departments.append(dept)
            self.stdout.write(f'  Department: {dept.name}')

        # Create Leave Categories
        categories = [
            {'name': 'Annual Leave', 'code': 'AL', 'color': '#10B981', 'sort_order': 1},
            {'name': 'Sick Leave', 'code': 'SL', 'color': '#EF4444', 'sort_order': 2},
            {'name': 'Personal Leave', 'code': 'PL', 'color': '#3B82F6', 'sort_order': 3},
            {'name': 'Unpaid Leave', 'code': 'UL', 'color': '#6B7280', 'sort_order': 4},
            {'name': 'Maternity Leave', 'code': 'ML', 'color': '#EC4899', 'sort_order': 5, 'requires_document': True},
            {'name': 'Paternity Leave', 'code': 'PAT', 'color': '#8B5CF6', 'sort_order': 6},
        ]
        for cat_data in categories:
            cat, _ = LeaveCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )
            self.stdout.write(f'  Category: {cat.name}')

        # Create Public Holidays for 2026
        holidays = [
            {'name': "New Year's Day", 'date': date(2026, 1, 1), 'is_recurring': True},
            {'name': 'Independence Day', 'date': date(2026, 7, 4), 'is_recurring': True},
            {'name': 'Labor Day', 'date': date(2026, 9, 7), 'is_recurring': False},
            {'name': 'Thanksgiving', 'date': date(2026, 11, 26), 'is_recurring': False},
            {'name': 'Christmas Day', 'date': date(2026, 12, 25), 'is_recurring': True},
        ]
        for hol_data in holidays:
            hol, _ = PublicHoliday.objects.get_or_create(
                name=hol_data['name'],
                date=hol_data['date'],
                defaults={
                    'year': hol_data['date'].year,
                    'is_recurring': hol_data['is_recurring'],
                    'is_active': True
                }
            )
            self.stdout.write(f'  Holiday: {hol.name}')

        # Create Admin User
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
                'location': created_locations[0],
                'department': created_departments[1],  # HR
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
                'location': created_locations[0],
                'department': created_departments[1],  # HR
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
                'location': created_locations[0],
                'department': created_departments[0],  # Engineering
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
                'location': created_locations[0],
                'department': created_departments[0],  # Engineering
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
