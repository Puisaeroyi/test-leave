"""
Django management command to seed initial data for the leave management system
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from organizations.models import Entity, Location, Department, DepartmentManager
from leaves.models import LeaveCategory, LeaveBalance, PublicHoliday

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed initial data for leave management system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Create Entities
        entity1, _ = Entity.objects.get_or_create(
            code='ACME',
            defaults={
                'name': 'ACME Corporation',
                'is_active': True
            }
        )
        self.stdout.write(f'Created Entity: {entity1.name}')

        entity2, _ = Entity.objects.get_or_create(
            code='ACME_SUB',
            defaults={
                'name': 'ACME Subsidiary',
                'is_active': True
            }
        )
        self.stdout.write(f'Created Entity: {entity2.name}')

        # Create Locations
        loc1, _ = Location.objects.get_or_create(
            entity=entity1,
            name='Headquarters',
            defaults={
                'city': 'New York',
                'country': 'USA',
                'timezone': 'America/New_York',
                'is_active': True
            }
        )

        loc2, _ = Location.objects.get_or_create(
            entity=entity1,
            name='West Coast Office',
            defaults={
                'city': 'San Francisco',
                'state': 'CA',
                'country': 'USA',
                'timezone': 'America/Los_Angeles',
                'is_active': True
            }
        )

        loc3, _ = Location.objects.get_or_create(
            entity=entity2,
            name='European Office',
            defaults={
                'city': 'London',
                'country': 'UK',
                'timezone': 'Europe/London',
                'is_active': True
            }
        )
        self.stdout.write(f'Created {Location.objects.count()} locations')

        # Create Departments
        dept1, _ = Department.objects.get_or_create(
            entity=entity1,
            code='ENG',
            defaults={
                'name': 'Engineering',
                'is_active': True
            }
        )

        dept2, _ = Department.objects.get_or_create(
            entity=entity1,
            code='HR',
            defaults={
                'name': 'Human Resources',
                'is_active': True
            }
        )

        dept3, _ = Department.objects.get_or_create(
            entity=entity1,
            code='MKT',
            defaults={
                'name': 'Marketing',
                'is_active': True
            }
        )

        dept4, _ = Department.objects.get_or_create(
            entity=entity1,
            code='FIN',
            defaults={
                'name': 'Finance',
                'is_active': True
            }
        )
        self.stdout.write(f'Created {Department.objects.count()} departments')

        # Create Leave Categories
        categories = [
            {'name': 'Annual Leave', 'code': 'ANNUAL', 'color': '#3B82F6', 'sort_order': 1},
            {'name': 'Sick Leave', 'code': 'SICK', 'color': '#EF4444', 'sort_order': 2},
            {'name': 'Personal Leave', 'code': 'PERSONAL', 'color': '#10B981', 'sort_order': 3},
            {'name': 'Parental Leave', 'code': 'PARENTAL', 'color': '#F59E0B', 'sort_order': 4, 'requires_document': True},
            {'name': 'Bereavement Leave', 'code': 'BEREAVEMENT', 'color': '#6B7280', 'sort_order': 5},
        ]

        for cat_data in categories:
            LeaveCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )

        self.stdout.write(f'Created {LeaveCategory.objects.count()} leave categories')

        # Create Admin User
        admin_user, created = User.objects.get_or_create(
            email='admin@acme.com',
            defaults={
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.Role.ADMIN,
                'status': User.Status.ACTIVE,
                'entity': entity1,
                'location': loc1,
                'department': dept2,
                'join_date': date.today(),
            }
        )
        if created:
            admin_user.set_password('Admin123!')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.email} / Admin123!'))
        else:
            self.stdout.write(f'Admin user already exists: {admin_user.email}')

        # Create HR User
        hr_user, created = User.objects.get_or_create(
            email='hr@acme.com',
            defaults={
                'first_name': 'Jane',
                'last_name': 'HR',
                'role': User.Role.HR,
                'status': User.Status.ACTIVE,
                'entity': entity1,
                'location': loc1,
                'department': dept2,
                'join_date': date.today(),
            }
        )
        if created:
            hr_user.set_password('Hr123!')
            hr_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created HR user: {hr_user.email} / Hr123!'))
        else:
            self.stdout.write(f'HR user already exists: {hr_user.email}')

        # Create Manager User
        manager_user, created = User.objects.get_or_create(
            email='manager@acme.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Manager',
                'role': User.Role.MANAGER,
                'status': User.Status.ACTIVE,
                'entity': entity1,
                'location': loc1,
                'department': dept1,
                'join_date': date.today(),
            }
        )
        if created:
            manager_user.set_password('Manager123!')
            manager_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created manager user: {manager_user.email} / Manager123!'))

            # Assign as department manager
            DepartmentManager.objects.get_or_create(
                department=dept1,
                location=loc1,
                manager=manager_user,
                defaults={'is_active': True}
            )
        else:
            self.stdout.write(f'Manager user already exists: {manager_user.email}')

        # Create sample employees
        employees = [
            {'email': 'alice@acme.com', 'first_name': 'Alice', 'last_name': 'Developer', 'dept': dept1},
            {'email': 'bob@acme.com', 'first_name': 'Bob', 'last_name': 'Designer', 'dept': dept1},
            {'email': 'charlie@acme.com', 'first_name': 'Charlie', 'last_name': 'Specialist', 'dept': dept3},
            {'email': 'diana@acme.com', 'first_name': 'Diana', 'last_name': 'Analyst', 'dept': dept4},
        ]

        for emp_data in employees:
            dept = emp_data.pop('dept')
            user, created = User.objects.get_or_create(
                email=emp_data['email'],
                defaults={
                    **emp_data,
                    'role': User.Role.EMPLOYEE,
                    'status': User.Status.ACTIVE,
                    'entity': entity1,
                    'location': loc1,
                    'department': dept,
                    'join_date': date.today(),
                }
            )
            if created:
                user.set_password('Employee123!')
                user.save()

                # Create leave balance for current year
                current_year = timezone.now().year
                LeaveBalance.objects.get_or_create(
                    user=user,
                    year=current_year,
                    defaults={'allocated_hours': Decimal('96.00')}
                )
                self.stdout.write(f'Created employee: {user.email}')
            else:
                self.stdout.write(f'Employee already exists: {user.email}')

        # Create Public Holidays for current year
        current_year = timezone.now().year
        holidays = [
            {'name': 'New Year Day', 'date': f'{current_year}-01-01', 'entity': entity1, 'location': None, 'recurring': True},
            {'name': 'Memorial Day', 'date': f'{current_year}-05-26', 'entity': entity1, 'location': None, 'recurring': True},
            {'name': 'Independence Day', 'date': f'{current_year}-07-04', 'entity': entity1, 'location': None, 'recurring': True},
            {'name': 'Labor Day', 'date': f'{current_year}-09-01', 'entity': entity1, 'location': None, 'recurring': True},
            {'name': 'Thanksgiving', 'date': f'{current_year}-11-27', 'entity': entity1, 'location': None, 'recurring': True},
            {'name': 'Christmas Day', 'date': f'{current_year}-12-25', 'entity': entity1, 'location': None, 'recurring': True},
        ]

        for holiday_data in holidays:
            PublicHoliday.objects.get_or_create(
                name=holiday_data['name'],
                date=holiday_data['date'],
                entity=holiday_data['entity'],
                defaults={
                    'location': holiday_data['location'],
                    'is_recurring': holiday_data['recurring'],
                    'year': current_year,
                    'is_active': True
                }
            )

        self.stdout.write(self.style.SUCCESS(f'Created {PublicHoliday.objects.count()} public holidays'))

        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))
        self.stdout.write(self.style.WARNING('\nLogin credentials:'))
        self.stdout.write(self.style.WARNING('  Admin: admin@acme.com / Admin123!'))
        self.stdout.write(self.style.WARNING('  HR: hr@acme.com / Hr123!'))
        self.stdout.write(self.style.WARNING('  Manager: manager@acme.com / Manager123!'))
        self.stdout.write(self.style.WARNING('  Employees: alice@acme.com / Employee123!'))
