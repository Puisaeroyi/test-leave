"""Constants for leave management module."""

from django.utils import timezone


# Pagination defaults
DEFAULT_PAGE_SIZE = 20


# Date/time defaults
DEFAULT_MONTH = 1  # January
DEFAULT_YEAR = timezone.now().year


# Leave calculation defaults
DEFAULT_YEARLY_ALLOCATION = 96
