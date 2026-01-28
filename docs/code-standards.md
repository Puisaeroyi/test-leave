# Code Standards & Development Guidelines

**Project:** Leave Management System
**Version:** 1.0.0
**Last Updated:** 2026-01-27

---

## Python & Django Standards

### File Naming

- **Module files:** `snake_case.py`
  - `models.py`, `views.py`, `serializers.py`, `urls.py`, `utils.py`
  - Services: `approval_service.py`, `notification_service.py`

- **App directories:** `snake_case/`
  - `users/`, `organizations/`, `leaves/`, `core/`

### Code Style

**PEP 8 Compliance:**
- Line length: 100 characters max (Django convention)
- Indentation: 4 spaces
- Two blank lines between classes/functions at module level
- One blank line between methods

**Imports:**
```python
# Order: stdlib, third-party, local
import os
from typing import Optional, List

from django.db import models
from rest_framework import serializers

from .utils import calculate_working_hours
```

**Naming Conventions:**

| Item | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase | `LeaveRequest`, `LeaveApprovalService` |
| Functions | snake_case | `validate_leave_dates()`, `get_user_balance()` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_HOURS_PER_DAY = 8` |
| Private | `_leading_underscore` | `_calculate_weekends()` |
| Protected | `__dunder__` (rarely) | For Django overrides |

---

### Django Model Standards

**Model Definition:**
```python
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class LeaveRequest(models.Model):
    """Leave request with full lifecycle tracking."""

    # Status choices
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
    ]

    # Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(LeaveCategory, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    hours_requested = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.5)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.user} - {self.category} ({self.status})"

    def get_working_hours(self):
        """Calculate actual working hours excluding weekends/holidays."""
        # Implementation in utils.py
        pass
```

**Model Standards:**
- All models inherit from `django.db.models.Model`
- Include `created_at` and `updated_at` timestamps
- Define string representation with `__str__`
- Add indexes for frequently queried fields
- Use `help_text` for clarity in admin
- Define `Meta` class with ordering and constraints
- Add docstrings to custom methods

---

### View & Serializer Standards

**ViewSet Pattern:**
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class LeaveRequestViewSet(viewsets.ModelViewSet):
    """Leave request CRUD and approval actions."""

    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by user department."""
        user = self.request.user
        return LeaveRequest.objects.filter(user__department=user.department)

    @action(detail=True, methods=['PUT'], permission_classes=[IsManagerOrAdmin])
    def approve(self, request, pk=None):
        """Approve a leave request."""
        leave_request = self.get_object()
        leave_request.status = 'APPROVED'
        leave_request.save()
        return Response(LeaveRequestSerializer(leave_request).data)

    def perform_create(self, serializer):
        """Automatically set user on creation."""
        serializer.save(user=self.request.user)
```

**Serializer Pattern:**
```python
from rest_framework import serializers

class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serialization for leave requests with validation."""

    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'user', 'user_name', 'category', 'category_name',
            'start_date', 'end_date', 'hours_requested', 'status',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status']

    def validate(self, data):
        """Validate date range and hours."""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before end date.")
        if data['hours_requested'] < 0.5:
            raise serializers.ValidationError("Minimum 0.5 hours required.")
        return data
```

---

### Service Layer Pattern

**Business Logic Service:**
```python
from typing import Optional

class LeaveApprovalService:
    """Handle leave request approval workflow."""

    @staticmethod
    def approve_request(request_id: int, approver) -> bool:
        """Approve a leave request and update balance."""
        try:
            leave_request = LeaveRequest.objects.get(id=request_id)
            if leave_request.status != 'PENDING':
                return False

            # Deduct from balance
            balance = LeaveBalance.objects.get(user=leave_request.user)
            balance.hours_used += leave_request.hours_requested
            balance.save()

            # Update request
            leave_request.status = 'APPROVED'
            leave_request.approved_by = approver
            leave_request.save()

            # Log audit
            AuditLog.objects.create(
                user=approver,
                action='APPROVE_LEAVE',
                object_id=request_id,
                details=f"Approved {leave_request.hours_requested} hours"
            )

            return True
        except Exception as e:
            # Log error
            return False
```

**Service Standards:**
- Static methods for stateless operations
- Explicit type hints (Python 3.9+)
- Document with docstrings
- Return simple types (bool, dict, or model instances)
- Handle exceptions, don't let them bubble up
- Log important business events
- Test independently from views

---

### Utility Functions

**Pattern:**
```python
from datetime import date, timedelta
from typing import List

def get_working_hours(start_date: date, end_date: date,
                     exclude_holidays: List[date] = None) -> float:
    """Calculate working hours between dates, excluding weekends and holidays."""
    if exclude_holidays is None:
        exclude_holidays = []

    working_days = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5 and current not in exclude_holidays:
            working_days += 1
        current += timedelta(days=1)

    return working_days * 8.0
```

**Utility Standards:**
- Pure functions (no side effects)
- Type hints for all parameters and returns
- Docstrings with parameter descriptions
- Reusable across views/services
- Tested independently

---

### Permissions & Authentication

**Custom Permission Pattern:**
```python
from rest_framework.permissions import BasePermission

class IsManagerOrAdmin(BasePermission):
    """Allow access only to managers and admins."""

    def has_permission(self, request, view):
        return request.user and request.user.role in ['MANAGER', 'ADMIN']

class IsHROrAdmin(BasePermission):
    """Allow access only to HR and admin users."""

    def has_permission(self, request, view):
        return request.user and request.user.role in ['HR', 'ADMIN']

class IsOwnerOrManager(BasePermission):
    """Allow user to access own data or manager's team data."""

    def has_object_permission(self, request, view, obj):
        # User can view own data
        if obj.user == request.user:
            return True
        # Manager can view team data
        if request.user.role == 'MANAGER':
            return obj.user.department == request.user.department
        return False
```

---

### Error Handling

**Pattern:**
```python
from rest_framework.exceptions import ValidationError, NotFound

def get_leave_balance(user_id: int):
    """Get user's leave balance with proper error handling."""
    try:
        return LeaveBalance.objects.get(user_id=user_id)
    except LeaveBalance.DoesNotExist:
        raise NotFound(f"No leave balance found for user {user_id}")

def process_leave_request(request_data: dict):
    """Validate and process leave request."""
    if not request_data.get('hours_requested'):
        raise ValidationError({'hours_requested': 'This field is required.'})

    if request_data['hours_requested'] < 0.5:
        raise ValidationError({'hours_requested': 'Minimum 0.5 hours required.'})
```

---

## TypeScript & React Standards

### File Naming

- **Component files:** `PascalCase.tsx`
  - `LeaveRequestForm.tsx`, `LeaveBalance.tsx`, `Layout.tsx`

- **Hook files:** `usePascalCase.ts`
  - `useAuth.ts`, `useLeaveBalance.ts`, `useNotifications.ts`

- **Utility files:** `camelCase.ts`
  - `api.ts`, `dateUtils.ts`, `validators.ts`

- **Type definitions:** `index.ts` in `types/`
  - `types/index.ts` for all interfaces

### Code Style

**TypeScript Configuration:**
```json
{
  "compilerOptions": {
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "target": "ES2020",
    "module": "ESNext"
  }
}
```

**Naming Conventions:**

| Item | Convention | Example |
|------|-----------|---------|
| Components | PascalCase | `LeaveRequestForm`, `NotificationCenter` |
| Functions | camelCase | `validateEmail()`, `getUserBalance()` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_PAGE_SIZE = 20` |
| Interfaces | PascalCase + I prefix (optional) | `ILeaveRequest` or `LeaveRequest` |
| Enums | PascalCase | `LeaveStatus`, `UserRole` |
| Private | `_leading_underscore` (rare) | Not common in React |

---

### Type Definitions

**Pattern:**
```typescript
// types/index.ts

export interface User {
  id: number;
  email: string;
  fullName: string;
  role: UserRole;
  department: number;
  createdAt: string;
}

export enum UserRole {
  EMPLOYEE = 'EMPLOYEE',
  MANAGER = 'MANAGER',
  HR = 'HR',
  ADMIN = 'ADMIN',
}

export interface LeaveRequest {
  id: number;
  userId: number;
  categoryId: number;
  startDate: string; // ISO 8601
  endDate: string;
  hoursRequested: number;
  status: LeaveStatus;
  notes: string;
  createdAt: string;
}

export enum LeaveStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  CANCELLED = 'CANCELLED',
}

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

---

### React Component Standards

**Function Component Pattern:**
```typescript
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/Button';
import { LeaveRequestForm } from '@/components/LeaveRequestForm';
import type { LeaveRequest } from '@/types';

interface LeaveRequestPageProps {
  onSuccess?: (request: LeaveRequest) => void;
}

export const LeaveRequestPage: React.FC<LeaveRequestPageProps> = ({ onSuccess }) => {
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (formData: LeaveRequest) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await api.leaves.createRequest(formData);
      onSuccess?.(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit request');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Request Leave</h1>
      {error && <div className="text-red-600 mb-4">{error}</div>}
      <LeaveRequestForm onSubmit={handleSubmit} isLoading={isSubmitting} />
    </div>
  );
};
```

**Component Standards:**
- Always export named component
- Define props interface separately
- Use React.FC for typed components
- Include JSDoc comments for complex logic
- Keep state minimal, lift up if shared
- Use hooks for side effects
- Error boundaries for error handling (future)

---

### Custom Hooks

**Pattern:**
```typescript
import { useState, useEffect } from 'react';
import type { LeaveBalance } from '@/types';

interface UseLeaveBalanceResult {
  balance: LeaveBalance | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useLeaveBalance = (): UseLeaveBalanceResult => {
  const [balance, setBalance] = useState<LeaveBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBalance = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.leaves.getMyBalance();
      setBalance(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch balance');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalance();
  }, []);

  return { balance, loading, error, refetch: fetchBalance };
};
```

---

### API Client Pattern

**Pattern:**
```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ApiResponse, PaginatedResponse, LeaveRequest } from '@/types';

class LeaveAPI {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({ baseURL });

    // JWT interceptor
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Auto-refresh on 401
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Attempt token refresh
          const refreshed = await this.refreshToken();
          if (refreshed) return this.client(error.config);
        }
        return Promise.reject(error);
      }
    );
  }

  async getMyBalance(): Promise<ApiResponse<any>> {
    return this.client.get('/leaves/balance/my/').then(r => r.data);
  }

  async createRequest(data: Partial<LeaveRequest>): Promise<LeaveRequest> {
    return this.client.post('/leaves/requests/', data).then(r => r.data);
  }

  private async refreshToken(): Promise<boolean> {
    // Implementation
    return true;
  }
}

export const api = new LeaveAPI(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1');
```

---

### Styling with Tailwind CSS

**Naming & Organization:**
```typescript
// Utility-first approach
const buttonClasses = "px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors";

// Component wrapper for consistent styling
interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className }) => (
  <div className={`bg-white rounded-lg shadow p-6 ${className || ''}`}>
    {children}
  </div>
);

// Conditional classes with clsx pattern
import clsx from 'clsx';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ variant = 'primary', size = 'md', disabled }) => {
  const baseClasses = "font-semibold rounded transition-colors";
  const variantClasses = {
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300",
  };
  const sizeClasses = {
    sm: "px-3 py-1 text-sm",
    md: "px-4 py-2",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <button
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        disabled && "opacity-50 cursor-not-allowed"
      )}
      disabled={disabled}
    >
      {/* content */}
    </button>
  );
};
```

---

### Error Handling in React

**Pattern:**
```typescript
interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

const initialState: AsyncState<any> = {
  data: null,
  loading: true,
  error: null,
};

export const useFetch = <T,>(
  fetchFn: () => Promise<T>
): AsyncState<T> => {
  const [state, setState] = useState<AsyncState<T>>(initialState);

  useEffect(() => {
    fetchFn()
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => setState({ data: null, loading: false, error }));
  }, []);

  return state;
};

// Usage in component
const MyComponent = () => {
  const { data, loading, error } = useFetch(() => api.getData());

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage message={error.message} />;
  return <div>{/* render data */}</div>;
};
```

---

## Testing Standards

### Backend (Django)

**Test File Naming:** `tests.py` or `test_*.py`

**Pattern:**
```python
from django.test import TestCase
from users.models import User

class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email='test@example.com',
            password='secure123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')

    def test_invalid_email(self):
        with self.assertRaises(ValidationError):
            invalid_user = User(email='invalid-email')
            invalid_user.full_clean()
```

---

### Frontend (React)

**Test File Naming:** `*.test.tsx`

**Pattern:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { LeaveRequestForm } from './LeaveRequestForm';

describe('LeaveRequestForm', () => {
  it('renders form fields', () => {
    render(<LeaveRequestForm onSubmit={jest.fn()} />);
    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
  });

  it('handles form submission', async () => {
    const mockSubmit = jest.fn();
    render(<LeaveRequestForm onSubmit={mockSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(mockSubmit).toHaveBeenCalled();
  });
});
```

---

## Git & Commit Standards

**Commit Message Format:** Conventional Commits

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code structure change
- `docs:` Documentation update
- `test:` Test addition/modification
- `style:` Formatting (no logic change)
- `chore:` Maintenance, dependencies

**Examples:**
```
feat(leaves): add leave request approval workflow

- Implement LeaveApprovalService
- Add approve/reject endpoints
- Update audit logging

feat(frontend): implement leave calendar visualization
fix(auth): resolve JWT refresh token timeout
refactor(utils): extract date calculation logic
docs(api): update endpoint documentation
```

---

## Documentation Standards

**Docstrings (Python):**
```python
def calculate_leave_hours(start_date: date, end_date: date) -> float:
    """Calculate total leave hours between two dates.

    Args:
        start_date: Leave start date (inclusive)
        end_date: Leave end date (inclusive)

    Returns:
        Float representing total working hours

    Raises:
        ValueError: If start_date is after end_date
    """
```

**JSDoc (TypeScript):**
```typescript
/**
 * Fetch user's leave balance
 * @returns Promise resolving to user's leave balance
 * @throws Error if user not authenticated or balance not found
 */
export const getMyBalance = async (): Promise<LeaveBalance> => {
  // implementation
};
```

---

## Code Review Checklist

- [ ] Follows naming conventions
- [ ] Has appropriate docstrings/comments
- [ ] Error handling implemented
- [ ] No hardcoded values (use constants)
- [ ] Performance optimized (no N+1 queries)
- [ ] Security validated (auth, input sanitization)
- [ ] Tests added/updated
- [ ] No console.log or debug code
- [ ] Imports organized correctly
- [ ] Types defined and used

