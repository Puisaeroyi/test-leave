"""Constants for leave management module."""

from django.utils import timezone


# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# Date/time defaults
DEFAULT_MONTH = 1  # January
DEFAULT_YEAR = timezone.now().year


# Leave calculation defaults
HOURS_PER_DAY = 8.0
DEFAULT_YEARLY_ALLOCATION = 96


# Request status limits
MAX_REQUEST_DURATION_DAYS = 365


# Calendar display
CALENDAR_MONTHS_AHEAD = 12
CALENDAR_MONTHS_BEHIND = 1


# Initial onboarding balance (21 days = 168 hours)
INITIAL_ONBOARDING_HOURS = 168
