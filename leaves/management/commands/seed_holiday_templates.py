"""Seed reviewed US and Vietnam holiday reference templates."""
from django.core.management.base import BaseCommand

from leaves.holiday_management import seed_holiday_templates


class Command(BaseCommand):
    help = "Seed US 2026-2027 and Vietnam 2026-2035 holiday templates"

    def handle(self, *args, **options):
        templates = seed_holiday_templates()
        for template in templates:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded {template.name}: {template.dates.count()} holidays"
                )
            )
