# Testing Guidelines

**Last Updated:** 2026-02-07

---

## Testing Strategy

**Target Coverage:**
- Backend: 80% minimum (critical paths 90%)
- Frontend: 70% minimum

**Test Types:**
- Unit Tests: Test individual functions/components
- Integration Tests: Test API endpoints, database
- E2E Tests: Test user workflows (future)

---

## Backend Testing (pytest)

### Project Structure

```
app_name/
├── tests/
│   ├── __init__.py
│   ├── test_models.py       # Model tests
│   ├── test_views.py        # API endpoint tests
│   ├── test_services.py     # Service/business logic tests
│   ├── test_serializers.py  # Serializer validation
│   └── fixtures.py          # Shared test fixtures
├── models.py
└── ...
```

### Running Tests

```bash
# All tests
python -m pytest --verbosity=2

# Specific file
python -m pytest app_name/tests/test_models.py

# Specific test
python -m pytest app_name/tests/test_models.py::TestLeaveRequest::test_status_validation

# With coverage
python -m pytest --cov=. --cov-report=html

# Run only failed tests
python -m pytest --lf

# Stop on first failure
python -m pytest -x
```

### Test Example: Model Tests

```python
# tests/test_models.py
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from leaves.models import LeaveRequest, LeaveBalance

User = get_user_model()

@pytest.mark.django_db
class TestLeaveRequest:
    """Test LeaveRequest model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email='emp@test.com',
            password='test123'
        )
        self.leave = LeaveRequest.objects.create(
            user=self.user,
            category_id='VACATION',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            hours=Decimal('8.0'),
            status='PENDING'
        )

    def test_leave_string_representation(self):
        """Test __str__ method."""
        expected = f"{self.user.email} - {self.leave.start_date}"
        assert str(self.leave) == expected

    def test_status_validation(self):
        """Test status choices."""
        self.leave.status = 'INVALID'
        with pytest.raises(ValidationError):
            self.leave.full_clean()

    def test_hours_precision(self):
        """Test Decimal precision for hours."""
        self.leave.hours = Decimal('16.50')
        self.leave.save()
        self.leave.refresh_from_db()
        assert self.leave.hours == Decimal('16.50')
```

### Test Example: API Endpoint Tests

```python
# tests/test_views.py
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

@pytest.mark.django_db
class TestLeaveRequestAPI:
    """Test Leave Request API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = APIClient()
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

    def test_create_leave_request_authenticated(self):
        """Test creating leave request as authenticated user."""
        self.client.force_authenticate(user=self.user)

        data = {
            'category': 'VACATION',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=1),
            'hours': 16.0,
            'notes': 'Vacation'
        }

        response = self.client.post(
            '/api/v1/leaves/requests/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'PENDING'

    def test_create_leave_request_unauthenticated(self):
        """Test creating leave request without authentication."""
        data = {
            'category': 'VACATION',
            'start_date': date.today(),
            'hours': 8.0
        }

        response = self.client.post(
            '/api/v1/leaves/requests/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_approve_leave_with_balance_deduction(self):
        """Test atomic approval with balance deduction."""
        # Create balance
        balance = LeaveBalance.objects.create(
            user=self.user,
            category_id='VACATION',
            hours=Decimal('80.00')
        )

        # Create leave request
        leave = LeaveRequest.objects.create(
            user=self.user,
            category_id='VACATION',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            hours=Decimal('16.0'),
            status='PENDING'
        )

        self.client.force_authenticate(user=self.approver)

        response = self.client.put(
            f'/api/v1/leaves/requests/{leave.id}/approve/',
            {'notes': 'Approved'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify balance deducted
        balance.refresh_from_db()
        assert balance.hours == Decimal('64.00')

        # Verify leave status changed
        leave.refresh_from_db()
        assert leave.status == 'APPROVED'
```

### Test Example: Service Tests

```python
# tests/test_services.py
import pytest
from decimal import Decimal
from datetime import date, timedelta

from leaves.services import LeaveApprovalService
from leaves.exceptions import InsufficientBalance

@pytest.mark.django_db
class TestLeaveApprovalService:
    """Test LeaveApprovalService business logic."""

    def test_approve_insufficient_balance_raises_error(self):
        """Test approval with insufficient balance."""
        user = User.objects.create_user(email='emp@test.com')
        approver = User.objects.create_user(email='mgr@test.com')
        user.approver = approver
        user.save()

        balance = LeaveBalance.objects.create(
            user=user,
            category_id='VACATION',
            hours=Decimal('8.0')
        )

        leave = LeaveRequest.objects.create(
            user=user,
            category_id='VACATION',
            start_date=date.today(),
            hours=Decimal('16.0'),
            status='PENDING'
        )

        service = LeaveApprovalService()

        with pytest.raises(InsufficientBalance):
            service.approve(leave, approver)

        # Verify balance unchanged
        balance.refresh_from_db()
        assert balance.hours == Decimal('8.0')
```

---

## Frontend Testing (Jest/Vitest)

### Project Structure

```
src/
├── components/
│   ├── Button.tsx
│   └── __tests__/
│       └── Button.test.tsx
├── pages/
│   ├── Dashboard.tsx
│   └── __tests__/
│       └── Dashboard.test.tsx
└── api/
    ├── leaveApi.js
    └── __tests__/
        └── leaveApi.test.js
```

### Running Tests

```bash
cd frontend

# All tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific file
npm test -- Button.test.tsx
```

### Component Test Example

```typescript
// __tests__/LeaveRequestModal.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LeaveRequestModal from '../LeaveRequestModal';

describe('LeaveRequestModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders modal when visible prop is true', () => {
    render(
      <LeaveRequestModal
        visible={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        userId="123"
      />
    );

    expect(screen.getByText('New Leave Request')).toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', async () => {
    const user = userEvent.setup();

    render(
      <LeaveRequestModal
        visible={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        userId="123"
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('submits form data and closes modal', async () => {
    mockOnSubmit.mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(
      <LeaveRequestModal
        visible={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        userId="123"
      />
    );

    await user.type(
      screen.getByLabelText(/Start Date/i),
      '2026-02-10'
    );
    await user.type(screen.getByLabelText(/Hours/i), '8');
    await user.click(screen.getByRole('button', { name: /Submit/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          startDate: '2026-02-10',
          hours: 8
        })
      );
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('displays error message on submit failure', async () => {
    mockOnSubmit.mockRejectedValue(new Error('API Error'));
    const user = userEvent.setup();

    render(
      <LeaveRequestModal
        visible={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        userId="123"
      />
    );

    await user.click(screen.getByRole('button', { name: /Submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

### Hook Test Example

```typescript
// __tests__/use-notifications.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useNotifications } from '../use-notifications';
import * as notificationApi from '../../api/notificationApi';

jest.mock('../../api/notificationApi');

describe('useNotifications', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches notifications on mount', async () => {
    const mockNotifications = {
      data: {
        results: [
          { id: '1', title: 'Request Approved', is_read: false }
        ],
        unread_count: 1
      }
    };

    jest.spyOn(notificationApi, 'listNotifications')
      .mockResolvedValue(mockNotifications);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => {
      expect(result.current.unreadCount).toBe(1);
      expect(result.current.notifications).toHaveLength(1);
    });
  });

  it('sets up polling interval', async () => {
    jest.useFakeTimers();
    jest.spyOn(notificationApi, 'listNotifications')
      .mockResolvedValue({
        data: { results: [], unread_count: 0 }
      });

    renderHook(() => useNotifications());

    expect(setInterval).toHaveBeenCalledWith(
      expect.any(Function),
      30000
    );

    jest.useRealTimers();
  });
});
```

---

## Test Data & Fixtures

### Shared Fixtures

```python
# conftest.py (pytest configuration)
import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='test123'
    )

@pytest.fixture
def approver():
    """Create test approver."""
    return User.objects.create_user(
        email='approver@example.com',
        password='test123'
    )

@pytest.fixture
def leave_balance(user):
    """Create test leave balance."""
    from leaves.models import LeaveBalance
    return LeaveBalance.objects.create(
        user=user,
        category_id='VACATION',
        hours=Decimal('80.00')
    )
```

---

## Coverage Requirements

**Acceptable Coverage:**
- New code: 100% (aim for this)
- Modified code: 80% minimum
- Legacy code: Improve by 5-10%
- Overall project: 80% minimum

**Generate Coverage Report:**

```bash
# Backend
python -m pytest --cov=leaves --cov-report=html

# Frontend
npm test -- --coverage
```

---

## Testing Best Practices

1. **Arrange-Act-Assert Pattern**
   ```python
   # Arrange: Set up test data
   user = User.objects.create_user(email='test@test.com')

   # Act: Perform the action
   result = some_function(user)

   # Assert: Verify the result
   assert result == expected_value
   ```

2. **Avoid Test Interdependency**
   ```python
   # Good: Each test is independent
   def test_create_user(self):
       user = User.objects.create_user(...)
       assert user.id is not None

   # Avoid: Tests depending on other tests
   def test_user_exists(self):
       # Relies on test_create_user running first
   ```

3. **Use Meaningful Names**
   ```python
   # Good
   def test_approve_with_insufficient_balance_raises_error(self):
       pass

   # Avoid
   def test_approve(self):
       pass
   ```

4. **Mock External Dependencies**
   ```python
   @patch('leaves.services.send_notification')
   def test_approve_sends_notification(self, mock_send):
       # Test without actually sending notification
       service.approve(leave, approver)
       mock_send.assert_called_once()
   ```

---

*Follow these guidelines to maintain high-quality, maintainable test code.*
