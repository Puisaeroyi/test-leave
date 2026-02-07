# Frontend Code Standards (React/TypeScript)

**Last Updated:** 2026-02-07

---

## File Naming Conventions

```
PascalCase for React components: Button.tsx, LeaveRequestForm.tsx
kebab-case for utilities and hooks: use-notifications.js, api-client.js
kebab-case for directories: pages/, components/, api/
```

---

## File Organization

**Component structure:**
```
components/
├── Header.tsx               # Component
├── Header.module.css        # Scoped styles (if needed)
└── __tests__/
    └── Header.test.tsx

pages/
├── Dashboard.tsx
├── Calendar.tsx
└── Profile.tsx

api/
├── http.js                  # Axios instance
├── authApi.js              # Auth endpoints
└── leaveApi.js             # Leave endpoints

hooks/
├── use-notifications.js     # Custom hooks
└── use-auth.js
```

---

## Component Style

```typescript
import React, { useState, useEffect } from 'react';
import { Button, Form, Modal } from 'antd';

interface LeaveRequestModalProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (data: LeaveRequestFormData) => Promise<void>;
  userId: string;
}

interface LeaveRequestFormData {
  startDate: string;
  endDate: string;
  hours: number;
  categoryId: string;
  notes?: string;
}

const LeaveRequestModal: React.FC<LeaveRequestModalProps> = ({
  visible,
  onClose,
  onSubmit,
  userId,
}) => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleSubmit = async (values: LeaveRequestFormData) => {
    setLoading(true);
    try {
      await onSubmit(values);
      form.resetFields();
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="New Leave Request"
      open={visible}
      onCancel={onClose}
      footer={null}
    >
      <Form
        form={form}
        onFinish={handleSubmit}
        layout="vertical"
      >
        {/* Form fields */}
      </Form>
    </Modal>
  );
};

export default LeaveRequestModal;
```

---

## API Client Pattern

```typescript
// api/http.ts
import axios, { AxiosInstance } from 'axios';

const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      try {
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL}/auth/refresh/`,
          { refresh: refreshToken }
        );
        localStorage.setItem('access_token', data.access);
        return http(error.config);
      } catch {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default http;
```

---

## State Management (Context API)

```typescript
// auth/authContext.tsx
import React, { createContext, useState, useCallback } from 'react';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'EMPLOYEE' | 'MANAGER' | 'HR' | 'ADMIN';
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const login = useCallback(async (email: string, password: string) => {
    // Implement login logic
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('access_token');
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

---

## TypeScript Types

Define types centrally:

```typescript
// types/index.ts
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  entity?: Entity;
  location?: Location;
  department?: Department;
}

export type UserRole = 'EMPLOYEE' | 'MANAGER' | 'HR' | 'ADMIN';

export interface LeaveRequest {
  id: string;
  user_id: string;
  category: string;
  start_date: string;
  end_date: string;
  hours: number;
  status: LeaveStatus;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export type LeaveStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
```

---

## Custom Hooks

```typescript
// hooks/use-notifications.ts
import { useEffect, useState, useCallback } from 'react';
import { notificationApi } from '../api/notificationApi';

export const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await notificationApi.listNotifications();
      setNotifications(response.data.results);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to fetch notifications', error);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = useCallback(async (id: string) => {
    await notificationApi.markAsRead(id);
    await fetchNotifications();
  }, [fetchNotifications]);

  return { notifications, unreadCount, markAsRead };
};
```

---

## Component Testing

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

  it('renders modal when visible', () => {
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

  it('calls onSubmit with form data', async () => {
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

    await user.type(screen.getByLabelText(/Start Date/i), '2026-02-10');
    await user.click(screen.getByRole('button', { name: /Submit/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});
```

---

## Performance Best Practices

```typescript
// Lazy load page components
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Calendar = React.lazy(() => import('./pages/Calendar'));

// Memoize expensive computations
const MemoizedComponent = React.memo(({ data }) => {
  return <div>{data}</div>;
});

// Debounce API calls in search
import { useMemo } from 'react';

const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = React.useState(value);

  React.useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

// Optimize list rendering with keys
const LeaveList = ({ leaves }) => (
  <div>
    {leaves.map((leave) => (
      <LeaveItem key={leave.id} leave={leave} />
    ))}
  </div>
);
```

---

## Code Organization

**Keep components focused:**
```typescript
// Good: Single responsibility
const LeaveRequestForm = ({ onSubmit }) => {
  // Form logic only
};

const LeaveRequestModal = ({ visible, onClose, onSubmit }) => {
  // Modal wrapper
  return (
    <Modal visible={visible} onCancel={onClose}>
      <LeaveRequestForm onSubmit={onSubmit} />
    </Modal>
  );
};

// Avoid: Too many responsibilities
const LeaveRequestModal = ({ visible, onClose, onSubmit }) => {
  // 200+ lines mixing form, modal, API calls, state management
};
```

---

## Styling Convention

Use Ant Design components primarily, CSS modules for custom styles:

```typescript
import styles from './Header.module.css';
import { Button, Layout } from 'antd';

export const Header = () => (
  <Layout.Header className={styles.header}>
    <div className={styles.logo}>Leave System</div>
    <Button type="primary">Login</Button>
  </Layout.Header>
);
```

**CSS Module (Header.module.css):**
```css
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 1.5rem;
  font-weight: bold;
}
```

---

## Environment Variables

Frontend uses `VITE_` prefix:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Leave Management System
VITE_NOTIFICATION_POLL_INTERVAL=30000
```

Access in code:
```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

---

*See [testing-guidelines.md](./testing-guidelines.md) for detailed testing patterns.*
