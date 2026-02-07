# Backend Code Standards (Django/Python)

**Last Updated:** 2026-02-07

---

## File Naming Conventions

```
kebab-case for modules: user_auth.py, leave_approval_service.py
PascalCase for classes: LeaveRequest, DepartmentManager
snake_case for functions and variables: get_working_days(), user_approver
SCREAMING_SNAKE_CASE for constants: MAX_LEAVE_HOURS, DEFAULT_WORKDAY_HOURS
```

---

## File Organization

**Maximum LOC per file:** 200 lines (split larger files into modules)

**Django app structure:**
```
app_name/
├── models.py           # < 300 LOC (split large models)
├── views/              # Directory for multiple views
│   ├── __init__.py
│   ├── requests.py
│   ├── balances.py
│   └── ...
├── serializers.py      # < 250 LOC
├── services.py         # Business logic (< 300 LOC per service)
├── utils.py            # Helper functions
├── constants.py        # Enums, constants
├── permissions.py      # Permission classes
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
├── migrations/         # Auto-generated
├── admin.py           # Django admin
├── apps.py            # App config
├── urls.py            # URL routing
└── signals.py         # Django signals
```

---

## Naming Conventions

**Models:**
```python
# Good
class LeaveRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

# Avoid
class LeaveReq(models.Model):  # Too abbreviated
    usr = models.ForeignKey(User, on_delete=models.CASCADE)
```

**Views/Viewsets:**
```python
# Good
class LeaveRequestViewSet(viewsets.ModelViewSet):
    def approve_leave(self, request, pk=None):
        ...

# Avoid
class LRViewSet(viewsets.ModelViewSet):
    def approve(self, request, pk=None):
```

**Serializers:**
```python
# Good
class LeaveRequestDetailedSerializer(serializers.ModelSerializer):
    approved_by_user = UserMinimalSerializer(read_only=True)

# Avoid
class LeaveRequestSer(serializers.ModelSerializer):
    approver = UserSerializer(read_only=True)
```

**Functions:**
```python
# Good
def calculate_working_days_between(start_date, end_date, exclude_holidays=None):
    """Calculate business days excluding weekends and holidays."""

# Avoid
def calc_days(sd, ed):  # Abbreviated, unclear
    pass
```

---

## Code Style (PEP 8)

```python
# Imports
import os
import json
from typing import Optional, List, Dict
from decimal import Decimal

from django.db import models
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from .models import LeaveRequest
from .services import LeaveApprovalService

# Line length: 88 characters (Black compatible)
# Blank lines: 2 between classes, 1 between methods

class LeaveRequest(models.Model):
    """Model representing a single leave request with full lifecycle."""

    DEFAULT_WORKDAY_HOURS = 8

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(LeaveCategory, on_delete=models.PROTECT)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=LEAVE_STATUS_CHOICES,
        default='PENDING'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Request'

    def __str__(self):
        return f"{self.user.email} - {self.start_date}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

---

## Type Hints

Always use type hints for function signatures:

```python
from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import date

def get_leave_balance(
    user_id: int,
    category: str,
    as_of_date: Optional[date] = None
) -> Optional[Decimal]:
    """Get leave balance for a user."""
    pass

def detect_overlapping_leaves(
    user_id: int,
    start_date: date,
    end_date: date
) -> List[LeaveRequest]:
    """Return list of overlapping leave requests."""
    pass
```

---

## Docstrings (Google Style)

```python
def approve_leave_request(
    leave_id: int,
    approver_id: int,
    notes: str = ""
) -> Tuple[bool, str]:
    """
    Approve a leave request atomically.

    Deducts hours from user's balance and changes status to APPROVED.
    Creates audit log and sends notification.

    Args:
        leave_id: Leave request ID to approve
        approver_id: Approver user ID
        notes: Optional approval notes (max 500 chars)

    Returns:
        Tuple of (success: bool, message: str)

    Raises:
        LeaveRequest.DoesNotExist: If leave_id not found
        InsufficientBalance: If user has insufficient balance
        PermissionDenied: If approver is not assigned
    """
    pass
```

---

## Error Handling

Always catch specific exceptions:

```python
from django.core.exceptions import PermissionDenied
from decimal import InvalidOperation

try:
    balance = LeaveBalance.objects.get(user_id=user_id)
    balance.hours -= Decimal(hours_to_deduct)
    balance.save()
except LeaveBalance.DoesNotExist:
    raise ValidationError(f"No balance found")
except InvalidOperation:
    raise ValidationError("Invalid decimal operation")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# Avoid
try:
    # ... code ...
except:  # Catches everything
    pass
```

---

## Decimal Precision

Always use `Decimal` for financial calculations:

```python
from decimal import Decimal, ROUND_HALF_UP

# Good
hours = Decimal('8.0')  # String, not float
balance = Decimal('80.50')

result = (balance * Decimal('0.5')).quantize(
    Decimal('0.01'),
    rounding=ROUND_HALF_UP
)

# Avoid
hours = 8.0  # Float, imprecise
balance = 80.50
result = balance * 0.5
```

---

## Years of Service Calculation

Standard implementation for dynamic EXEMPT_VACATION:

```python
from datetime import date
from math import floor

def calculate_exempt_vacation_hours(
    join_date: date,
    reference_date: date = None
) -> Decimal:
    """
    Calculate EXEMPT_VACATION hours based on years of service.

    Tiers:
        Year 1: Prorated by month (8h/month × months worked)
        Years 2-5: 80 hours
        Years 6-10: 120 hours
        Years 11-15: 160 hours
        Years 16+: 200 hours

    Note: YoS = floor((ref_date - join_date).days / 365.25) + 1
    """
    if reference_date is None:
        reference_date = date(date.today().year, 1, 1)

    days_employed = (reference_date - join_date).days
    yos = floor(days_employed / 365.25) + 1

    if yos == 1:
        months_worked = days_employed // 30
        return Decimal(str(8 * months_worked))
    elif yos <= 5:
        return Decimal('80')
    elif yos <= 10:
        return Decimal('120')
    elif yos <= 15:
        return Decimal('160')
    else:
        return Decimal('200')
```

---

## Database Queries

Optimize queries to avoid N+1 problems:

```python
# Good: Use select_related for ForeignKey
leaves = LeaveRequest.objects.filter(
    user__entity=entity
).select_related('user', 'category', 'approved_by')

# Good: Use prefetch_related for ManyToMany
departments = Department.objects.all().prefetch_related('managers')

# Good: Limit fields retrieved
users = User.objects.filter(
    is_active=True
).values_list('id', 'email', 'name')

# Bad: N+1 query problem
leaves = LeaveRequest.objects.all()
for leave in leaves:
    print(leave.user.email)  # Query per iteration
```

### Calendar Visibility Patterns

Entity-level filtering with bidirectional approser visibility:

```python
from django.db.models import Q

# TeamCalendarView pattern: entity + subordinates + approver
team_filters = Q(entity=user.entity)
subordinate_filter = Q(approver=user)
approver_filter = Q(id=user.approver.pk) if user.approver else Q()

team_members = User.objects.filter(
    team_filters | subordinate_filter | approver_filter
).filter(is_active=True).distinct()
```

### Holiday Scoping Patterns

Cascading scoping (Global → Entity → Location) with correct field references:

```python
# PublicHoliday model fields: holiday_name, start_date, end_date, entity, location
# NOTE: Use 'holiday_name' NOT 'name' for holiday display name

holidays_query = PublicHoliday.objects.filter(
    is_active=True
).filter(
    Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
).filter(
    Q(entity=user.entity) | Q(entity__isnull=True)  # Entity or global
)

# Add location filter if applicable
if user.location:
    holidays_query = holidays_query.filter(
        Q(location=user.location) | Q(location__isnull=True)
    )

# Correct field access
for holiday in holidays_query:
    print(holiday.holiday_name)  # Correct
    # print(holiday.name)  # WRONG - field doesn't exist
```

---

## API Response Format

Consistent JSON structure:

```python
# Success (200, 201)
{
    "success": true,
    "message": "Leave request created successfully",
    "data": {
        "id": 123,
        "user_id": 456,
        "status": "PENDING"
    }
}

# Error (400, 401, 403, 404, 500)
{
    "success": false,
    "message": "Insufficient leave balance",
    "error_code": "INSUFFICIENT_BALANCE",
    "details": {
        "field": "hours",
        "available": 8,
        "requested": 16
    }
}
```

---

## Testing Example

```python
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model

from leaves.models import LeaveRequest, LeaveBalance
from leaves.services import LeaveApprovalService

User = get_user_model()

class TestLeaveApprovalService(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='emp@test.com',
            password='test123'
        )
        self.approver = User.objects.create_user(
            email='mgr@test.com',
            password='test123'
        )
        self.user.approver = self.approver
        self.user.save()

    def test_approve_deducts_balance(self):
        leave = LeaveRequest.objects.create(
            user=self.user,
            category_id='VACATION',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            hours=Decimal('16.0'),
            status='PENDING'
        )

        service = LeaveApprovalService()
        service.approve(leave, self.approver)

        balance = LeaveBalance.objects.get(user=self.user)
        self.assertEqual(balance.hours, Decimal('64.00'))
```

---

## Common Patterns

**Service Classes for Business Logic:**
```python
class LeaveApprovalService:
    def approve(self, leave: LeaveRequest, approver: User) -> None:
        with transaction.atomic():
            balance = LeaveBalance.objects.select_for_update().get(...)
            balance.hours -= leave.hours
            balance.save()
            leave.status = 'APPROVED'
            leave.save()
            # Create audit log, notification
```

**Permission Checks:**
```python
class IsApprover(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user.approver
```

---

*See [testing-guidelines.md](./testing-guidelines.md) for detailed testing patterns.*
